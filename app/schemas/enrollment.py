"""Pydantic-схемы для записей пользователя на курс."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enrollment import EnrollmentStatus


class EnrollmentCreate(BaseModel):
    """Создание записи пользователя на курс."""

    course_id: int = Field(gt=0)
    status: EnrollmentStatus = EnrollmentStatus.PLANNED
    semester: int | None = Field(default=None, ge=1, le=20)


class EnrollmentUpdate(BaseModel):
    """Обновление статуса/семестра записи."""

    status: EnrollmentStatus | None = None
    semester: int | None = Field(default=None, ge=1, le=20)


class EnrollmentRead(BaseModel):
    """Представление записи на чтение."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    status: EnrollmentStatus
    semester: int | None
    created_at: datetime
