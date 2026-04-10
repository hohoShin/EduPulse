"""마케팅 타이밍 API 라우터 (rule-based MVP)."""
from fastapi import APIRouter

from edupulse.api.schemas.marketing import (
    LeadConversionRequest,
    LeadConversionResponse,
    MarketingRequest,
    MarketingResponse,
)
from edupulse.api.services import marketing_service
from edupulse.constants import DemandTier

router = APIRouter()

# 수요 등급별 마케팅 타이밍 규칙
_MARKETING_RULES = {
    DemandTier.HIGH: {"weeks_before": 2, "earlybird_days": 7, "discount_rate": 0.05},
    DemandTier.MID:  {"weeks_before": 3, "earlybird_days": 14, "discount_rate": 0.10},
    DemandTier.LOW:  {"weeks_before": 4, "earlybird_days": 21, "discount_rate": 0.15},
}


@router.post("/marketing/timing", response_model=MarketingResponse)
def suggest_marketing_timing(request: MarketingRequest):
    """수요 등급에 따른 광고 타이밍 및 할인율 제안."""
    rule = _MARKETING_RULES[request.demand_tier]

    return MarketingResponse(
        course_name=request.course_name,
        demand_tier=request.demand_tier,
        ad_launch_weeks_before=rule["weeks_before"],
        earlybird_duration_days=rule["earlybird_days"],
        discount_rate=rule["discount_rate"],
    )


@router.post("/marketing/lead-conversion", response_model=LeadConversionResponse)
def predict_lead_conversion(request: LeadConversionRequest) -> LeadConversionResponse:
    """잠재 수강생 전환 예측.

    상담 로그와 웹 로그를 분석하여 분야별 예상 전환 수강생 수,
    전환율 추세, 상담 건수 추세, 마케팅 권고안을 반환한다.
    """
    result = marketing_service.predict_lead_conversion(field=request.field)
    return LeadConversionResponse(field=request.field, **result)
