from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.api.routes_orders import order_out
from app.core.timeutil import utcnow
from app.db.session import get_db
from app.domain.loyalty import LoyaltyCardFactory
from app.domain.order_state import STATUS_TITLES, OrderStatus
from app.models import Dish, Order, OrderItem, Restaurant, User
from app.schemas import DishIn, DishOut, OrderOut, RestaurantDetailOut, RestaurantIn, RestaurantOut, UserAdminUpdate, UserOut
from app.services.catalog_service import CUISINES, CatalogService
from app.services.order_service import OrderError, OrderService

router = APIRouter(prefix="/api/admin", tags=["Адмін-панель"], dependencies=[Depends(require_admin)])


def _get_or_404(db: Session, model, obj_id: int, msg: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, msg)
    return obj


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    delivered = Order.status == OrderStatus.DELIVERED.value
    revenue = db.scalar(select(func.coalesce(func.sum(Order.total), 0)).where(delivered))
    by_status = dict(db.execute(select(Order.status, func.count(Order.id)).group_by(Order.status)).all())
    top_dishes = db.execute(
        select(OrderItem.dish_name, func.sum(OrderItem.quantity).label("qty"))
        .join(Order)
        .where(Order.status != OrderStatus.CANCELLED.value)
        .group_by(OrderItem.dish_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
    ).all()
    by_restaurant = db.execute(
        select(Restaurant.name, func.count(Order.id), func.coalesce(func.sum(Order.total), 0))
        .join(Order, Order.restaurant_id == Restaurant.id)
        .where(delivered)
        .group_by(Restaurant.name)
        .order_by(func.sum(Order.total).desc())
    ).all()
    since = utcnow() - timedelta(days=7)
    return {
        "orders_total": sum(by_status.values()),
        "orders_last_7_days": db.scalar(select(func.count(Order.id)).where(Order.created_at >= since)),
        "revenue": float(revenue or 0),
        "users": db.scalar(select(func.count(User.id))),
        "premium_users": db.scalar(select(func.count(User.id)).where(User.card_type == "PREMIUM")),
        "restaurants": db.scalar(select(func.count(Restaurant.id))),
        "orders_by_status": [
            {"status": s, "title": STATUS_TITLES.get(s, s), "count": c} for s, c in by_status.items()
        ],
        "top_dishes": [{"name": n, "quantity": int(q)} for n, q in top_dishes],
        "revenue_by_restaurant": [
            {"name": n, "orders": int(c), "revenue": float(r)} for n, c, r in by_restaurant
        ],
    }


@router.get("/restaurants", response_model=list[RestaurantOut])
def list_restaurants(db: Session = Depends(get_db)):
    return CatalogService(db).list_restaurants(sort="name", include_inactive=True)


@router.get("/restaurants/{restaurant_id}", response_model=RestaurantDetailOut)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    r = CatalogService(db).get_restaurant(restaurant_id)
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заклад не знайдено")
    return r


def _validate_cuisine(code: str):
    if code not in CUISINES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Невідомий тип кухні")


@router.post("/restaurants", response_model=RestaurantOut, status_code=201)
def create_restaurant(data: RestaurantIn, db: Session = Depends(get_db)):
    _validate_cuisine(data.cuisine)
    r = Restaurant(**data.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.put("/restaurants/{restaurant_id}", response_model=RestaurantOut)
def update_restaurant(restaurant_id: int, data: RestaurantIn, db: Session = Depends(get_db)):
    _validate_cuisine(data.cuisine)
    r = _get_or_404(db, Restaurant, restaurant_id, "Заклад не знайдено")
    for k, v in data.model_dump().items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/restaurants/{restaurant_id}", status_code=204)
def delete_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    r = _get_or_404(db, Restaurant, restaurant_id, "Заклад не знайдено")
    has_orders = db.scalar(select(func.count(Order.id)).where(Order.restaurant_id == r.id))
    if has_orders:
        r.is_active = False  # заклад з історією замовлень не видаляємо, а деактивуємо
    else:
        db.delete(r)
    db.commit()


@router.post("/restaurants/{restaurant_id}/dishes", response_model=DishOut, status_code=201)
def create_dish(restaurant_id: int, data: DishIn, db: Session = Depends(get_db)):
    _get_or_404(db, Restaurant, restaurant_id, "Заклад не знайдено")
    dish = Dish(restaurant_id=restaurant_id, **data.model_dump())
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish


@router.put("/dishes/{dish_id}", response_model=DishOut)
def update_dish(dish_id: int, data: DishIn, db: Session = Depends(get_db)):
    dish = _get_or_404(db, Dish, dish_id, "Страву не знайдено")
    for k, v in data.model_dump().items():
        setattr(dish, k, v)
    db.commit()
    db.refresh(dish)
    return dish


@router.delete("/dishes/{dish_id}", status_code=204)
def delete_dish(dish_id: int, db: Session = Depends(get_db)):
    dish = _get_or_404(db, Dish, dish_id, "Страву не знайдено")
    db.delete(dish)
    db.commit()


@router.get("/orders", response_model=list[OrderOut])
def list_orders(status_filter: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Order).order_by(Order.created_at.desc()).limit(200)
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    return [order_out(o) for o in db.scalars(stmt)]


@router.post("/orders/{order_id}/advance", response_model=OrderOut)
def advance_order(order_id: int, db: Session = Depends(get_db)):
    order = _get_or_404(db, Order, order_id, "Замовлення не знайдено")
    try:
        return order_out(OrderService(db).advance(order))
    except OrderError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = _get_or_404(db, Order, order_id, "Замовлення не знайдено")
    try:
        return order_out(OrderService(db).cancel(order, by_admin=True))
    except OrderError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return list(db.scalars(select(User).order_by(User.id)))


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserAdminUpdate, db: Session = Depends(get_db)):
    user = _get_or_404(db, User, user_id, "Користувача не знайдено")
    if data.role is not None:
        if data.role not in ("CLIENT", "ADMIN"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Невідома роль")
        user.role = data.role
    if data.card_type is not None:
        if data.card_type not in LoyaltyCardFactory.available_types():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Невідомий тип картки")
        user.card_type = data.card_type
    if data.bonus_points is not None:
        user.bonus_points = data.bonus_points
    db.commit()
    db.refresh(user)
    return user
