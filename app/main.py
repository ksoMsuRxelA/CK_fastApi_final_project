"""Точка входа приложения FastAPI."""
from fastapi import FastAPI

app = FastAPI(
    title="Study Planner API",
    description="REST API для планирования учебной траектории студента",
    version="0.1.0",
)


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    """Корневой эндпоинт для проверки работоспособности."""
    return {"status": "ok", "service": "Study Planner API"}


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health-check эндпоинт."""
    return {"status": "healthy"}
