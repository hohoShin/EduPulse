"""수요 예측 API 라우터."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from edupulse.api.schemas.demand import (
    ClosureRiskRequest,
    ClosureRiskResponse,
    ConfidenceInterval,
    DemandRequest,
    DemandResponse,
)
from edupulse.constants import DemandTier
from edupulse.model.predict import predict_demand as _predict_demand

router = APIRouter()

# 최소 개강 인원 기준 (폐강 위험 계산용, 과정 단위)
_MIN_ENROLLMENT = 15


@router.post("/demand/predict", response_model=DemandResponse)
def predict_demand(request: DemandRequest):
    """수요 예측 엔드포인트.

    request.model_name으로 모델을 선택한다 (기본값: 'ensemble').
    predict_demand()를 직접 호출하여 스케일 보정이 적용된 결과를 반환한다.
    """
    try:
        result = _predict_demand(
            request.course_name, str(request.start_date), request.field,
            model_name=request.model_name,
        )
    except Exception:
        raise HTTPException(status_code=503, detail=f"Model '{request.model_name}' not loaded")

    return DemandResponse(
        course_name=request.course_name,
        field=request.field,
        predicted_enrollment=result.predicted_enrollment,
        demand_tier=result.demand_tier,
        confidence_interval=ConfidenceInterval(
            lower=result.confidence_lower,
            upper=result.confidence_upper,
        ),
        model_used=result.model_used,
        prediction_date=datetime.now(timezone.utc),
    )


@router.post("/demand/closure-risk", response_model=ClosureRiskResponse)
def assess_closure_risk(request: ClosureRiskRequest) -> ClosureRiskResponse:
    """폐강 위험도 평가 엔드포인트.

    예측 수강생 수와 신뢰 구간 하한을 기반으로 폐강 위험도(high/medium/low)를 계산한다.
    - high: 신뢰 구간 하한이 최소 개강 인원 미만이거나 LOW 티어
    - medium: MID 티어 또는 신뢰 구간 하한이 경계 수준
    - low: HIGH 티어이고 신뢰 구간 하한이 충분
    """
    result = _predict_demand(
        request.course_name, str(request.start_date), request.field,
        model_name=request.model_name,
    )

    enrollment = result.predicted_enrollment
    lower = result.confidence_lower
    tier = result.demand_tier

    factors: list[str] = []
    if tier == DemandTier.LOW:
        factors.append(f"예측 수강생 수 부족: {enrollment}명 (LOW 등급)")
    if lower < _MIN_ENROLLMENT:
        factors.append(f"신뢰 구간 하한({lower:.1f}명)이 최소 개강 인원({_MIN_ENROLLMENT}명) 미만")

    # 위험 등급: 수요 티어를 기준으로 결정 (신뢰 구간 하한은 보조 지표)
    if tier == DemandTier.LOW:
        risk_level: str = "high"
        risk_score = max(0.0, 1.0 - enrollment / (_MIN_ENROLLMENT * 2))
        recommendation = "마케팅 강화 및 조기 등록 할인 적용을 권장합니다. 개강 4주 전까지 최소 인원 미달 시 폐강을 검토하세요."
    elif tier == DemandTier.MID:
        risk_level = "medium"
        risk_score = 0.4
        factors.append(f"예측 수강생 수: {enrollment}명 (MID 등급) — 추가 모집 권장")
        recommendation = "조기 등록 혜택 제공으로 수강생 확보를 권장합니다. 개강 2주 전 재평가 예정."
    else:
        risk_level = "low"
        risk_score = 0.1
        factors.append(f"예측 수강생 수: {enrollment}명 (HIGH 등급) — 안정적 개강 예상")
        recommendation = "현재 마케팅 전략을 유지하세요. 개강 준비에 집중하시기 바랍니다."

    score = round(risk_score, 4)
    risk_trend = [round(score * f, 2) for f in [0.85, 0.88, 0.91, 0.93, 0.95, 0.97, 0.99, 1.0]]

    return ClosureRiskResponse(
        risk_score=score,
        risk_level=risk_level,
        contributing_factors=factors,
        recommendation=recommendation,
        predicted_enrollment=enrollment,
        min_enrollment=_MIN_ENROLLMENT,
        risk_trend=risk_trend,
    )
