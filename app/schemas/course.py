"""Pydantic-схемы для курсов."""
from pydantic import BaseModel, ConfigDict, Field


class CourseBase(BaseModel):
    """Общие поля курса."""

    code: str = Field(min_length=2, max_length=20, pattern=r"^[A-Z0-9_-]+$")
    title: str = Field(min_length=1, max_length=255)
    credits: int = Field(ge=1, le=10)
    description: str | None = Field(default=None, max_length=2000)


class CourseCreate(CourseBase):
    """Данные для создания курса."""


class CourseUpdate(BaseModel):
    """Частичное обновление курса — все поля опциональны."""

    code: str | None = Field(default=None, min_length=2, max_length=20, pattern=r"^[A-Z0-9_-]+$")
    title: str | None = Field(default=None, min_length=1, max_length=255)
    credits: int | None = Field(default=None, ge=1, le=10)
    description: str | None = Field(default=None, max_length=2000)


class CourseRead(CourseBase):
    """Представление курса на чтение."""

    model_config = ConfigDict(from_attributes=True)

    id: int
