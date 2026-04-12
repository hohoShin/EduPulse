"""수요 예측 및 관련 API 테스트. FakeForecaster 사용 — 모델 파일 불필요."""
from edupulse.constants import DemandTier
from edupulse.model.predict import _model_cache, _model_mtime, MODEL_VERSION


def test_predict_with_model_selection(client):
    """model_name 파라미터로 모델을 선택할 수 있어야 한다 (xgboost, prophet, ensemble)."""
    from tests.conftest import FakeForecaster

    for model_name in ("prophet", "ensemble"):
        key = f"{model_name}_v{MODEL_VERSION}"
        _model_cache[key] = FakeForecaster()
        _model_mtime[key] = float("inf")  # mtime 리로딩 방지

    for model_name in ("xgboost", "prophet", "ensemble"):
        response = client.post(
            "/api/v1/demand/predict",
            json={
                "course_name": "Python 웹개발",
                "start_date": "2026-05-01",
                "field": "coding",
                "model_name": model_name,
            },
        )
        assert response.status_code == 200, f"{model_name} 선택 실패: {response.text}"
        data = response.json()
        assert data["demand_tier"] in ("High", "Mid", "Low")


def test_predict_demand_success(client):
    """정상 요청 시 200과 DemandResponse 구조를 반환해야 한다."""
    response = client.post(
        "/api/v1/demand/predict",
        json={"course_name": "Python 웹개발", "start_date": "2026-05-01", "field": "coding"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["course_name"] == "Python 웹개발"
    assert data["field"] == "coding"
    assert "predicted_enrollment" in data
    assert "demand_tier" in data
    assert data["demand_tier"] in ("High", "Mid", "Low")
    assert "confidence_interval" in data
    assert "lower" in data["confidence_interval"]
    assert "upper" in data["confidence_interval"]
    assert "model_used" in data
    assert "prediction_date" in data


def test_predict_demand_no_model(client_no_model, monkeypatch):
    """모델 미로딩 상태에서 503을 반환해야 한다."""
    # 캐시가 비어 있고 디스크 로딩도 실패하도록 패치
    def _always_fail(name, version=1):
        raise RuntimeError(f"테스트: 모델 '{name}' 로딩 불가")

    monkeypatch.setattr("edupulse.model.predict.load_model", _always_fail)

    response = client_no_model.post(
        "/api/v1/demand/predict",
        json={"course_name": "Python 웹개발", "start_date": "2026-05-01", "field": "coding"},
    )
    assert response.status_code == 503


def test_predict_demand_invalid_field(client):
    """유효하지 않은 field 값에 대해 422를 반환해야 한다."""
    response = client.post(
        "/api/v1/demand/predict",
        json={"course_name": "Python 웹개발", "start_date": "2026-05-01", "field": "invalid"},
    )
    assert response.status_code == 422


def test_schedule_suggest(client):
    """스케줄 제안 API가 강사 수와 강의실 수를 올바르게 계산해야 한다."""
    response = client.post(
        "/api/v1/schedule/suggest",
        json={"course_name": "Python 웹개발", "start_date": "2026-05-01", "predicted_enrollment": 30},
    )
    assert response.status_code == 200
    data = response.json()
    # 30명: 강사 = ceil(30/15) = 2, 강의실 = ceil(30/30) = 1
    assert data["required_instructors"] == 2
    assert data["required_classrooms"] == 1


def test_marketing_timing_high(client):
    """High 수요 등급에 대해 2주 전 광고를 제안해야 한다."""
    response = client.post(
        "/api/v1/marketing/timing",
        json={"course_name": "Python 웹개발", "start_date": "2026-05-01", "demand_tier": "High"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ad_launch_weeks_before"] == 2
    assert data["earlybird_duration_days"] == 7
    assert data["discount_rate"] == 0.05


def test_marketing_timing_low(client):
    """Low 수요 등급에 대해 4주 전 광고를 제안해야 한다."""
    response = client.post(
        "/api/v1/marketing/timing",
        json={"course_name": "Python 웹개발", "start_date": "2026-05-01", "demand_tier": "Low"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ad_launch_weeks_before"] == 4
    assert data["earlybird_duration_days"] == 21
    assert data["discount_rate"] == 0.15


def test_closure_risk_high(client, make_fake_forecaster):
    """예측 수강생이 매우 적을 때(LOW tier) 폐강 위험도가 'high'여야 한다."""
    from tests.conftest import FakeForecaster
    fake = make_fake_forecaster(enrollment=2, tier=DemandTier.LOW, lower=1.0, upper=3.0)
    _model_cache[f"xgboost_v{MODEL_VERSION}"] = fake
    _model_cache[f"ensemble_v{MODEL_VERSION}"] = fake
    _model_mtime[f"xgboost_v{MODEL_VERSION}"] = float("inf")
    _model_mtime[f"ensemble_v{MODEL_VERSION}"] = float("inf")

    response = client.post(
        "/api/v1/demand/closure-risk",
        json={"course_name": "Python 웹개발", "start_date": "2026-05-01", "field": "coding"},
    )
    assert response.status_code == 200, f"closure-risk 실패: {response.text}"
    data = response.json()
    assert data["risk_level"] == "high"
    assert "risk_score" in data
    assert "contributing_factors" in data
    assert "recommendation" in data


def test_closure_risk_mid(client, make_fake_forecaster):
    """예측 수강생이 중간(MID tier)일 때 폐강 위험도가 'medium'이어야 한다."""
    from tests.conftest import FakeForecaster
    fake = make_fake_forecaster(enrollment=3, tier=DemandTier.MID, lower=2.0, upper=5.0)
    _model_cache[f"xgboost_v{MODEL_VERSION}"] = fake
    _model_cache[f"ensemble_v{MODEL_VERSION}"] = fake
    _model_mtime[f"xgboost_v{MODEL_VERSION}"] = float("inf")
    _model_mtime[f"ensemble_v{MODEL_VERSION}"] = float("inf")

    response = client.post(
        "/api/v1/demand/closure-risk",
        json={"course_name": "Python 웹개발", "start_date": "2026-05-01", "field": "coding"},
    )
    assert response.status_code == 200, f"closure-risk 실패: {response.text}"
    data = response.json()
    assert data["risk_level"] == "medium"


def test_closure_risk_low(client, make_fake_forecaster):
    """예측 수강생이 충분(HIGH tier)할 때 폐강 위험도가 'low'여야 한다."""
    from tests.conftest import FakeForecaster
    fake = make_fake_forecaster(enrollment=10, tier=DemandTier.HIGH, lower=8.0, upper=12.0)
    _model_cache[f"xgboost_v{MODEL_VERSION}"] = fake
    _model_cache[f"ensemble_v{MODEL_VERSION}"] = fake
    _model_mtime[f"xgboost_v{MODEL_VERSION}"] = float("inf")
    _model_mtime[f"ensemble_v{MODEL_VERSION}"] = float("inf")

    response = client.post(
        "/api/v1/demand/closure-risk",
        json={"course_name": "Python 웹개발", "start_date": "2026-05-01", "field": "coding"},
    )
    assert response.status_code == 200, f"closure-risk 실패: {response.text}"
    data = response.json()
    assert data["risk_level"] == "low"


def test_lead_conversion(client):
    """마케팅 lead-conversion 엔드포인트가 200과 올바른 구조를 반환해야 한다."""
    response = client.post(
        "/api/v1/marketing/lead-conversion",
        json={"field": "coding"},
    )
    assert response.status_code == 200, f"lead-conversion 실패: {response.text}"
    data = response.json()
    assert data["field"] == "coding"
    assert "estimated_conversions" in data
    assert "consultation_count_trend" in data
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)


def test_schedule_assignment_plan(client):
    """스케줄 제안 API의 응답에 assignment_plan 필드가 존재해야 한다 (None 허용)."""
    response = client.post(
        "/api/v1/schedule/suggest",
        json={"course_name": "Python 웹개발", "start_date": "2026-05-01", "predicted_enrollment": 30},
    )
    assert response.status_code == 200
    data = response.json()
    assert "assignment_plan" in data
    # assignment_plan은 None이거나 classes+summary 구조여야 한다
    if data["assignment_plan"] is not None:
        assert "classes" in data["assignment_plan"]
        assert "summary" in data["assignment_plan"]
