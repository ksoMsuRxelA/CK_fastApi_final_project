"""Модель курса."""
from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Course(Base):
    """Курс в каталоге."""

    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("credits BETWEEN 1 AND 10", name="ck_courses_credits_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Рёбра графа, где этот курс — "потребитель" (нужны его префеквизиты).
    prerequisites: Mapped[list["Prerequisite"]] = relationship(
        back_populates="course",
        foreign_keys="Prerequisite.course_id",
        cascade="all, delete-orphan",
    )
    # Рёбра, где этот курс — сам префеквизит для других.
    dependents: Mapped[list["Prerequisite"]] = relationship(
        back_populates="prereq",
        foreign_keys="Prerequisite.prereq_id",
        cascade="all, delete-orphan",
    )

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Course id={self.id} code={self.code!r}>"
