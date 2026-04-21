"""Сервисный слой для работы с курсами."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Course
from app.schemas import CourseCreate, CourseUpdate


class CourseNotFoundError(Exception):
    """Курс не найден."""


class CourseCodeConflictError(Exception):
    """Курс с таким кодом уже существует."""


async def list_courses(session: AsyncSession) -> list[Course]:
    """Вернуть все курсы из каталога."""
    result = await session.execute(select(Course).order_by(Course.code))
    return list(result.scalars().all())


async def get_course(session: AsyncSession, course_id: int) -> Course:
    """Получить курс по id или бросить CourseNotFoundError."""
    course = await session.get(Course, course_id)
    if course is None:
        raise CourseNotFoundError(f"Course id={course_id} not found")
    return course


async def create_course(session: AsyncSession, data: CourseCreate) -> Course:
    """Создать новый курс."""
    course = Course(**data.model_dump())
    session.add(course)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise CourseCodeConflictError(
            f"Course with code {data.code!r} already exists"
        ) from exc
    await session.refresh(course)
    return course


async def update_course(
    session: AsyncSession,
    course_id: int,
    data: CourseUpdate,
) -> Course:
    """Частично обновить курс."""
    course = await get_course(session, course_id)

    patch = data.model_dump(exclude_unset=True)
    for field, value in patch.items():
        setattr(course, field, value)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise CourseCodeConflictError(
            f"Course with code {data.code!r} already exists"
        ) from exc
    await session.refresh(course)
    return course


async def delete_course(session: AsyncSession, course_id: int) -> None:
    """Удалить курс. Каскад удалит его префеквизиты и записи."""
    course = await get_course(session, course_id)
    await session.delete(course)
    await session.commit()
