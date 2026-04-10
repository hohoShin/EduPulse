"""마케팅 타이밍 API 요청/응답 스키마."""
from datetime import date
from typing import Literal

from pydantic import BaseModel

from edupulse.constants import DemandTier


class MarketingRequest(BaseModel):
    course_name: str
    start_date: date
    demand_tier: DemandTier


class MarketingResponse(BaseModel):
    course_name: str
    demand_tier: DemandTier
    ad_launch_weeks_before: int
    earlybird_duration_days: int
    discount_rate: float


class LeadConversionRequest(BaseModel):
    field: Literal["coding", "security", "game", "art"]


class LeadConversionResponse(BaseModel):
    field: str
    estimated_conversions: int
    consultation_count_trend: list[float]
    recommendations: list[str]
