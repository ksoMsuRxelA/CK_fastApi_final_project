"""Сервисный слой для работы с пользователями."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.password import hash_password, verify_password
from app.models import User
from app.schemas import UserCreate


class UserAlreadyExistsError(Exception):
    """Пользователь с таким email уже существует."""


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Найти пользователя по email."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Найти пользователя по id."""
    return await session.get(User, user_id)


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    """Создать нового пользователя. Бросает UserAlreadyExistsError при дубликате email."""
    existing = await get_user_by_email(session, data.email)
    if existing is not None:
        raise UserAlreadyExistsError(f"User with email {data.email} already exists")

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """Проверить креды. Вернёт User при успехе, иначе None."""
    user = await get_user_by_email(session, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
