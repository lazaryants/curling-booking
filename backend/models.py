# /var/www/bro/backend/models.py
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)
from typing import Annotated, Literal, Optional
from datetime import datetime, time

# ==================== ПОЛЬЗОВАТЕЛЬСКИЕ ТИПЫ ====================

UserName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=100,
    ),
]

UserPhone = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        max_length=20,
    ),
]

UserEmail = Annotated[
    EmailStr,
    Field(max_length=100),
]

UserPassword = Annotated[
    str,
    StringConstraints(
        min_length=6,
        max_length=128,
    ),
]

UserRole = Literal["user", "admin"]


# ==================== АВТОРИЗАЦИЯ ====================
class UserRegister(BaseModel):
    email: UserEmail
    phone: Optional[UserPhone] = None
    name: UserName
    password: UserPassword


class UserLogin(BaseModel):
    email: str
    password: str


class ProfileUpdate(BaseModel):
    name: Optional[UserName] = None
    phone: Optional[UserPhone] = None
    email: Optional[UserEmail] = None
    password: Optional[UserPassword] = None

# ==================== БРОНИРОВАНИЕ ====================
class BookingCreate(BaseModel):
    lane_id: int
    booking_date: str  # Формат: "2024-02-11"
    start_time: str    # Формат: "10:00"
    end_time: str      # Формат: "11:00"
    
    @field_validator('booking_date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Дата должна быть в формате ГГГГ-ММ-ДД')
        return v
    
    @field_validator('start_time', 'end_time')
    def validate_time(cls, v):
        try:
            datetime.strptime(v, '%H:%M')
        except ValueError:
            raise ValueError('Время должно быть в формате ЧЧ:ММ')
        return v

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    comment: Optional[str] = None

# ==================== АДМИН ====================
class UserCreateAdmin(BaseModel):
    email: UserEmail
    name: UserName
    phone: Optional[UserPhone] = None
    password: UserPassword
    role: UserRole = "user"


class UserUpdate(BaseModel):
    name: Optional[UserName] = None
    phone: Optional[UserPhone] = None
    email: Optional[UserEmail] = None
    password: Optional[UserPassword] = None
    role: Optional[UserRole] = None

# ==================== ОТВЕТЫ ====================
class BookingResponse(BaseModel):
    id: int
    lane_id: int
    lane_name: str
    user_id: int
    user_name: str
    user_phone: str
    booking_date: str
    start_time: str
    end_time: str
    status: str
    comment: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
