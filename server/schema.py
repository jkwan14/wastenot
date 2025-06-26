from pydantic import BaseModel
from datetime import date, datetime


class FoodIn(BaseModel):
    name: str
    expiration_date: date
    category_id: int


class FoodOut(FoodIn):
    id: int


class FoodUpdate(BaseModel):
    name: str | None = None
    expiration_date: date | None = None
    category_id: int | None = None


class NotificationIn(BaseModel):
    message: str
    created_at: datetime
    food_id: int


class NotificationOut(NotificationIn):
    notification_id: int

class Config:
     orm_mode = True


class LoginCredentials(BaseModel):
    username: str
    password: str


class SuccessResponse(BaseModel):
    success: bool


class SecretResponse(BaseModel):
    secret: str


class UserPublicDetails(BaseModel):
    username: str
