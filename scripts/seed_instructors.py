"""강사 시드 데이터 투입 스크립트.

분야별 3~4명씩 총 14명의 가상 강사를 삽입한다.
중복 실행 시 이미 존재하는 강사는 건너뛴다.

실행:
    python scripts/seed_instructors.py
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from edupulse.database import SessionLocal, engine, Base
from edupulse.db_models.instructor import Instructor

SEED_INSTRUCTORS = [
    # coding (4명)
    {"name": "김코딩", "field": "coding", "available_slots": ["오전", "오후", "저녁"], "max_classes": 3},
    {"name": "박파이썬", "field": "coding", "available_slots": ["오전", "오후"], "max_classes": 2},
    {"name": "이자바", "field": "coding", "available_slots": ["오후", "저녁"], "max_classes": 2},
    {"name": "최웹개발", "field": "coding", "available_slots": ["오전", "저녁"], "max_classes": 2},
    # security (3명)
    {"name": "이보안", "field": "security", "available_slots": ["오전", "오후", "저녁"], "max_classes": 2},
    {"name": "정해킹", "field": "security", "available_slots": ["오후", "저녁"], "max_classes": 2},
    {"name": "한시큐", "field": "security", "available_slots": ["오전", "오후"], "max_classes": 2},
    # game (4명)
    {"name": "강유니티", "field": "game", "available_slots": ["오전", "오후"], "max_classes": 2},
    {"name": "윤언리얼", "field": "game", "available_slots": ["오후", "저녁"], "max_classes": 2},
    {"name": "임게임", "field": "game", "available_slots": ["오전", "오후", "저녁"], "max_classes": 3},
    {"name": "조기획", "field": "game", "available_slots": ["오전", "저녁"], "max_classes": 2},
    # art (3명)
    {"name": "서디자인", "field": "art", "available_slots": ["오전", "오후"], "max_classes": 2},
    {"name": "문일러", "field": "art", "available_slots": ["오후", "저녁"], "max_classes": 2},
    {"name": "장그래픽", "field": "art", "available_slots": ["오전", "오후", "저녁"], "max_classes": 3},
]


def seed_instructors():
    """강사 시드 데이터 투입. 이미 존재하면 건너뛴다."""
    Base.metadata.create_all(engine)

    session = SessionLocal()
    try:
        existing_names = set(
            row[0] for row in session.execute(select(Instructor.name)).all()
        )

        added = 0
        for data in SEED_INSTRUCTORS:
            if data["name"] in existing_names:
                continue
            session.add(Instructor(**data))
            added += 1

        session.commit()
        total = session.query(Instructor).count()
        print(f"시드 완료: {added}명 추가 (전체 {total}명)")
    finally:
        session.close()


if __name__ == "__main__":
    seed_instructors()
