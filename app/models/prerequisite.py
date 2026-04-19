"""Модель префеквизита — ребро графа зависимостей курсов."""
from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Prerequisite(Base):
    """Ребро графа: чтобы пройти course_id, нужен prereq_id."""

    __tablename__ = "prerequisites"
    __table_args__ = (
        CheckConstraint(
            "course_id <> prereq_id",
            name="ck_prerequisites_no_self_loop",
        ),
    )

    course_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        primary_key=True,
    )
    prereq_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        primary_key=True,
    )

    course: Mapped["Course"] = relationship(
        back_populates="prerequisites",
        foreign_keys=[course_id],
    )
    prereq: Mapped["Course"] = relationship(
        back_populates="dependents",
        foreign_keys=[prereq_id],
    )

    def __repr__(self) -> str:
        return f"<Prerequisite course_id={self.course_id} prereq_id={self.prereq_id}>"
