"""강사 스케줄링 API 요청/응답 스키마."""
from datetime import date
from typing import Optional

from pydantic import BaseModel


class ScheduleRequest(BaseModel):
    course_name: str
    start_date: date
    predicted_enrollment: int


class ClassAssignment(BaseModel):
    class_number: int
    instructor_slot: str
    time_slot: str
    capacity: int


class AssignmentPlan(BaseModel):
    classes: list[ClassAssignment]
    summary: str


class ScheduleResponse(BaseModel):
    course_name: str
    start_date: date
    predicted_enrollment: int
    required_instructors: int
    required_classrooms: int
    assignment_plan: Optional[AssignmentPlan] = None
