"""수요 예측 API 라우터."""
from datetime import datetime

from fastapi import APIRouter

from edupulse.api.dependencies import get_model
from edupulse.api.schemas.demand import ConfidenceInterval, DemandRequest, DemandResponse
from edupulse.model.predict import _build_features

router = APIRouter()


@router.post("/demand/predict", response_model=DemandResponse)
def predict_demand(request: DemandRequest):
    """수요 예측 엔드포인트.

    request.model_name으로 모델을 선택한다 (기본값: 'ensemble').
    선택한 모델이 미로딩 상태이면 503을 반환한다.
    """
    model = get_model(request.model_name)
    features = _build_features(request.course_name, str(request.start_date), request.field)
    result = model.predict(features)

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
        prediction_date=datetime.utcnow(),
    )
