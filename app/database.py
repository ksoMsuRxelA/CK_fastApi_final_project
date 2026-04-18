"""Инициализация SQLAlchemy: движок, фабрика сессий, Base."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(  # pylint: disable=invalid-name
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-зависимость для получения сессии БД."""
    async with AsyncSessionLocal() as session:
        yield session
