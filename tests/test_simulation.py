"""시뮬레이션 API 테스트 — FakeForecaster 사용, 모델 파일 불필요."""
from edupulse.model.predict import _model_cache, _model_mtime, MODEL_VERSION


def test_optimal_start(client):
    """검색 윈도우 내 최적 개강일 후보를 최대 5개 반환해야 한다."""
    response = client.post(
        "/api/v1/simulation/optimal-start",
        json={
            "course_name": "Python 웹개발",
            "field": "coding",
            "search_window_start": "2026-05-01",
            "search_window_end": "2026-06-30",
        },
    )
    assert response.status_code == 200, f"optimal-start 실패: {response.text}"
    data = response.json()
    assert "top_candidates" in data
    assert isinstance(data["top_candidates"], list)
    assert len(data["top_candidates"]) <= 5
    for candidate in data["top_candidates"]:
        assert "date" in candidate
        assert "predicted_enrollment" in candidate
        assert "demand_tier" in candidate
        assert candidate["demand_tier"] in ("High", "Mid", "Low")
        assert "composite_score" in candidate


def test_optimal_start_window_too_long(client):
    """검색 윈도우가 16주(112일) 초과 시 422를 반환해야 한다."""
    response = client.post(
        "/api/v1/simulation/optimal-start",
        json={
            "course_name": "Python 웹개발",
            "field": "coding",
            "search_window_start": "2026-01-01",
            "search_window_end": "2026-12-31",  # 364일 > 112일
        },
    )
    assert response.status_code == 422, f"윈도우 초과 검증 실패: {response.text}"


def test_simulate(client):
    """신규 과정 시뮬레이션이 기준/낙관/비관 세 시나리오를 반환해야 한다."""
    response = client.post(
        "/api/v1/simulation/simulate",
        json={
            "course_name": "Python 웹개발",
            "field": "coding",
            "start_date": "2026-05-01",
            "price_per_student": 500000.0,
        },
    )
    assert response.status_code == 200, f"simulate 실패: {response.text}"
    data = response.json()
    assert "baseline" in data
    assert "optimistic" in data
    assert "pessimistic" in data
    for key in ("baseline", "optimistic", "pessimistic"):
        scenario = data[key]
        assert "scenario" in scenario
        assert "predicted_enrollment" in scenario
        assert "demand_tier" in scenario
        assert scenario["demand_tier"] in ("High", "Mid", "Low")
        assert "estimated_revenue" in scenario


def test_demographics(client):
    """분야별 수강생 인구통계 분석이 200과 올바른 구조를 반환해야 한다."""
    response = client.post(
        "/api/v1/simulation/demographics",
        json={"field": "coding"},
    )
    assert response.status_code == 200, f"demographics 실패: {response.text}"
    data = response.json()
    assert data["field"] == "coding"
    assert "age_distribution" in data
    assert isinstance(data["age_distribution"], list)
    assert "purpose_distribution" in data
    assert isinstance(data["purpose_distribution"], list)
    assert "trend" in data


def test_competitors(client):
    """분야별 경쟁사 현황 분석이 200과 올바른 구조를 반환해야 한다."""
    response = client.post(
        "/api/v1/simulation/competitors",
        json={"field": "coding"},
    )
    assert response.status_code == 200, f"competitors 실패: {response.text}"
    data = response.json()
    assert data["field"] == "coding"
    assert "competitor_openings" in data
    assert "competitor_avg_price" in data
    assert "saturation_index" in data
    assert "recommendation" in data
    assert isinstance(data["recommendation"], str)
