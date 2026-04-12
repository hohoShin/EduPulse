"""강사 스케줄링 API 라우터 (DB 연동)."""
import math
from typing import Optional

_UNASSIGNED = "미배정 (강사 추가 필요)"

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from edupulse.api.dependencies import get_db
from edupulse.api.schemas.schedule import (
    AssignmentPlan,
    ClassAssignment,
    InstructorResponse,
    ScheduleRequest,
    ScheduleResponse,
)
from edupulse.db_models.instructor import Instructor

router = APIRouter()

_CLASS_CAPACITY = 30  # 강의실당 최대 수용 인원

# 시간대 슬롯 매핑: DB의 짧은 이름 → 표시용 전체 이름
_SLOT_DISPLAY = {
    "오전": "오전 (09:00-12:00)",
    "오후": "오후 (13:00-16:00)",
    "저녁": "저녁 (18:00-21:00)",
}
_DEFAULT_SLOTS = ["오전 (09:00-12:00)", "오후 (13:00-16:00)", "저녁 (18:00-21:00)"]


def _class_label(idx: int) -> str:
    """반 이름 라벨 생성. 0→A, 25→Z, 26→AA, 27→AB, ..."""
    label = ""
    n = idx
    while True:
        label = chr(65 + n % 26) + label
        n = n // 26 - 1
        if n < 0:
            break
    return label


@router.get("/schedule/instructors", response_model=list[InstructorResponse])
def list_instructors(
    field: Optional[str] = Query(None, description="분야 필터 (coding/security/game/art)"),
    db: Session = Depends(get_db),
):
    """전체 강사 목록 조회. 분야별 필터 지원."""
    stmt = select(Instructor).where(Instructor.is_active.is_(True))
    if field:
        stmt = stmt.where(Instructor.field == field)
    stmt = stmt.order_by(Instructor.id)
    return db.execute(stmt).scalars().all()


@router.post("/schedule/suggest", response_model=ScheduleResponse)
def suggest_schedule(
    request: ScheduleRequest,
    db: Session = Depends(get_db),
):
    """강사 수 및 강의실 수 계산 및 배정 계획 생성.

    field가 제공되면 해당 분야 강사를 DB에서 조회하여 실제 이름으로 배정한다.
    강사가 부족하면 '미배정 (강사 추가 필요)'로 표시.
    """
    required_instructors = math.ceil(request.predicted_enrollment / 15)
    required_classrooms = math.ceil(request.predicted_enrollment / _CLASS_CAPACITY)

    # DB에서 해당 분야 활성 강사 조회
    available_instructors: list[Instructor] = []
    if request.field:
        stmt = (
            select(Instructor)
            .where(Instructor.field == request.field, Instructor.is_active.is_(True))
            .order_by(Instructor.id)
        )
        available_instructors = list(db.execute(stmt).scalars().all())

    # 강의실별 배정 계획 생성 (Greedy 최적 배정)
    classes: list[ClassAssignment] = []
    remaining = request.predicted_enrollment

    if available_instructors:
        # 강사별 배정 추적 상태
        assigned_count: dict[int, int] = {inst.id: 0 for inst in available_instructors}
        slot_usage: dict[int, set[str]] = {inst.id: set() for inst in available_instructors}

        for i in range(required_classrooms):
            capacity = min(remaining, _CLASS_CAPACITY)

            # 배정 가능한 (강사, 시간대) 후보 필터링
            candidates: list[tuple[Instructor, str]] = []
            for inst in available_instructors:
                if assigned_count[inst.id] >= inst.max_classes:
                    continue
                for slot in (inst.available_slots or []):
                    if slot not in slot_usage[inst.id]:
                        candidates.append((inst, slot))

            if candidates:
                # 부하 균등: 배정 수 적은 강사 우선, 동률 시 잔여 슬롯 적은 강사 우선
                candidates.sort(key=lambda x: (
                    assigned_count[x[0].id],
                    len(x[0].available_slots or []) - assigned_count[x[0].id],
                ))
                inst, slot = candidates[0]
                assigned_count[inst.id] += 1
                slot_usage[inst.id].add(slot)
                instructor_name = inst.name
                display_slot = _SLOT_DISPLAY.get(slot, slot)
            else:
                instructor_name = _UNASSIGNED
                display_slot = _DEFAULT_SLOTS[i % len(_DEFAULT_SLOTS)]

            classes.append(
                ClassAssignment(
                    class_number=i + 1,
                    class_name=f"{_class_label(i)}반",
                    instructor_slot=instructor_name,
                    time_slot=display_slot,
                    capacity=capacity,
                    classroom=f"강의실 {i + 1}",
                )
            )
            remaining -= capacity
    else:
        # 강사 정보 없으면 기존 fallback
        for i in range(required_classrooms):
            capacity = min(remaining, _CLASS_CAPACITY)
            classes.append(
                ClassAssignment(
                    class_number=i + 1,
                    class_name=f"{_class_label(i)}반",
                    instructor_slot=f"강사 {i + 1}",
                    time_slot=_DEFAULT_SLOTS[i % len(_DEFAULT_SLOTS)],
                    capacity=capacity,
                    classroom=f"강의실 {i + 1}",
                )
            )
            remaining -= capacity

    # 실제 배정된 강사 수 및 미배정 반 수 계산
    unassigned = sum(1 for c in classes if c.instructor_slot == _UNASSIGNED)
    assigned_instructor_count = len({
        c.instructor_slot for c in classes if c.instructor_slot != _UNASSIGNED
    })
    unassigned_note = f" ({unassigned}개 반 강사 추가 필요)" if unassigned > 0 else ""

    assignment_plan = AssignmentPlan(
        classes=classes,
        summary=(
            f"총 {request.predicted_enrollment}명 대상 {required_classrooms}개 반 편성. "
            f"강사 {assigned_instructor_count}명 배정.{unassigned_note}"
        ),
    )

    return ScheduleResponse(
        course_name=request.course_name,
        start_date=request.start_date,
        predicted_enrollment=request.predicted_enrollment,
        required_instructors=assigned_instructor_count if available_instructors else required_instructors,
        required_classrooms=required_classrooms,
        assignment_plan=assignment_plan,
    )
