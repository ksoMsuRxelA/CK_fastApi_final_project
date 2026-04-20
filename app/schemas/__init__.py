"""Пакет Pydantic-схем приложения."""
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentRead,
    EnrollmentUpdate,
)
from app.schemas.prerequisite import PrerequisiteCreate, PrerequisiteRead
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin, UserRead

__all__ = [
    "CourseCreate",
    "CourseRead",
    "CourseUpdate",
    "EnrollmentCreate",
    "EnrollmentRead",
    "EnrollmentUpdate",
    "PrerequisiteCreate",
    "PrerequisiteRead",
    "Token",
    "UserCreate",
    "UserLogin",
    "UserRead",
]
