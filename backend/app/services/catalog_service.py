from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Order, Restaurant, Review, User

CUISINES: dict[str, str] = {
    "UKRAINIAN": "Українська",
    "ITALIAN": "Італійська",
    "JAPANESE": "Японська",
    "AMERICAN": "Американська",
    "GEORGIAN": "Грузинська",
    "ASIAN": "Азійська",
    "DESSERTS": "Десерти та кава",
}


class CatalogService:
    def __init__(self, db: Session):
        self.db = db

    def list_restaurants(
        self,
        cuisine: str | None = None,
        price_level: int | None = None,
        max_delivery_time: int | None = None,
        q: str | None = None,
        sort: str = "rating",
        only_ids: set[int] | None = None,
        include_inactive: bool = False,
    ) -> list[Restaurant]:
        stmt = select(Restaurant)
        if not include_inactive:
            stmt = stmt.where(Restaurant.is_active.is_(True))
        if cuisine:
            stmt = stmt.where(Restaurant.cuisine == cuisine)
        if price_level:
            stmt = stmt.where(Restaurant.price_level <= price_level)
        if max_delivery_time:
            stmt = stmt.where(Restaurant.delivery_time_min <= max_delivery_time)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(Restaurant.name.ilike(like) | Restaurant.description.ilike(like))
        if only_ids is not None:
            if not only_ids:
                return []
            stmt = stmt.where(Restaurant.id.in_(only_ids))
        order = {
            "rating": (Restaurant.rating.desc(), Restaurant.id),
            "delivery_time": (Restaurant.delivery_time_min.asc(), Restaurant.id),
            "price": (Restaurant.price_level.asc(), Restaurant.rating.desc()),
            "name": (Restaurant.name.asc(),),
        }.get(sort, (Restaurant.rating.desc(), Restaurant.id))
        return list(self.db.scalars(stmt.order_by(*order)))

    def get_restaurant(self, restaurant_id: int) -> Restaurant | None:
        return self.db.scalar(
            select(Restaurant).options(selectinload(Restaurant.dishes)).where(Restaurant.id == restaurant_id)
        )

    def list_reviews(self, restaurant_id: int) -> list[Review]:
        stmt = select(Review).where(Review.restaurant_id == restaurant_id).order_by(Review.created_at.desc())
        return list(self.db.scalars(stmt))

    def user_has_delivered_order(self, user: User, restaurant_id: int) -> bool:
        return bool(
            self.db.scalar(
                select(
                    exists().where(
                        Order.user_id == user.id,
                        Order.restaurant_id == restaurant_id,
                        Order.status == "DELIVERED",
                    )
                )
            )
        )

    def add_or_update_review(self, user: User, restaurant: Restaurant, rating: int, text: str) -> Review:
        review = self.db.scalar(
            select(Review).where(Review.user_id == user.id, Review.restaurant_id == restaurant.id)
        )
        if review is None:
            review = Review(user_id=user.id, restaurant_id=restaurant.id, rating=rating, text=text)
            self.db.add(review)
        else:
            review.rating, review.text = rating, text
        self.db.flush()
        self.recalculate_rating(restaurant)
        return review

    def recalculate_rating(self, restaurant: Restaurant) -> None:
        avg, count = self.db.execute(
            select(func.avg(Review.rating), func.count(Review.id)).where(Review.restaurant_id == restaurant.id)
        ).one()
        restaurant.rating = round(float(avg or 0), 2)
        restaurant.reviews_count = int(count or 0)
