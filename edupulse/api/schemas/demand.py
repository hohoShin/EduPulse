"""수요 예측 API 요청/응답 스키마."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from edupulse.constants import DemandTier


class DemandRequest(BaseModel):
    course_name: str  # 현재 모델에서 미사용 — 향후 과정별 세분화 시 활용 예정
    start_date: date
    field: Literal["coding", "security", "game", "art"]
    model_name: Literal["xgboost", "prophet", "ensemble"] = "ensemble"


class ConfidenceInterval(BaseModel):
    lower: float
    upper: float


class DemandResponse(BaseModel):
    course_name: str
    field: str
    predicted_enrollment: int
    demand_tier: DemandTier
    confidence_interval: ConfidenceInterval
    model_used: str
    prediction_date: datetime
