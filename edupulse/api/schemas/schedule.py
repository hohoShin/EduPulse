"""강사 스케줄링 API 요청/응답 스키마."""
from datetime import date
from typing import Optional

from pydantic import BaseModel


class ScheduleRequest(BaseModel):
    course_name: str
    start_date: date
    predicted_enrollment: int


class ScheduleResponse(BaseModel):
    course_name: str
    start_date: date
    predicted_enrollment: int
    required_instructors: int
    required_classrooms: int
    assignment_plan: Optional[str] = None
