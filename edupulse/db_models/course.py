"""Course and Cohort ORM models."""
from datetime import datetime, date
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Date, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from edupulse.database import Base


class Course(Base):
    """강좌 테이블. 분야별 교육 과정 정의."""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    field: Mapped[str] = mapped_column(String(50), nullable=False)  # coding/security/game/art
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cohorts: Mapped[list["Cohort"]] = relationship("Cohort", back_populates="course")


class Cohort(Base):
    """기수 테이블. 강좌의 개설 회차."""

    __tablename__ = "cohorts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    cohort_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    course: Mapped["Course"] = relationship("Course", back_populates="cohorts")
    enrollments: Mapped[list["Enrollment"]] = relationship(  # type: ignore[name-defined]
        "Enrollment", back_populates="cohort"
    )
