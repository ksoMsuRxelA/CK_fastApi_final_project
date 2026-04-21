"""Эндпоинты для записей текущего пользователя на курсы."""
from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, DbSession
from app.schemas import EnrollmentCreate, EnrollmentRead, EnrollmentUpdate
from app.services import course_service, enrollment_service

router = APIRouter(prefix="/users/me/enrollments", tags=["enrollments"])


@router.get("", response_model=list[EnrollmentRead], summary="Мои записи на курсы")
async def list_my_enrollments(
    current_user: CurrentUser,
    session: DbSession,
) -> list[EnrollmentRead]:
    """Список всех записей текущего пользователя."""
    items = await enrollment_service.list_user_enrollments(session, current_user.id)
    return [EnrollmentRead.model_validate(i) for i in items]


@router.post(
    "",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Записаться на курс",
)
async def create_my_enrollment(
    data: EnrollmentCreate,
    current_user: CurrentUser,
    session: DbSession,
) -> EnrollmentRead:
    """Создать запись на курс от имени текущего пользователя."""
    try:
        enrollment = await enrollment_service.create_enrollment(
            session, current_user.id, data
        )
    except course_service.CourseNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found") from exc
    except enrollment_service.EnrollmentConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return EnrollmentRead.model_validate(enrollment)


@router.patch(
    "/{enrollment_id}",
    response_model=EnrollmentRead,
    summary="Обновить статус/семестр записи",
)
async def update_my_enrollment(
    enrollment_id: int,
    data: EnrollmentUpdate,
    current_user: CurrentUser,
    session: DbSession,
) -> EnrollmentRead:
    """Частичное обновление своей записи."""
    try:
        enrollment = await enrollment_service.update_enrollment(
            session, enrollment_id, current_user.id, data
        )
    except enrollment_service.EnrollmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return EnrollmentRead.model_validate(enrollment)


@router.delete(
    "/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить свою запись",
)
async def delete_my_enrollment(
    enrollment_id: int,
    current_user: CurrentUser,
    session: DbSession,
) -> None:
    """Удалить собственную запись на курс."""
    try:
        await enrollment_service.delete_enrollment(
            session, enrollment_id, current_user.id
        )
    except enrollment_service.EnrollmentNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
