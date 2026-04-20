"""Схема ответа с JWT-токеном."""
from pydantic import BaseModel


class Token(BaseModel):
    """Ответ эндпоинта логина с JWT."""

    access_token: str
    token_type: str = "bearer"
