import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PaymentResult:
    success: bool
    status: str  # PAID | PENDING | FAILED
    transaction_id: str | None = None
    message: str = ""


def luhn_valid(card_number: str) -> bool:
    digits = [int(c) for c in card_number if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


# Strategy
class PaymentStrategy(ABC):
    code: str
    title: str

    @abstractmethod
    def pay(self, amount: Decimal, details: dict | None = None) -> PaymentResult:
        ...

    def to_dict(self) -> dict:
        return {"code": self.code, "title": self.title}


class OnlineCardPayment(PaymentStrategy):
    code = "CARD"
    title = "Онлайн карткою"

    def pay(self, amount: Decimal, details: dict | None = None) -> PaymentResult:
        card_number = (details or {}).get("card_number")
        # Якщо номер не передано — використовується збережена картка (повторне замовлення)
        if card_number and not luhn_valid(card_number):
            return PaymentResult(False, "FAILED", message="Некоректний номер картки")
        txn = "TXN-" + uuid.uuid4().hex[:12].upper()
        return PaymentResult(True, "PAID", txn, f"Оплачено {amount} ₴")


class CashPayment(PaymentStrategy):
    code = "CASH"
    title = "Готівкою при отриманні"

    def pay(self, amount: Decimal, details: dict | None = None) -> PaymentResult:
        return PaymentResult(True, "PENDING", None, "Оплата при отриманні")


PAYMENT_STRATEGIES: dict[str, PaymentStrategy] = {
    s.code: s for s in (OnlineCardPayment(), CashPayment())
}


def get_payment_strategy(code: str) -> PaymentStrategy:
    try:
        return PAYMENT_STRATEGIES[code]
    except KeyError:
        raise ValueError(f"Невідомий спосіб оплати: {code}") from None
