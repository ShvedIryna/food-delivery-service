from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes_catalog import restaurant_out
from app.db.session import get_db
from app.domain.loyalty import PREMIUM_PRICE, LoyaltyCardFactory, RegularCustomerPolicy
from app.models import Notification, Restaurant, User
from app.schemas import NotificationOut, ProfileUpdate, RestaurantOut, UserOut
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/me", tags=["Особистий кабінет"])


@router.get("", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("", response_model=UserOut)
def update_me(data: ProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(user)
    return user


@router.get("/loyalty")
def loyalty(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = LoyaltyCardFactory.create(user.card_type)
    delivered = OrderService(db).delivered_orders_count(user)
    return {
        "card": card.to_dict(),
        "bonus_points": user.bonus_points,
        "delivered_orders": delivered,
        "regular_discount_percent": float(RegularCustomerPolicy.discount_rate(delivered) * 100),
        "next_level": RegularCustomerPolicy.next_level(delivered),
        "premium_price": float(PREMIUM_PRICE),
        "premium_offer": LoyaltyCardFactory.create("PREMIUM").to_dict(),
    }


@router.post("/loyalty/premium", response_model=UserOut)
def buy_premium(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.card_type == "PREMIUM":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "У вас вже преміум-картка")
    user.card_type = "PREMIUM"
    db.add(
        Notification(
            user_id=user.id,
            kind="PROMO",
            title="Вітаємо з преміум-карткою!",
            message="Тепер доставка безкоштовна, а бонуси нараховуються у розмірі 7%.",
        )
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("/favorites", response_model=list[RestaurantOut])
def favorites(user: User = Depends(get_current_user)):
    ids = {r.id for r in user.favorites}
    return [restaurant_out(r, ids) for r in user.favorites]


@router.post("/favorites/{restaurant_id}", status_code=204)
def add_favorite(restaurant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    restaurant = db.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заклад не знайдено")
    if restaurant not in user.favorites:
        user.favorites.append(restaurant)
        db.commit()


@router.delete("/favorites/{restaurant_id}", status_code=204)
def remove_favorite(restaurant_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    user.favorites = [r for r in user.favorites if r.id != restaurant_id]
    db.commit()


@router.get("/notifications", response_model=list[NotificationOut])
def notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = (
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(50)
    )
    return list(db.scalars(stmt))


@router.post("/notifications/read-all", status_code=204)
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(update(Notification).where(Notification.user_id == user.id).values(is_read=True))
    db.commit()
