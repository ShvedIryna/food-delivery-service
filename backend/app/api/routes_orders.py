from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.domain.order_state import STATUS_TITLES, state_for
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
