"""Pydantic-схемы для эндпоинта построения учебного плана."""
from pydantic import BaseModel, Field


class StudyPlanRequest(BaseModel):
    """Входные параметры для построения плана."""

    target_course_id: int = Field(gt=0, description="ID целевого курса")
    max_credits_per_semester: int = Field(
        ge=1,
        le=30,
        description="Максимальная нагрузка на семестр в кредитах",
    )
    completed_course_ids: list[int] = Field(
        default_factory=list,
        description=(
            "ID уже пройденных курсов. Если пуст, берутся из enrollments "
            "пользователя со статусом completed."
        ),
    )


class PlannedCourseRead(BaseModel):
    """Курс в семестре плана."""

    course_id: int
    course_code: str
    course_title: str
    credits: int


class SemesterRead(BaseModel):
    """Один семестр плана."""

    number: int
    courses: list[PlannedCourseRead]
    total_credits: int


class StudyPlanResponse(BaseModel):
    """Построенный план."""

    semesters: list[SemesterRead]
    total_credits: int
    total_courses: int
    target_course_id: int
