"""Instructor ORM model. 강사 정보 테이블."""
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from edupulse.database import Base


class Instructor(Base):
    """강사 테이블. 분야별 강사 정보 및 가용 시간대."""

    __tablename__ = "instructors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    field: Mapped[str] = mapped_column(String(50), nullable=False)  # coding/security/game/art
    available_slots: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    max_classes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="2")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
