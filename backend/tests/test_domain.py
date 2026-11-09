from decimal import Decimal

import pytest

from app.domain.delivery import ExpressDelivery, PickupDelivery, StandardDelivery, get_delivery_strategy
from app.domain.events import OrderEvent, OrderEventPublisher, OrderEventType, OrderObserver
from app.domain.loyalty import LoyaltyCardFactory, PremiumCard, RegularCustomerPolicy, StandardCard
from app.domain.order_builder import OrderBuilder, OrderValidationError
from app.domain.order_state import InvalidTransition, OrderContext
from app.domain.payment import CashPayment, OnlineCardPayment, luhn_valid
from app.domain.pricing import PricingContext, build_price_calculator


def test_standard_delivery_free_from_500():
    s = StandardDelivery()
    assert s.calculate_fee(Decimal("499")) == Decimal("49.00")
    assert s.calculate_fee(Decimal("500")) == Decimal("0.00")


def test_express_is_faster_and_pickup_is_free():
    assert ExpressDelivery().estimate_minutes(50) < 50
    assert PickupDelivery().calculate_fee(Decimal("100")) == 0
    assert PickupDelivery().requires_address is False


def test_unknown_delivery_raises():
    with pytest.raises(ValueError):
        get_delivery_strategy("DRONE")


def test_luhn():
    assert luhn_valid("4242 4242 4242 4242")
    assert not luhn_valid("4242 4242 4242 4241")


def test_payment_strategies():
    assert OnlineCardPayment().pay(Decimal("100"), {"card_number": "4242424242424242"}).status == "PAID"
    assert OnlineCardPayment().pay(Decimal("100"), {"card_number": "1111"}).success is False
    assert CashPayment().pay(Decimal("100")).status == "PENDING"


def test_loyalty_factory():
    assert isinstance(LoyaltyCardFactory.create("PREMIUM"), PremiumCard)
    assert isinstance(LoyaltyCardFactory.create("UNKNOWN"), StandardCard)
    assert LoyaltyCardFactory.create("STANDARD").calculate_bonus(Decimal("1000")) == 30
    assert LoyaltyCardFactory.create("PREMIUM").calculate_bonus(Decimal("1000")) == 70


def test_regular_customer_policy():
    assert RegularCustomerPolicy.discount_rate(0) == 0
    assert RegularCustomerPolicy.discount_rate(3) == Decimal("0.05")
    assert RegularCustomerPolicy.discount_rate(12) == Decimal("0.10")
    assert RegularCustomerPolicy.next_level(1)["orders_needed"] == 2


def _ctx(**kw):
    base = dict(subtotal=Decimal("400"), delivery=StandardDelivery(), card=StandardCard())
    base.update(kw)
    return PricingContext(**base)


def test_price_base():
    p = build_price_calculator().calculate(_ctx())
    assert p.delivery_fee == Decimal("49.00")
    assert p.total == Decimal("449.00")


def test_price_premium_free_delivery_and_regular_discount():
    p = build_price_calculator().calculate(_ctx(card=PremiumCard(), delivered_orders=5))
    assert p.delivery_fee == 0
    assert p.discount == Decimal("20.00")
    assert p.total == Decimal("380.00")
    assert len(p.notes) == 2


def test_bonus_limited_to_half():
    p = build_price_calculator().calculate(_ctx(bonus_to_use=1000, available_bonus=1000))
    assert p.bonus_used == 200
    assert p.total == Decimal("249.00")


def test_state_delivery_flow():
    ctx = OrderContext("NEW", is_pickup=False)
    assert ctx.advance() == "PREPARING"
    assert ctx.advance() == "DELIVERING"
    assert ctx.advance() == "DELIVERED"
    with pytest.raises(InvalidTransition):
        ctx.advance()


def test_state_pickup_flow_and_cancel_rules():
    ctx = OrderContext("PREPARING", is_pickup=True)
    with pytest.raises(InvalidTransition):
        ctx.cancel(by_admin=False)
    assert ctx.advance() == "READY_FOR_PICKUP"
    assert OrderContext("NEW", False).cancel() == "CANCELLED"


def test_observer_notifies_all():
    received = []

    class Spy(OrderObserver):
        def update(self, event):
            received.append(event.new_status)

    pub = OrderEventPublisher()
    pub.subscribe(Spy())
    pub.subscribe(Spy())
    pub.notify(OrderEvent(OrderEventType.STATUS_CHANGED, object(), "NEW", "PREPARING"))
    assert received == ["PREPARING", "PREPARING"]


def test_builder_validation():
    b = OrderBuilder(1).with_delivery(StandardDelivery()).with_payment(CashPayment())
    with pytest.raises(OrderValidationError):
        b.build()  # порожній кошик
    b.add_item(1, "Піца", Decimal("200"), 2).add_item(1, "Піца", Decimal("200"))
    with pytest.raises(OrderValidationError):
        b.build()  # немає адреси
    draft = b.deliver_to("вул. Руська, 1", 49.84, 24.03).build()
    assert draft.subtotal == Decimal("600.00")
    assert draft.lines[0].quantity == 3


def test_builder_min_order_and_pickup():
    b = OrderBuilder(1, Decimal("300")).add_item(1, "Суп", Decimal("100"))
    b.with_delivery(PickupDelivery()).with_payment(CashPayment())
    with pytest.raises(OrderValidationError):
        b.build()
    b.add_item(2, "Рол", Decimal("250"))
    assert b.build().address is None
