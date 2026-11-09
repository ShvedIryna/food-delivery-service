from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class OrderEventType(str, Enum):
    CREATED = "CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"


@dataclass
class OrderEvent:
    type: OrderEventType
    order: Any  # ORM-об'єкт Order (домен не залежить від SQLAlchemy)
    old_status: str | None = None
    new_status: str | None = None


class OrderObserver(ABC):
    @abstractmethod
    def update(self, event: OrderEvent) -> None:
        ...


# Observer
class OrderEventPublisher:
    def __init__(self) -> None:
        self._observers: list[OrderObserver] = []

    def subscribe(self, observer: OrderObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: OrderObserver) -> None:
        self._observers.remove(observer)

    def notify(self, event: OrderEvent) -> None:
        for observer in list(self._observers):
            observer.update(event)
