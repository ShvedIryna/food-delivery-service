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


class OrderItemIn(BaseModel):
    dish_id: int
    quantity: int = Field(ge=1, le=50)


class OrderCreate(BaseModel):
    restaurant_id: int
    items: list[OrderItemIn] = Field(min_length=1)
    delivery_type: str = "STANDARD"
    payment_method: str = "CARD"
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    comment: str | None = Field(default=None, max_length=500)
    use_bonus: int = Field(default=0, ge=0)
    card_number: str | None = None


class OrderItemOut(ORM):
    id: int
    dish_id: int | None
    dish_name: str
    unit_price: MoneyFloat
    quantity: int


class OrderOut(ORM):
    id: int
    restaurant_id: int
    restaurant_name: str
    status: str
    status_title: str
    delivery_type: str
    payment_method: str
    payment_status: str
    transaction_id: str | None
    address: str | None
    lat: float | None
    lng: float | None
    comment: str | None
    subtotal: MoneyFloat
    delivery_fee: MoneyFloat
    discount: MoneyFloat
    bonus_used: int
    bonus_earned: int
    total: MoneyFloat
    estimated_minutes: int
    created_at: datetime
    status_changed_at: datetime
    can_cancel: bool
    items: list[OrderItemOut]


class PriceQuoteOut(BaseModel):
    subtotal: MoneyFloat
    delivery_fee: MoneyFloat
    discount: MoneyFloat
    bonus_used: int
    total: MoneyFloat
    notes: list[str]
    estimated_minutes: int
    bonus_to_earn: int


class NotificationOut(ORM):
    id: int
    order_id: int | None
    kind: str
    title: str
    message: str
    is_read: bool
    created_at: datetime


class RestaurantIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = ""
    cuisine: str
    price_level: int = Field(default=2, ge=1, le=3)
    delivery_time_min: int = Field(default=40, ge=5, le=180)
    min_order: float = Field(default=0, ge=0)
    address: str = ""
    lat: float
    lng: float
    is_active: bool = True


class DishIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = ""
    category: str = "Основні страви"
    price: float = Field(gt=0)
    weight_g: int | None = None
    is_available: bool = True


class UserAdminUpdate(BaseModel):
    role: str | None = None
    card_type: str | None = None
    bonus_points: int | None = Field(default=None, ge=0)
