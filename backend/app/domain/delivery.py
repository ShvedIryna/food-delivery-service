from abc import ABC, abstractmethod
from decimal import Decimal

from app.domain.money import money


# Strategy
class DeliveryStrategy(ABC):
    code: str
    title: str
    description: str
    requires_address: bool = True

    @abstractmethod
    def calculate_fee(self, subtotal: Decimal) -> Decimal:
        ...

    @abstractmethod
    def estimate_minutes(self, base_minutes: int) -> int:
        ...

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "requires_address": self.requires_address,
        }


class StandardDelivery(DeliveryStrategy):
    code = "STANDARD"
    title = "Стандартна"
    description = "49 ₴, безкоштовно від 500 ₴"
    BASE_FEE = Decimal("49")
    FREE_FROM = Decimal("500")

    def calculate_fee(self, subtotal: Decimal) -> Decimal:
        return money(0) if subtotal >= self.FREE_FROM else money(self.BASE_FEE)

    def estimate_minutes(self, base_minutes: int) -> int:
        return base_minutes


class ExpressDelivery(DeliveryStrategy):
    code = "EXPRESS"
    title = "Експрес"
    description = "99 ₴, приблизно на 40% швидше"
    FEE = Decimal("99")

    def calculate_fee(self, subtotal: Decimal) -> Decimal:
        return money(self.FEE)

    def estimate_minutes(self, base_minutes: int) -> int:
        return max(15, round(base_minutes * 0.6))


class PickupDelivery(DeliveryStrategy):
    code = "PICKUP"
    title = "Самовивіз"
    description = "Безкоштовно, заберіть замовлення у закладі"
    requires_address = False

    def calculate_fee(self, subtotal: Decimal) -> Decimal:
        return money(0)

    def estimate_minutes(self, base_minutes: int) -> int:
        return 15  # лише час приготування


DELIVERY_STRATEGIES: dict[str, DeliveryStrategy] = {
    s.code: s for s in (StandardDelivery(), ExpressDelivery(), PickupDelivery())
}


def get_delivery_strategy(code: str) -> DeliveryStrategy:
    try:
        return DELIVERY_STRATEGIES[code]
    except KeyError:
        raise ValueError(f"Невідомий спосіб доставки: {code}") from None
