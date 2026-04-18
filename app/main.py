"""Точка входа приложения FastAPI."""
from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="REST API для планирования учебной траектории студента",
    version="0.1.0",
)


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    """Корневой эндпоинт для проверки работоспособности."""
    return {"status": "ok", "service": settings.app_name}


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health-check эндпоинт."""
    return {"status": "healthy"}
