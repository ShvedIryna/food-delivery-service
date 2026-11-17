import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.timeutil import utcnow
from app.db.session import SessionLocal
from app.domain.order_state import OrderStatus
from app.models import Order
from app.services.order_service import OrderError, OrderService

ACTIVE = (
    OrderStatus.NEW.value,
    OrderStatus.PREPARING.value,
    OrderStatus.DELIVERING.value,
    OrderStatus.READY_FOR_PICKUP.value,
)


def simulate_tick() -> int:
    settings = get_settings()
    moved = 0
    db = SessionLocal()
    try:
        service = OrderService(db)
        for order in db.scalars(select(Order).where(Order.status.in_(ACTIVE))).all():
            elapsed = (utcnow() - order.status_changed_at).total_seconds()
            limit = (
                settings.sim_delivery_seconds
                if order.status == OrderStatus.DELIVERING.value
                else settings.sim_step_seconds
            )
            if order.status == OrderStatus.READY_FOR_PICKUP.value:
                limit = settings.sim_step_seconds * 3  # клієнт іде забирати замовлення
            if elapsed >= limit:
                try:
                    service.advance(order)
                    moved += 1
                except OrderError:
                    db.rollback()
    finally:
        db.close()
    return moved


async def run_simulator(interval: float = 5.0) -> None:
    while True:
        try:
            await asyncio.to_thread(simulate_tick)
        except Exception as exc:  # noqa: BLE001 — симуляція не повинна «валити» сервер
            print(f"[simulation] помилка: {exc}")
        await asyncio.sleep(interval)
