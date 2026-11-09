from abc import ABC
from decimal import ROUND_DOWN, Decimal


class LoyaltyCard(ABC):
    type_code: str
    title: str
    bonus_rate: Decimal  # частка суми, що повертається бонусами
    free_delivery: bool = False
    perks: tuple[str, ...] = ()

    def calculate_bonus(self, paid_amount: Decimal) -> int:
        return int((paid_amount * self.bonus_rate).to_integral_value(rounding=ROUND_DOWN))

    def to_dict(self) -> dict:
        return {
            "type": self.type_code,
            "title": self.title,
            "bonus_percent": float(self.bonus_rate * 100),
            "free_delivery": self.free_delivery,
            "perks": list(self.perks),
        }


class StandardCard(LoyaltyCard):
    type_code = "STANDARD"
    title = "Стандартна картка"
    bonus_rate = Decimal("0.03")
    perks = ("3% бонусами з кожного замовлення",)


class PremiumCard(LoyaltyCard):
    type_code = "PREMIUM"
    title = "Преміум-картка"
    bonus_rate = Decimal("0.07")
    free_delivery = True
    perks = ("7% бонусами з кожного замовлення", "Безкоштовна доставка будь-яким способом")


# Factory Method
class LoyaltyCardFactory:

    _registry: dict[str, type[LoyaltyCard]] = {
        StandardCard.type_code: StandardCard,
        PremiumCard.type_code: PremiumCard,
    }

    @classmethod
    def create(cls, card_type: str) -> LoyaltyCard:
        card_cls = cls._registry.get(card_type, StandardCard)
        return card_cls()

    @classmethod
    def register(cls, card_cls: type[LoyaltyCard]) -> None:
        cls._registry[card_cls.type_code] = card_cls

    @classmethod
    def available_types(cls) -> list[str]:
        return list(cls._registry)


PREMIUM_PRICE = Decimal("199")  # вартість преміум-картки (імітація покупки)
MAX_BONUS_SHARE = Decimal("0.5")  # бонусами можна оплатити до 50% замовлення


class RegularCustomerPolicy:

    LEVELS: tuple[tuple[int, Decimal], ...] = (
        (10, Decimal("0.10")),
        (3, Decimal("0.05")),
    )

    @classmethod
    def discount_rate(cls, delivered_orders: int) -> Decimal:
        for threshold, rate in cls.LEVELS:
            if delivered_orders >= threshold:
                return rate
        return Decimal("0")

    @classmethod
    def next_level(cls, delivered_orders: int) -> dict | None:
        for threshold, rate in sorted(cls.LEVELS):
            if delivered_orders < threshold:
                return {
                    "orders_needed": threshold - delivered_orders,
                    "discount_percent": float(rate * 100),
                }
        return None
