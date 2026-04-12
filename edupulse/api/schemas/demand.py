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


class DemandTrendRequest(BaseModel):
    """수요 트렌드 요청. 과거 8주 실적 + 미래 4주 예측 시계열."""

    field: Literal["coding", "security", "game", "art"]
    model_name: Literal["xgboost", "prophet", "ensemble"] = "ensemble"


class TrendPoint(BaseModel):
    """시계열 트렌드 포인트."""

    date: str
    value: float
    upper: float | None = None
    lower: float | None = None
    category: Literal["actual", "forecast"]


class DemandTrendResponse(BaseModel):
    """수요 트렌드 응답. 과거 실적 + 미래 예측 포인트."""

    field: str
    points: list[TrendPoint]
    model_used: str


class ClosureRiskRequest(BaseModel):
    course_name: str
    start_date: date
    field: Literal["coding", "security", "game", "art"]
    model_name: Literal["xgboost", "prophet", "ensemble"] = "ensemble"


class ClosureRiskResponse(BaseModel):
    risk_score: float
    risk_level: Literal["high", "medium", "low"]
    contributing_factors: list[str]
    recommendation: str
    predicted_enrollment: int | None = None
    min_enrollment: int | None = None
    risk_trend: list[float] | None = None
