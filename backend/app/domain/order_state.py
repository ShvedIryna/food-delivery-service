from abc import ABC
from enum import Enum


class OrderStatus(str, Enum):
    NEW = "NEW"
    PREPARING = "PREPARING"
    DELIVERING = "DELIVERING"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class InvalidTransition(Exception):
    pass


# State
class OrderState(ABC):
    status: OrderStatus
    title: str
    is_final: bool = False
    client_can_cancel: bool = False
    admin_can_cancel: bool = False

    def next(self, ctx: "OrderContext") -> "OrderState":
        raise InvalidTransition(f"Замовлення у стані «{self.title}» не можна просунути далі")

    def cancel(self, ctx: "OrderContext", by_admin: bool = False) -> "OrderState":
        allowed = self.admin_can_cancel if by_admin else self.client_can_cancel
        if not allowed:
            raise InvalidTransition(f"Замовлення у стані «{self.title}» не можна скасувати")
        return CancelledState()


class NewState(OrderState):
    status = OrderStatus.NEW
    title = "Прийняте"
    client_can_cancel = True
    admin_can_cancel = True

    def next(self, ctx):
        return PreparingState()


class PreparingState(OrderState):
    status = OrderStatus.PREPARING
    title = "Готується"
    admin_can_cancel = True

    def next(self, ctx):
        return ReadyForPickupState() if ctx.is_pickup else DeliveringState()


class DeliveringState(OrderState):
    status = OrderStatus.DELIVERING
    title = "Доставляється"

    def next(self, ctx):
        return DeliveredState()


class ReadyForPickupState(OrderState):
    status = OrderStatus.READY_FOR_PICKUP
    title = "Готове до видачі"

    def next(self, ctx):
        return DeliveredState()


class DeliveredState(OrderState):
    status = OrderStatus.DELIVERED
    title = "Доставлено"
    is_final = True


class CancelledState(OrderState):
    status = OrderStatus.CANCELLED
    title = "Скасовано"
    is_final = True


_STATES: dict[str, type[OrderState]] = {
    cls.status.value: cls
    for cls in (NewState, PreparingState, DeliveringState, ReadyForPickupState, DeliveredState, CancelledState)
}

STATUS_TITLES: dict[str, str] = {code: cls.title for code, cls in _STATES.items()}


def state_for(status: str) -> OrderState:
    return _STATES[status]()


class OrderContext:

    def __init__(self, status: str, is_pickup: bool):
        self._state = state_for(status)
        self.is_pickup = is_pickup

    @property
    def state(self) -> OrderState:
        return self._state

    @property
    def status(self) -> str:
        return self._state.status.value

    def advance(self) -> str:
        self._state = self._state.next(self)
        return self.status

    def cancel(self, by_admin: bool = False) -> str:
        self._state = self._state.cancel(self, by_admin)
        return self.status
