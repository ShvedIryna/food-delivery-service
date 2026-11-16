from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.timeutil import utcnow
from app.db.session import get_db
from app.domain.order_state import STATUS_TITLES, OrderStatus, state_for
from app.domain.tracking import build_route, haversine_km, position_on_route
from app.models import Order, User
from app.schemas import OrderCreate, OrderItemOut, OrderOut, PriceQuoteOut
from app.services.order_service import OrderError, OrderService

router = APIRouter(prefix="/api", tags=["Замовлення"])


def order_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        restaurant_id=order.restaurant_id,
        restaurant_name=order.restaurant.name if order.restaurant else "",
        status=order.status,
        status_title=STATUS_TITLES.get(order.status, order.status),
        delivery_type=order.delivery_type,
        payment_method=order.payment_method,
        payment_status=order.payment_status,
        transaction_id=order.transaction_id,
        address=order.address,
        lat=order.lat,
        lng=order.lng,
        comment=order.comment,
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        discount=order.discount,
        bonus_used=order.bonus_used,
        bonus_earned=order.bonus_earned,
        total=order.total,
        estimated_minutes=order.estimated_minutes,
        created_at=order.created_at,
        status_changed_at=order.status_changed_at,
        can_cancel=state_for(order.status).client_can_cancel,
        items=[OrderItemOut.model_validate(i) for i in order.items],
    )


def _bad_request(exc: Exception):
    return HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.get("/orders/options")
def order_options():
    return {"delivery": OrderService.delivery_options(), "payment": OrderService.payment_methods()}


@router.post("/orders/quote", response_model=PriceQuoteOut)
def quote(data: OrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return OrderService(db).quote(user, data)
    except OrderError as exc:
        raise _bad_request(exc)


@router.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(data: OrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return order_out(OrderService(db).place_order(user, data))
    except OrderError as exc:
        raise _bad_request(exc)


@router.get("/orders", response_model=list[OrderOut])
def my_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    orders = db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc()))
    return [order_out(o) for o in orders]


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return order_out(OrderService(db).get_user_order(user, order_id))
    except OrderError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = OrderService(db)
    try:
        order = service.get_user_order(user, order_id)
        return order_out(service.cancel(order, by_admin=False))
    except OrderError as exc:
        raise _bad_request(exc)


@router.post("/orders/{order_id}/repeat", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def repeat_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return order_out(OrderService(db).repeat_order(user, order_id))
    except OrderError as exc:
        raise _bad_request(exc)


@router.get("/orders/{order_id}/tracking")
def tracking(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        order = OrderService(db).get_user_order(user, order_id)
    except OrderError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))

    r = order.restaurant
    start = (r.lat, r.lng)
    result = {
        "order_id": order.id,
        "status": order.status,
        "status_title": STATUS_TITLES.get(order.status, order.status),
        "restaurant": {"name": r.name, "lat": r.lat, "lng": r.lng},
        "destination": None,
        "route": [],
        "courier": None,
        "progress": 0.0,
        "eta_minutes": None,
        "distance_km": None,
    }
    if order.delivery_type == "PICKUP" or order.lat is None:
        return result

    end = (order.lat, order.lng)
    route = build_route(start, end)
    result["destination"] = {"address": order.address, "lat": order.lat, "lng": order.lng}
    result["route"] = [list(p) for p in route]
    result["distance_km"] = round(sum(haversine_km(route[i], route[i + 1]) for i in range(len(route) - 1)), 2)

    duration = get_settings().sim_delivery_seconds
    if order.status == OrderStatus.DELIVERING.value:
        elapsed = (utcnow() - order.status_changed_at).total_seconds()
        progress = min(elapsed / duration, 1.0)
        lat, lng = position_on_route(route, progress)
        result.update(
            courier={"lat": lat, "lng": lng},
            progress=round(progress, 3),
            eta_minutes=max(1, round((1 - progress) * order.estimated_minutes * 0.5)),
        )
    elif order.status == OrderStatus.DELIVERED.value:
        result.update(courier={"lat": end[0], "lng": end[1]}, progress=1.0, eta_minutes=0)
    elif order.status in (OrderStatus.NEW.value, OrderStatus.PREPARING.value):
        result.update(courier={"lat": start[0], "lng": start[1]}, eta_minutes=order.estimated_minutes)
    return result
