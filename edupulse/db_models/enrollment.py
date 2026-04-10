"""Enrollment ORM model."""
from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from edupulse.database import Base


class Enrollment(Base):
    """수강 등록 테이블."""

    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cohort_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False
    )
    student_name: Mapped[str] = mapped_column(String(100), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active/cancelled/completed

    cohort: Mapped["Cohort"] = relationship(  # type: ignore[name-defined]
        "Cohort", back_populates="enrollments"
    )
