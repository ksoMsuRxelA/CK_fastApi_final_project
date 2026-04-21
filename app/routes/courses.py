"""Эндпоинты для курсов и префеквизитов."""
from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, DbSession
from app.schemas import (
    CourseCreate,
    CourseRead,
    CourseUpdate,
    PrerequisiteCreate,
    PrerequisiteRead,
)
from app.services import course_service, prerequisite_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseRead], summary="Список всех курсов")
async def list_courses(session: DbSession) -> list[CourseRead]:
    """Публичный список курсов."""
    courses = await course_service.list_courses(session)
    return [CourseRead.model_validate(c) for c in courses]


@router.get("/{course_id}", response_model=CourseRead, summary="Получить курс по id")
async def get_course(course_id: int, session: DbSession) -> CourseRead:
    """Публичный просмотр одного курса."""
    try:
        course = await course_service.get_course(session, course_id)
    except course_service.CourseNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found") from exc
    return CourseRead.model_validate(course)


@router.post(
    "",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать курс (требует авторизации)",
)
async def create_course(
    data: CourseCreate,
    session: DbSession,
    _user: CurrentUser,
) -> CourseRead:
    """Создать новый курс. Требует JWT."""
    try:
        course = await course_service.create_course(session, data)
    except course_service.CourseCodeConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return CourseRead.model_validate(course)


@router.patch(
    "/{course_id}",
    response_model=CourseRead,
    summary="Обновить курс (требует авторизации)",
)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    session: DbSession,
    _user: CurrentUser,
) -> CourseRead:
    """Частично обновить поля курса."""
    try:
        course = await course_service.update_course(session, course_id, data)
    except course_service.CourseNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found") from exc
    except course_service.CourseCodeConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return CourseRead.model_validate(course)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить курс (требует авторизации)",
)
async def delete_course(
    course_id: int,
    session: DbSession,
    _user: CurrentUser,
) -> None:
    """Удалить курс. Каскадно удалит связанные префеквизиты и записи."""
    try:
        await course_service.delete_course(session, course_id)
    except course_service.CourseNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found") from exc


# ---------- Префеквизиты ----------

@router.get(
    "/{course_id}/prerequisites",
    response_model=list[PrerequisiteRead],
    summary="Список префеквизитов курса",
)
async def list_prerequisites(
    course_id: int,
    session: DbSession,
) -> list[PrerequisiteRead]:
    """Вернуть все рёбра course_id -> prereq_id для курса."""
    try:
        edges = await prerequisite_service.list_prerequisites(session, course_id)
    except course_service.CourseNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found") from exc
    return [PrerequisiteRead.model_validate(e) for e in edges]


@router.post(
    "/{course_id}/prerequisites",
    response_model=PrerequisiteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить префеквизит (требует авторизации)",
)
async def add_prerequisite(
    course_id: int,
    data: PrerequisiteCreate,
    session: DbSession,
    _user: CurrentUser,
) -> PrerequisiteRead:
    """Добавить ребро. Бросает 409 если создаст цикл или уже существует."""
    try:
        edge = await prerequisite_service.add_prerequisite(
            session, course_id, data.prereq_id
        )
    except course_service.CourseNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found") from exc
    except prerequisite_service.PrerequisiteCycleError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except prerequisite_service.PrerequisiteConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return PrerequisiteRead.model_validate(edge)


@router.delete(
    "/{course_id}/prerequisites/{prereq_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить префеквизит (требует авторизации)",
)
async def remove_prerequisite(
    course_id: int,
    prereq_id: int,
    session: DbSession,
    _user: CurrentUser,
) -> None:
    """Удалить ребро course_id -> prereq_id."""
    try:
        await prerequisite_service.remove_prerequisite(session, course_id, prereq_id)
    except prerequisite_service.PrerequisiteNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
