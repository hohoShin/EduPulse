"""프로젝트 전역 상수. 모든 모듈이 여기서 import."""
from enum import Enum


class DemandTier(str, Enum):
    HIGH = "High"    # >= 6명 (주간 기준)
    MID = "Mid"      # >= 3명 (주간 기준)
    LOW = "Low"      # < 3명 (주간 기준)


DEMAND_THRESHOLDS = {"high": 6, "mid": 3}


def classify_demand(predicted_count: int) -> DemandTier:
    """예측 인원 → 수요 등급 변환. DemandTier enum 반환."""
    if predicted_count >= DEMAND_THRESHOLDS["high"]:
        return DemandTier.HIGH
    elif predicted_count >= DEMAND_THRESHOLDS["mid"]:
        return DemandTier.MID
    else:
        return DemandTier.LOW
