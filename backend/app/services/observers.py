from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.events import OrderEvent, OrderEventType, OrderObserver
from app.domain.loyalty import LoyaltyCardFactory
from app.domain.order_state import STATUS_TITLES, OrderStatus
from app.models import Notification, Order

STATUS_MESSAGES = {
    OrderStatus.PREPARING.value: ("Замовлення готується", "Заклад «{r}» почав готувати ваше замовлення №{id}."),
    OrderStatus.DELIVERING.value: ("Кур'єр у дорозі", "Замовлення №{id} передано кур'єру. Відстежуйте його на карті."),
    OrderStatus.READY_FOR_PICKUP.value: ("Замовлення готове", "Замовлення №{id} чекає на вас у закладі «{r}»."),
    OrderStatus.DELIVERED.value: ("Замовлення доставлено", "Смачного! Замовлення №{id} отримано."),
    OrderStatus.CANCELLED.value: ("Замовлення скасовано", "Замовлення №{id} скасовано."),
}


# Observer: конкретні спостерігачі
class NotificationObserver(OrderObserver):

    def __init__(self, db: Session):
        self.db = db

    def update(self, event: OrderEvent) -> None:
        order: Order = event.order
        r_name = order.restaurant.name if order.restaurant else ""
        if event.type == OrderEventType.CREATED:
            title = "Замовлення прийняте"
            message = f"Замовлення №{order.id} на суму {order.total} ₴ прийняте. Очікуйте ~{order.estimated_minutes} хв."
        else:
            title, template = STATUS_MESSAGES.get(
                event.new_status, (STATUS_TITLES.get(event.new_status, "Статус змінено"), "Замовлення №{id}.")
            )
            message = template.format(id=order.id, r=r_name)
        self.db.add(Notification(user_id=order.user_id, order_id=order.id, kind="ORDER_STATUS", title=title, message=message))


class LoyaltyObserver(OrderObserver):

    def __init__(self, db: Session):
        self.db = db

    def update(self, event: OrderEvent) -> None:
        if event.type != OrderEventType.STATUS_CHANGED:
            return
        order: Order = event.order
        user = order.user
        if event.new_status == OrderStatus.DELIVERED.value:
            card = LoyaltyCardFactory.create(user.card_type)
            points = card.calculate_bonus(Decimal(order.total))
            if points > 0:
                order.bonus_earned = points
                user.bonus_points += points
                self.db.add(
                    Notification(
                        user_id=user.id,
                        order_id=order.id,
                        kind="BONUS",
                        title=f"+{points} бонусних балів",
                        message=f"За замовлення №{order.id} нараховано {points} балів ({card.title}).",
                    )
                )
        elif event.new_status == OrderStatus.CANCELLED.value and order.bonus_used:
            user.bonus_points += order.bonus_used
            self.db.add(
                Notification(
                    user_id=user.id,
                    order_id=order.id,
                    kind="BONUS",
                    title="Бонуси повернено",
                    message=f"Повернено {order.bonus_used} балів за скасоване замовлення №{order.id}.",
                )
            )


class PaymentObserver(OrderObserver):

    def update(self, event: OrderEvent) -> None:
        if event.type != OrderEventType.STATUS_CHANGED:
            return
        order: Order = event.order
        if event.new_status == OrderStatus.DELIVERED.value and order.payment_method == "CASH":
            order.payment_status = "PAID"
        elif event.new_status == OrderStatus.CANCELLED.value and order.payment_status == "PAID":
            order.payment_status = "REFUNDED"
