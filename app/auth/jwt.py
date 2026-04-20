"""Создание и валидация JWT-токенов доступа."""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


class TokenError(Exception):
    """Ошибка валидации или декодирования токена."""


def create_access_token(
    subject: str | int,
    expires_minutes: int | None = None,
) -> str:
    """Создать подписанный JWT-токен.

    Args:
        subject: идентификатор субъекта (обычно user id), кладётся в sub.
        expires_minutes: срок жизни в минутах; по умолчанию из настроек.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Декодировать и проверить JWT-токен. Возвращает payload."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise TokenError(str(exc)) from exc
