"""Pydantic-схемы для пользователей."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Общие поля пользователя."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)


class UserCreate(UserBase):
    """Данные для регистрации нового пользователя."""

    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _password_fits_bcrypt(cls, value: str) -> str:
        """Bcrypt молча обрезает пароли длиннее 72 байт — проще запретить явно."""
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 bytes when UTF-8 encoded")
        return value


class UserRead(UserBase):
    """Публичные данные пользователя."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class UserLogin(BaseModel):
    """Данные для входа в систему."""

    email: EmailStr
    password: str
