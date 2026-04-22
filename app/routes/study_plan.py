"""Эндпоинт построения учебного плана."""
from fastapi import APIRouter, HTTPException, status

from app.algorithms.study_plan import (
    CoursesMissingError,
    CreditLimitExceededError,
)
from app.dependencies import CurrentUser, DbSession
from app.schemas import (
    PlannedCourseRead,
    SemesterRead,
    StudyPlanRequest,
    StudyPlanResponse,
)
from app.services import study_plan_service

router = APIRouter(tags=["study-plan"])


@router.post(
    "/study-plan",
    response_model=StudyPlanResponse,
    summary="Построить план прохождения курсов до целевого",
)
async def create_study_plan(
    data: StudyPlanRequest,
    current_user: CurrentUser,
    session: DbSession,
) -> StudyPlanResponse:
    """Строит оптимальный план по семестрам.

    Если completed_course_ids не передан — используются курсы со статусом
    completed из enrollments пользователя.
    """
    try:
        plan, course_map = await study_plan_service.build_plan_for_user(
            session=session,
            user_id=current_user.id,
            target_course_id=data.target_course_id,
            max_credits_per_semester=data.max_credits_per_semester,
            completed_override=(
                data.completed_course_ids if data.completed_course_ids else None
            ),
        )
    except CoursesMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except CreditLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Сериализация: обогатим курсы кодами и названиями
    semesters = [
        SemesterRead(
            number=s.number,
            total_credits=s.total_credits,
            courses=[
                PlannedCourseRead(
                    course_id=pc.course_id,
                    course_code=course_map[pc.course_id].code,
                    course_title=course_map[pc.course_id].title,
                    credits=pc.credits,
                )
                for pc in s.courses
            ],
        )
        for s in plan.semesters
    ]

    return StudyPlanResponse(
        semesters=semesters,
        total_credits=plan.total_credits,
        total_courses=plan.total_courses,
        target_course_id=data.target_course_id,
    )
