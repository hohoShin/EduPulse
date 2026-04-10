"""강사 스케줄링 API 라우터 (rule-based MVP)."""
import math

from fastapi import APIRouter

from edupulse.api.schemas.schedule import AssignmentPlan, ClassAssignment, ScheduleRequest, ScheduleResponse

router = APIRouter()

_CLASS_CAPACITY = 30  # 강의실당 최대 수용 인원
_INSTRUCTORS_PER_CLASS = 1  # 강의실당 강사 수


@router.post("/schedule/suggest", response_model=ScheduleResponse)
def suggest_schedule(request: ScheduleRequest):
    """강사 수 및 강의실 수 계산 및 배정 계획 생성.

    - 강사 수: ceil(수강생 수 / 15)
    - 강의실 수: ceil(수강생 수 / 30)
    - assignment_plan: 강의실별 배정 계획 (rule-based)
    """
    required_instructors = math.ceil(request.predicted_enrollment / 15)
    required_classrooms = math.ceil(request.predicted_enrollment / _CLASS_CAPACITY)

    # rule-based 배정 계획 생성
    classes: list[ClassAssignment] = []
    remaining = request.predicted_enrollment
    time_slots = ["09:00-12:00", "13:00-16:00", "17:00-20:00"]

    for i in range(required_classrooms):
        capacity = min(remaining, _CLASS_CAPACITY)
        classes.append(
            ClassAssignment(
                class_number=i + 1,
                instructor_slot=f"강사 {i + 1}",
                time_slot=time_slots[i % len(time_slots)],
                capacity=capacity,
            )
        )
        remaining -= capacity

    assignment_plan = AssignmentPlan(
        classes=classes,
        summary=(
            f"총 {request.predicted_enrollment}명 대상 {required_classrooms}개 반 편성. "
            f"강사 {required_instructors}명 배정."
        ),
    )

    return ScheduleResponse(
        course_name=request.course_name,
        start_date=request.start_date,
        predicted_enrollment=request.predicted_enrollment,
        required_instructors=required_instructors,
        required_classrooms=required_classrooms,
        assignment_plan=assignment_plan,
    )
