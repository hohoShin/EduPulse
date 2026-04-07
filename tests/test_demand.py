"""수요 예측 및 관련 API 테스트. FakeForecaster 사용 — 모델 파일 불필요."""
from edupulse.api.dependencies import MODEL_REGISTRY


def test_predict_with_model_selection(client):
    """model_name 파라미터로 모델을 선택할 수 있어야 한다 (xgboost, prophet, ensemble)."""
    from tests.conftest import FakeForecaster

    MODEL_REGISTRY["prophet"] = FakeForecaster()
    MODEL_REGISTRY["ensemble"] = FakeForecaster()

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


def test_predict_demand_no_model(client_no_model):
    """모델 미로딩 상태에서 503을 반환해야 한다."""
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
