from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

# Грошові значення: Decimal з БД → float у JSON
MoneyFloat = Annotated[float, BeforeValidator(lambda v: float(v) if v is not None else v)]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterIn(BaseModel):
    email: str = Field(min_length=5, max_length=120, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6, max_length=100)
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=30)


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(ORM):
    id: int
    email: str
    full_name: str
    phone: str | None
    address: str | None
    role: str
    card_type: str
    bonus_points: int
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)


class DishOut(ORM):
    id: int
    restaurant_id: int
    name: str
    description: str
    category: str
    price: MoneyFloat
    weight_g: int | None
    is_available: bool


class RestaurantOut(ORM):
    id: int
    name: str
    description: str
    cuisine: str
    price_level: int
    delivery_time_min: int
    min_order: MoneyFloat
    address: str
    lat: float
    lng: float
    is_active: bool
    rating: float
    reviews_count: int
    is_favorite: bool = False


class RestaurantDetailOut(RestaurantOut):
    dishes: list[DishOut] = []


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str = Field(default="", max_length=1000)


class ReviewOut(ORM):
    id: int
    restaurant_id: int
    rating: int
    text: str
    created_at: datetime
    author: str
