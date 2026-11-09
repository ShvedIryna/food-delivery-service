from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal

from app.domain.delivery import DeliveryStrategy
from app.domain.loyalty import MAX_BONUS_SHARE, LoyaltyCard, RegularCustomerPolicy
from app.domain.money import money


@dataclass
class PricingContext:
    subtotal: Decimal
    delivery: DeliveryStrategy
    card: LoyaltyCard
    delivered_orders: int = 0
    bonus_to_use: int = 0
    available_bonus: int = 0


@dataclass
class PriceBreakdown:
    subtotal: Decimal
    delivery_fee: Decimal = Decimal("0")
    discount: Decimal = Decimal("0")
    bonus_used: int = 0
    notes: list[str] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        value = self.subtotal - self.discount + self.delivery_fee - Decimal(self.bonus_used)
        return money(max(value, Decimal("0")))

    def to_dict(self) -> dict:
        return {
            "subtotal": float(self.subtotal),
            "delivery_fee": float(self.delivery_fee),
            "discount": float(self.discount),
            "bonus_used": self.bonus_used,
            "total": float(self.total),
            "notes": self.notes,
        }


class PriceCalculator(ABC):
    @abstractmethod
    def calculate(self, ctx: PricingContext) -> PriceBreakdown:
        ...


class BasePriceCalculator(PriceCalculator):
    def calculate(self, ctx: PricingContext) -> PriceBreakdown:
        subtotal = money(ctx.subtotal)
        return PriceBreakdown(subtotal=subtotal, delivery_fee=ctx.delivery.calculate_fee(subtotal))


# Decorator
class PriceCalculatorDecorator(PriceCalculator):
    def __init__(self, wrapped: PriceCalculator):
        self._wrapped = wrapped

    def calculate(self, ctx: PricingContext) -> PriceBreakdown:
        return self._wrapped.calculate(ctx)


class RegularCustomerDiscount(PriceCalculatorDecorator):
    def calculate(self, ctx: PricingContext) -> PriceBreakdown:
        result = super().calculate(ctx)
        rate = RegularCustomerPolicy.discount_rate(ctx.delivered_orders)
        if rate > 0:
            result.discount += money(result.subtotal * rate)
            result.notes.append(f"Знижка постійного клієнта {int(rate * 100)}%")
        return result


class PremiumFreeDelivery(PriceCalculatorDecorator):
    def calculate(self, ctx: PricingContext) -> PriceBreakdown:
        result = super().calculate(ctx)
        if ctx.card.free_delivery and result.delivery_fee > 0:
            result.delivery_fee = money(0)
            result.notes.append("Безкоштовна доставка за преміум-карткою")
        return result


class BonusRedemption(PriceCalculatorDecorator):
    def calculate(self, ctx: PricingContext) -> PriceBreakdown:
        result = super().calculate(ctx)
        if ctx.bonus_to_use <= 0:
            return result
        limit = int(((result.subtotal - result.discount) * MAX_BONUS_SHARE).to_integral_value(rounding=ROUND_DOWN))
        used = max(0, min(ctx.bonus_to_use, ctx.available_bonus, limit))
        if used:
            result.bonus_used = used
            result.notes.append(f"Списано {used} бонусних балів")
        return result


def build_price_calculator() -> PriceCalculator:
    return BonusRedemption(PremiumFreeDelivery(RegularCustomerDiscount(BasePriceCalculator())))
