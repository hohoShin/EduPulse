"""Health check endpoint 테스트."""


def test_health_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "models_loaded" in data


def test_health_shows_loaded_models(client):
    response = client.get("/api/v1/health")
    data = response.json()
    assert "xgboost" in data["models_loaded"]


def test_health_no_model(client_no_model):
    response = client_no_model.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["models_loaded"] == []
