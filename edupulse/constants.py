"""프로젝트 전역 상수. 모든 모듈이 여기서 import."""
from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class DemandTier(str, Enum):
    HIGH = "High"    # >= 6명 (주간 기준)
    MID = "Mid"      # >= 3명 (주간 기준)
    LOW = "Low"      # < 3명 (주간 기준)


DEMAND_THRESHOLDS = {"high": 6, "mid": 3}

# 분야 → 인코딩 값 (알파벳 순 고정). 모든 모듈이 이 매핑을 단일 진실 소스로 사용한다.
FIELD_ENCODING = {"art": 0, "coding": 1, "game": 2, "security": 3}

# CSV 데이터 파일 경로 (단일 진실 소스)
ENROLLMENT_PATH = str(PROJECT_ROOT / "edupulse/data/raw/internal/enrollment_history.csv")
SEARCH_TRENDS_PATH = str(PROJECT_ROOT / "edupulse/data/raw/external/search_trends.csv")
JOB_POSTINGS_PATH = str(PROJECT_ROOT / "edupulse/data/raw/external/job_postings.csv")
CONSULTATION_PATH = str(PROJECT_ROOT / "edupulse/data/raw/internal/consultation_logs.csv")
STUDENT_PROFILES_PATH = str(PROJECT_ROOT / "edupulse/data/raw/internal/student_profiles.csv")
WEB_LOGS_PATH = str(PROJECT_ROOT / "edupulse/data/raw/internal/web_logs.csv")
CERT_EXAM_PATH = str(PROJECT_ROOT / "edupulse/data/raw/external/cert_exam_schedule.csv")
COMPETITOR_PATH = str(PROJECT_ROOT / "edupulse/data/raw/external/competitor_data.csv")
SEASONAL_PATH = str(PROJECT_ROOT / "edupulse/data/raw/external/seasonal_events.csv")

CSV_PATHS = {
    "enrollment": ENROLLMENT_PATH,
    "search_trends": SEARCH_TRENDS_PATH,
    "job_postings": JOB_POSTINGS_PATH,
    "consultation": CONSULTATION_PATH,
    "student_profiles": STUDENT_PROFILES_PATH,
    "web_logs": WEB_LOGS_PATH,
    "cert_exam": CERT_EXAM_PATH,
    "competitor": COMPETITOR_PATH,
    "seasonal": SEASONAL_PATH,
}


def classify_demand(predicted_count: int) -> DemandTier:
    """예측 인원 → 수요 등급 변환. DemandTier enum 반환."""
    if predicted_count >= DEMAND_THRESHOLDS["high"]:
        return DemandTier.HIGH
    elif predicted_count >= DEMAND_THRESHOLDS["mid"]:
        return DemandTier.MID
    else:
        return DemandTier.LOW
