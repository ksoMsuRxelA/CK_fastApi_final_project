"""Pydantic-схемы для префеквизитов."""
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self


class PrerequisiteCreate(BaseModel):
    """Добавление ребра: course_id зависит от prereq_id."""

    prereq_id: int = Field(gt=0)


class PrerequisiteRead(BaseModel):
    """Представление ребра на чтение."""

    model_config = ConfigDict(from_attributes=True)

    course_id: int
    prereq_id: int

    @model_validator(mode="after")
    def _no_self_loop(self) -> Self:
        if self.course_id == self.prereq_id:
            raise ValueError("course_id и prereq_id не могут совпадать")
        return self
