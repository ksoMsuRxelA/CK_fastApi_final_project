"""Хеширование и проверка паролей через bcrypt."""
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Вернуть bcrypt-хеш от пароля."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Проверить, соответствует ли plain-пароль хешу."""
    return _pwd_context.verify(plain, hashed)
