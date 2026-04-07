"""강사 스케줄링 API 라우터 (rule-based MVP)."""
import math

from fastapi import APIRouter

from edupulse.api.schemas.schedule import ScheduleRequest, ScheduleResponse

router = APIRouter()


@router.post("/schedule/suggest", response_model=ScheduleResponse)
def suggest_schedule(request: ScheduleRequest):
    """강사 수 및 강의실 수 계산. predicted_enrollment / 15 = 강사 수 (올림), / 30 = 강의실 수 (올림)."""
    required_instructors = math.ceil(request.predicted_enrollment / 15)
    required_classrooms = math.ceil(request.predicted_enrollment / 30)

    return ScheduleResponse(
        course_name=request.course_name,
        start_date=request.start_date,
        predicted_enrollment=request.predicted_enrollment,
        required_instructors=required_instructors,
        required_classrooms=required_classrooms,
        assignment_plan=None,  # TODO: Instructor 테이블 연동 후 구현
    )
