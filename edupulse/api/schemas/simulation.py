"""시뮬레이션 API 요청/응답 스키마."""
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, model_validator

from edupulse.constants import DemandTier


class StartDateCandidate(BaseModel):
    date: date
    predicted_enrollment: int
    demand_tier: DemandTier
    composite_score: float


class OptimalStartRequest(BaseModel):
    course_name: str
    field: Literal["coding", "security", "game", "art"]
    search_window_start: date
    search_window_end: date

    @model_validator(mode="after")
    def check_window_max_16_weeks(self) -> "OptimalStartRequest":
        """검색 윈도우는 최대 16주(112일)로 제한한다."""
        delta = (self.search_window_end - self.search_window_start).days
        if delta > 112:
            raise ValueError("search_window_end - search_window_start 는 최대 16주(112일)입니다.")
        return self


class OptimalStartResponse(BaseModel):
    top_candidates: list[StartDateCandidate]


class SimulateRequest(BaseModel):
    course_name: str
    field: Literal["coding", "security", "game", "art"]
    start_date: date
    price_per_student: float = 500000.0


class ScenarioResult(BaseModel):
    scenario: str
    predicted_enrollment: int
    demand_tier: DemandTier
    estimated_revenue: float


class MarketContext(BaseModel):
    competitor_openings: int
    competitor_avg_price: float
    search_volume_trend: list[float]


class SimulateResponse(BaseModel):
    baseline: ScenarioResult
    optimistic: ScenarioResult
    pessimistic: ScenarioResult
    market_context: Optional[MarketContext] = None


class DemographicsRequest(BaseModel):
    field: Literal["coding", "security", "game", "art"]


class AgeGroup(BaseModel):
    group: str
    ratio: float


class PurposeGroup(BaseModel):
    purpose: str
    ratio: float


class DemographicsResponse(BaseModel):
    field: str
    age_distribution: list[AgeGroup]
    purpose_distribution: list[PurposeGroup]
    trend: str


class TrendMetric(BaseModel):
    current: float
    average: float
    trend_direction: Literal["up", "down", "stable"]


class CompetitorRequest(BaseModel):
    field: Literal["coding", "security", "game", "art"]


class CompetitorResponse(BaseModel):
    field: str
    competitor_openings: int
    competitor_avg_price: float
    saturation_index: float
    recommendation: str
