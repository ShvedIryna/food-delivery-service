from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.timeutil import utcnow
from app.domain.delivery import DELIVERY_STRATEGIES, get_delivery_strategy
from app.domain.events import OrderEvent, OrderEventPublisher, OrderEventType
from app.domain.loyalty import LoyaltyCardFactory
from app.domain.order_builder import OrderBuilder, OrderDraft, OrderValidationError
from app.domain.order_state import InvalidTransition, OrderContext, OrderStatus
from app.domain.payment import PAYMENT_STRATEGIES, get_payment_strategy
from app.domain.pricing import PriceBreakdown, PricingContext, build_price_calculator
from app.models import Dish, Order, OrderItem, Restaurant, User
from app.schemas import OrderCreate
from app.services.observers import LoyaltyObserver, NotificationObserver, PaymentObserver


class OrderError(Exception):
    ...


# Facade
class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.publisher = OrderEventPublisher()
        self.publisher.subscribe(PaymentObserver())
        self.publisher.subscribe(LoyaltyObserver(db))
        self.publisher.subscribe(NotificationObserver(db))
        self.calculator = build_price_calculator()

    @staticmethod
    def delivery_options() -> list[dict]:
        return [s.to_dict() for s in DELIVERY_STRATEGIES.values()]

    @staticmethod
    def payment_methods() -> list[dict]:
        return [s.to_dict() for s in PAYMENT_STRATEGIES.values()]

    def delivered_orders_count(self, user: User) -> int:
        return self.db.scalar(
            select(func.count(Order.id)).where(Order.user_id == user.id, Order.status == OrderStatus.DELIVERED.value)
        ) or 0

    def _build_draft(self, user: User, data: OrderCreate) -> tuple[Restaurant, OrderDraft]:
        restaurant = self.db.get(Restaurant, data.restaurant_id)
        if restaurant is None or not restaurant.is_active:
            raise OrderError("Заклад недоступний")
        dish_ids = [i.dish_id for i in data.items]
        dishes = {
            d.id: d
            for d in self.db.scalars(
                select(Dish).where(Dish.id.in_(dish_ids), Dish.restaurant_id == restaurant.id)
            )
        }
        try:
            builder = OrderBuilder(restaurant.id, Decimal(restaurant.min_order or 0))
            for item in data.items:
                dish = dishes.get(item.dish_id)
                if dish is None or not dish.is_available:
                    raise OrderError("Одна зі страв недоступна. Оновіть кошик.")
                builder.add_item(dish.id, dish.name, Decimal(dish.price), item.quantity)
            draft = (
                builder.with_delivery(get_delivery_strategy(data.delivery_type))
                .with_payment(get_payment_strategy(data.payment_method), {"card_number": data.card_number})
                .deliver_to(data.address, data.lat, data.lng)
                .with_comment(data.comment)
                .use_bonus(data.use_bonus)
                .build()
            )
        except (OrderValidationError, ValueError) as exc:
            raise OrderError(str(exc)) from exc
        return restaurant, draft

    def _price(self, user: User, draft: OrderDraft) -> PriceBreakdown:
        ctx = PricingContext(
            subtotal=draft.subtotal,
            delivery=draft.delivery,
            card=LoyaltyCardFactory.create(user.card_type),
            delivered_orders=self.delivered_orders_count(user),
            bonus_to_use=draft.bonus_to_use,
            available_bonus=user.bonus_points,
        )
        return self.calculator.calculate(ctx)

    def quote(self, user: User, data: OrderCreate) -> dict:
        restaurant, draft = self._build_draft(user, data)
        price = self._price(user, draft)
        card = LoyaltyCardFactory.create(user.card_type)
        return {
            **price.to_dict(),
            "estimated_minutes": draft.delivery.estimate_minutes(restaurant.delivery_time_min),
            "bonus_to_earn": card.calculate_bonus(price.total),
        }

    def place_order(self, user: User, data: OrderCreate) -> Order:
        restaurant, draft = self._build_draft(user, data)
        price = self._price(user, draft)

        payment = draft.payment.pay(price.total, draft.payment_details)
        if not payment.success:
            raise OrderError(payment.message or "Оплата не пройшла")

        now = utcnow()
        order = Order(
            user_id=user.id,
            restaurant_id=restaurant.id,
            status=OrderStatus.NEW.value,
            delivery_type=draft.delivery.code,
            payment_method=draft.payment.code,
            payment_status=payment.status,
            transaction_id=payment.transaction_id,
            address=draft.address,
            lat=draft.lat,
            lng=draft.lng,
            comment=draft.comment,
            subtotal=price.subtotal,
            delivery_fee=price.delivery_fee,
            discount=price.discount,
            bonus_used=price.bonus_used,
            total=price.total,
            estimated_minutes=draft.delivery.estimate_minutes(restaurant.delivery_time_min),
            created_at=now,
            status_changed_at=now,
            items=[
                OrderItem(dish_id=l.dish_id, dish_name=l.name, unit_price=l.unit_price, quantity=l.quantity)
                for l in draft.lines
            ],
        )
        user.bonus_points -= price.bonus_used
        if draft.address and not user.address:
            user.address = draft.address
        self.db.add(order)
        self.db.flush()
        order.restaurant = restaurant
        self.publisher.notify(OrderEvent(OrderEventType.CREATED, order, None, order.status))
        self.db.commit()
        self.db.refresh(order)
        return order

    def repeat_order(self, user: User, order_id: int) -> Order:
        source = self.get_user_order(user, order_id)
        if not any(i.dish_id for i in source.items):
            raise OrderError("Страви з цього замовлення більше недоступні")
        data = OrderCreate(
            restaurant_id=source.restaurant_id,
            items=[{"dish_id": i.dish_id, "quantity": i.quantity} for i in source.items if i.dish_id],
            delivery_type=source.delivery_type,
            payment_method=source.payment_method,
            address=source.address,
            lat=source.lat,
            lng=source.lng,
            comment=source.comment,
        )
        return self.place_order(user, data)

    def get_user_order(self, user: User, order_id: int) -> Order:
        order = self.db.get(Order, order_id)
        if order is None or (order.user_id != user.id and user.role != "ADMIN"):
            raise OrderError("Замовлення не знайдено")
        return order

    def _change_status(self, order: Order, action) -> Order:
        ctx = OrderContext(order.status, is_pickup=order.delivery_type == "PICKUP")
        old = order.status
        try:
            new = action(ctx)
        except InvalidTransition as exc:
            raise OrderError(str(exc)) from exc
        order.status = new
        order.status_changed_at = utcnow()
        self.publisher.notify(OrderEvent(OrderEventType.STATUS_CHANGED, order, old, new))
        self.db.commit()
        self.db.refresh(order)
        return order

    def advance(self, order: Order) -> Order:
        return self._change_status(order, lambda ctx: ctx.advance())

    def cancel(self, order: Order, by_admin: bool = False) -> Order:
        return self._change_status(order, lambda ctx: ctx.cancel(by_admin))
