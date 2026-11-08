from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user
from app.db.session import get_db
from app.models import Restaurant, User
from app.schemas import DishOut, RestaurantDetailOut, RestaurantOut, ReviewIn, ReviewOut
from app.services.catalog_service import CUISINES, CatalogService

router = APIRouter(prefix="/api", tags=["Каталог"])


def restaurant_out(r: Restaurant, favorite_ids: set[int]) -> RestaurantOut:
    out = RestaurantOut.model_validate(r)
    out.is_favorite = r.id in favorite_ids
    return out


def review_out(review) -> ReviewOut:
    return ReviewOut(
        id=review.id,
        restaurant_id=review.restaurant_id,
        rating=review.rating,
        text=review.text,
        created_at=review.created_at,
        author=review.user.full_name if review.user else "Користувач",
    )


@router.get("/cuisines")
def list_cuisines():
    return [{"code": code, "title": title} for code, title in CUISINES.items()]


@router.get("/restaurants", response_model=list[RestaurantOut])
def list_restaurants(
    cuisine: str | None = None,
    price_level: int | None = Query(default=None, ge=1, le=3),
    max_delivery_time: int | None = Query(default=None, ge=5),
    q: str | None = None,
    sort: str = "rating",
    favorites_only: bool = False,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    favorite_ids = {r.id for r in user.favorites} if user else set()
    restaurants = CatalogService(db).list_restaurants(
        cuisine=cuisine,
        price_level=price_level,
        max_delivery_time=max_delivery_time,
        q=q,
        sort=sort,
        only_ids=favorite_ids if favorites_only else None,
    )
    return [restaurant_out(r, favorite_ids) for r in restaurants]


@router.get("/restaurants/{restaurant_id}", response_model=RestaurantDetailOut)
def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    restaurant = CatalogService(db).get_restaurant(restaurant_id)
    if restaurant is None or not restaurant.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заклад не знайдено")
    favorite_ids = {r.id for r in user.favorites} if user else set()
    base = restaurant_out(restaurant, favorite_ids)
    dishes = [DishOut.model_validate(d) for d in restaurant.dishes if d.is_available]
    return RestaurantDetailOut(**base.model_dump(), dishes=dishes)


@router.get("/restaurants/{restaurant_id}/reviews", response_model=list[ReviewOut])
def list_reviews(restaurant_id: int, db: Session = Depends(get_db)):
    return [review_out(r) for r in CatalogService(db).list_reviews(restaurant_id)]


@router.post("/restaurants/{restaurant_id}/reviews", response_model=ReviewOut, status_code=201)
def add_review(
    restaurant_id: int,
    data: ReviewIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = CatalogService(db)
    restaurant = service.get_restaurant(restaurant_id)
    if restaurant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заклад не знайдено")
    if not service.user_has_delivered_order(user, restaurant_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Відгук можна залишити після отримання замовлення з цього закладу")
    review = service.add_or_update_review(user, restaurant, data.rating, data.text.strip())
    db.commit()
    db.refresh(review)
    return review_out(review)
