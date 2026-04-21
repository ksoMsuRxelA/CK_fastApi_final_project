"""Сервисный слой для префеквизитов (рёбер DAG курсов)."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Prerequisite
from app.services.course_service import get_course


class PrerequisiteCycleError(Exception):
    """Добавление ребра создало бы цикл в графе зависимостей."""


class PrerequisiteNotFoundError(Exception):
    """Ребро не найдено."""


class PrerequisiteConflictError(Exception):
    """Такое ребро уже существует или нарушает ограничение."""


async def list_prerequisites(session: AsyncSession, course_id: int) -> list[Prerequisite]:
    """Вернуть все рёбра, где course_id — потребитель."""
    await get_course(session, course_id)  # 404 если курса нет
    result = await session.execute(
        select(Prerequisite).where(Prerequisite.course_id == course_id)
    )
    return list(result.scalars().all())


async def _has_path(
    session: AsyncSession,
    start_id: int,
    target_id: int,
) -> bool:
    """Проверить, существует ли путь из start_id в target_id по рёбрам prereq.

    Рёбра направлены: course_id -> prereq_id ("чтобы пройти course_id, нужен prereq_id").
    Обход идёт по этим рёбрам: из узла X переходим во все Y, где (X, Y) — ребро.
    """
    # Подгрузим весь граф одним запросом — для учебного планировщика это ок.
    result = await session.execute(select(Prerequisite.course_id, Prerequisite.prereq_id))
    edges = result.all()

    # Построим список смежности: course_id -> [prereq_id, ...]
    adjacency: dict[int, list[int]] = {}
    for course_id, prereq_id in edges:
        adjacency.setdefault(course_id, []).append(prereq_id)

    # Итеративный DFS, чтобы избежать рекурсии на больших графах.
    stack = [start_id]
    visited: set[int] = set()
    while stack:
        node = stack.pop()
        if node == target_id:
            return True
        if node in visited:
            continue
        visited.add(node)
        stack.extend(adjacency.get(node, []))
    return False


async def add_prerequisite(
    session: AsyncSession,
    course_id: int,
    prereq_id: int,
) -> Prerequisite:
    """Добавить ребро course_id -> prereq_id с проверками на цикл и существование курсов."""
    if course_id == prereq_id:
        raise PrerequisiteConflictError("course_id и prereq_id не могут совпадать")

    # 404 если любой из курсов не существует
    await get_course(session, course_id)
    await get_course(session, prereq_id)

    # Цикл образуется, если из prereq_id уже достижим course_id
    # (то есть prereq_id транзитивно зависит от course_id).
    if await _has_path(session, prereq_id, course_id):
        raise PrerequisiteCycleError(
            f"Adding prerequisite {prereq_id} to course {course_id} would create a cycle"
        )

    edge = Prerequisite(course_id=course_id, prereq_id=prereq_id)
    session.add(edge)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise PrerequisiteConflictError("Prerequisite already exists") from exc
    return edge


async def remove_prerequisite(
    session: AsyncSession,
    course_id: int,
    prereq_id: int,
) -> None:
    """Удалить ребро course_id -> prereq_id."""
    edge = await session.get(Prerequisite, (course_id, prereq_id))
    if edge is None:
        raise PrerequisiteNotFoundError(
            f"Prerequisite ({course_id} -> {prereq_id}) not found"
        )
    await session.delete(edge)
    await session.commit()
