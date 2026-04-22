"""Общие фикстуры для pytest.

Тесты используют SQLite in-memory с переопределённой зависимостью get_db.
Каждый тест получает чистую БД — это обеспечивает изоляцию тестов.
"""
import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app import models  # noqa: F401  регистрирует модели в metadata
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """TestClient с чистой SQLite-БД для каждого теста.

    Создаётся новый in-memory engine со своим пулом соединений,
    чтобы разные тесты не делили состояние.
    """
    # StaticPool нужен, чтобы все соединения смотрели в одну in-memory БД.
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def _init_schema() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_init_schema())

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    loop.run_until_complete(engine.dispose())
    loop.close()


# ---------- Хелперы регистрации и авторизации ----------

def register_user(
    client: TestClient,
    email: str = "user@example.com",
    password: str = "supersecret123",
    full_name: str = "Test User",
) -> dict[str, Any]:
    """Зарегистрировать пользователя и вернуть его данные."""
    r = client.post(
        "/auth/register",
        json={"email": email, "full_name": full_name, "password": password},
    )
    assert r.status_code == 201, r.json()
    return r.json()


def login(
    client: TestClient,
    email: str = "user@example.com",
    password: str = "supersecret123",
) -> str:
    """Залогиниться и вернуть access_token."""
    r = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert r.status_code == 200, r.json()
    return r.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    """Сформировать заголовок Authorization."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user_token(client: TestClient) -> str:
    """Зарегистрировать дефолтного пользователя и вернуть его токен."""
    register_user(client)
    return login(client)


@pytest.fixture()
def user_headers(user_token: str) -> dict[str, str]:
    return auth_headers(user_token)
