"""Сервисный слой для эндпоинта /study-plan."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.algorithms.study_plan import (
    CourseNode,
    StudyPlan,
    build_study_plan,
)
from app.models import Course, Enrollment, EnrollmentStatus, Prerequisite


async def _load_graph(
    session: AsyncSession,
) -> tuple[list[CourseNode], list[tuple[int, int]], dict[int, Course]]:
    """Загрузить каталог курсов и все рёбра префеквизитов."""
    courses_result = await session.execute(select(Course))
    all_courses_db = list(courses_result.scalars().all())
    course_map = {c.id: c for c in all_courses_db}
    nodes = [CourseNode(id=c.id, credits=c.credits) for c in all_courses_db]

    edges_result = await session.execute(
        select(Prerequisite.course_id, Prerequisite.prereq_id)
    )
    edges = list(edges_result.all())

    return nodes, edges, course_map


async def _load_completed_from_enrollments(
    session: AsyncSession,
    user_id: int,
) -> set[int]:
    """Получить множество id курсов, записанных пользователем со статусом completed."""
    result = await session.execute(
        select(Enrollment.course_id).where(
            Enrollment.user_id == user_id,
            Enrollment.status == EnrollmentStatus.COMPLETED.value,
        )
    )
    return {row[0] for row in result.all()}


async def build_plan_for_user(
    session: AsyncSession,
    user_id: int,
    target_course_id: int,
    max_credits_per_semester: int,
    completed_override: list[int] | None = None,
) -> tuple[StudyPlan, dict[int, Course]]:
    """Построить план для пользователя.

    Если completed_override задан — используется он.
    Иначе подтягиваются курсы со статусом completed из enrollments пользователя.
    """
    nodes, edges, course_map = await _load_graph(session)

    if completed_override is not None:
        completed = set(completed_override)
    else:
        completed = await _load_completed_from_enrollments(session, user_id)

    plan = build_study_plan(
        all_courses=nodes,
        prerequisites=edges,
        target_id=target_course_id,
        completed_ids=completed,
        max_credits_per_semester=max_credits_per_semester,
    )
    return plan, course_map
