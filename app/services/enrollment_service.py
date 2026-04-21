"""Сервисный слой для записей пользователя на курсы."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Enrollment
from app.schemas import EnrollmentCreate, EnrollmentUpdate
from app.services.course_service import get_course


class EnrollmentNotFoundError(Exception):
    """Запись не найдена или принадлежит другому пользователю."""


class EnrollmentConflictError(Exception):
    """Пользователь уже записан на этот курс."""


async def list_user_enrollments(
    session: AsyncSession,
    user_id: int,
) -> list[Enrollment]:
    """Вернуть все записи пользователя."""
    result = await session.execute(
        select(Enrollment)
        .where(Enrollment.user_id == user_id)
        .order_by(Enrollment.id)
    )
    return list(result.scalars().all())


async def create_enrollment(
    session: AsyncSession,
    user_id: int,
    data: EnrollmentCreate,
) -> Enrollment:
    """Записать пользователя на курс."""
    await get_course(session, data.course_id)  # 404 если курса нет

    enrollment = Enrollment(
        user_id=user_id,
        course_id=data.course_id,
        status=data.status.value,
        semester=data.semester,
    )
    session.add(enrollment)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise EnrollmentConflictError(
            f"User already has enrollment for course {data.course_id}"
        ) from exc
    await session.refresh(enrollment)
    return enrollment


async def _get_owned_enrollment(
    session: AsyncSession,
    enrollment_id: int,
    user_id: int,
) -> Enrollment:
    """Получить запись, проверив, что она принадлежит указанному пользователю."""
    enrollment = await session.get(Enrollment, enrollment_id)
    if enrollment is None or enrollment.user_id != user_id:
        raise EnrollmentNotFoundError(f"Enrollment id={enrollment_id} not found")
    return enrollment


async def update_enrollment(
    session: AsyncSession,
    enrollment_id: int,
    user_id: int,
    data: EnrollmentUpdate,
) -> Enrollment:
    """Частично обновить свою запись на курс."""
    enrollment = await _get_owned_enrollment(session, enrollment_id, user_id)

    patch = data.model_dump(exclude_unset=True)
    if "status" in patch and patch["status"] is not None:
        enrollment.status = patch["status"].value
    if "semester" in patch:
        enrollment.semester = patch["semester"]

    await session.commit()
    await session.refresh(enrollment)
    return enrollment


async def delete_enrollment(
    session: AsyncSession,
    enrollment_id: int,
    user_id: int,
) -> None:
    """Удалить свою запись на курс."""
    enrollment = await _get_owned_enrollment(session, enrollment_id, user_id)
    await session.delete(enrollment)
    await session.commit()
