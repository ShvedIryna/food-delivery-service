from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.delivery import DeliveryStrategy
from app.domain.money import money
from app.domain.payment import PaymentStrategy


class OrderValidationError(ValueError):
    pass


@dataclass
class OrderLine:
    dish_id: int
    name: str
    unit_price: Decimal
    quantity: int

    @property
    def total(self) -> Decimal:
        return money(self.unit_price * self.quantity)


@dataclass
class OrderDraft:
    restaurant_id: int
    lines: list[OrderLine]
    delivery: DeliveryStrategy
    payment: PaymentStrategy
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    comment: str | None = None
    bonus_to_use: int = 0
    payment_details: dict = field(default_factory=dict)

    @property
    def subtotal(self) -> Decimal:
        return money(sum((line.total for line in self.lines), Decimal("0")))


# Builder
class OrderBuilder:
    MAX_QUANTITY = 50

    def __init__(self, restaurant_id: int, min_order: Decimal = Decimal("0")):
        self._restaurant_id = restaurant_id
        self._min_order = min_order
        self._lines: dict[int, OrderLine] = {}
        self._delivery: DeliveryStrategy | None = None
        self._payment: PaymentStrategy | None = None
        self._address: str | None = None
        self._lat: float | None = None
        self._lng: float | None = None
        self._comment: str | None = None
        self._bonus = 0
        self._payment_details: dict = {}

    def add_item(self, dish_id: int, name: str, unit_price: Decimal, quantity: int = 1) -> "OrderBuilder":
        if quantity < 1 or quantity > self.MAX_QUANTITY:
            raise OrderValidationError(f"Некоректна кількість для «{name}»")
        if dish_id in self._lines:
            self._lines[dish_id].quantity += quantity
        else:
            self._lines[dish_id] = OrderLine(dish_id, name, money(unit_price), quantity)
        return self

    def with_delivery(self, strategy: DeliveryStrategy) -> "OrderBuilder":
        self._delivery = strategy
        return self

    def with_payment(self, strategy: PaymentStrategy, details: dict | None = None) -> "OrderBuilder":
        self._payment = strategy
        self._payment_details = details or {}
        return self

    def deliver_to(self, address: str | None, lat: float | None = None, lng: float | None = None) -> "OrderBuilder":
        self._address = address.strip() if address else None
        self._lat, self._lng = lat, lng
        return self

    def with_comment(self, comment: str | None) -> "OrderBuilder":
        self._comment = comment.strip() if comment else None
        return self

    def use_bonus(self, points: int) -> "OrderBuilder":
        self._bonus = max(0, int(points or 0))
        return self

    def build(self) -> OrderDraft:
        if not self._lines:
            raise OrderValidationError("Кошик порожній")
        if self._delivery is None:
            raise OrderValidationError("Не обрано спосіб доставки")
        if self._payment is None:
            raise OrderValidationError("Не обрано спосіб оплати")
        if self._delivery.requires_address:
            if not self._address:
                raise OrderValidationError("Вкажіть адресу доставки")
            if self._lat is None or self._lng is None:
                raise OrderValidationError("Позначте точку доставки на карті")
        draft = OrderDraft(
            restaurant_id=self._restaurant_id,
            lines=list(self._lines.values()),
            delivery=self._delivery,
            payment=self._payment,
            address=self._address if self._delivery.requires_address else None,
            lat=self._lat if self._delivery.requires_address else None,
            lng=self._lng if self._delivery.requires_address else None,
            comment=self._comment,
            bonus_to_use=self._bonus,
            payment_details=self._payment_details,
        )
        if draft.subtotal < self._min_order:
            raise OrderValidationError(f"Мінімальна сума замовлення у цьому закладі — {self._min_order} ₴")
        return draft
