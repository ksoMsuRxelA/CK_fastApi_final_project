"""Точка входа приложения FastAPI."""
from fastapi import FastAPI

from app.config import get_settings
from app.routes import auth as auth_routes
from app.routes import courses as courses_routes
from app.routes import enrollments as enrollments_routes

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="REST API для планирования учебной траектории студента",
    version="0.1.0",
)

app.include_router(auth_routes.router)
app.include_router(courses_routes.router)
app.include_router(enrollments_routes.router)


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    """Корневой эндпоинт для проверки работоспособности."""
    return {"status": "ok", "service": settings.app_name}


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Health-check эндпоинт."""
    return {"status": "healthy"}
