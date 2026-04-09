"""pytest fixtures. FakeForecaster mock 포함."""
import pytest
from fastapi.testclient import TestClient

from edupulse.api.main import app
from edupulse.model.predict import _model_cache, MODEL_VERSION
from edupulse.constants import DemandTier
from edupulse.model.base import BaseForecaster, PredictionResult

import pandas as pd


class FakeForecaster(BaseForecaster):
    """테스트용 가짜 모델. 모델 파일 불필요, 결정론적 결과."""

    def train(self, df: pd.DataFrame) -> None:
        pass

    def _predict(self, features: pd.DataFrame) -> PredictionResult:
        return PredictionResult(
            predicted_enrollment=20,
            demand_tier=DemandTier.MID,
            confidence_lower=15.0,
            confidence_upper=25.0,
            model_used="fake",
            mape=None,
        )

    def evaluate(self, df: pd.DataFrame, n_splits: int = 5) -> dict:
        return {"mape": 0.1}

    def save(self, path: str, version: int) -> None:
        pass

    def load(self, path: str, version: int) -> None:
        pass


@pytest.fixture(autouse=True)
def _force_cpu(monkeypatch):
    """LSTM 테스트 시 MPS 대신 CPU 사용을 강제한다."""
    try:
        import torch
        cpu = lambda: torch.device("cpu")
        monkeypatch.setattr("edupulse.model.utils.get_device", cpu)
        monkeypatch.setattr("edupulse.model.lstm_model.get_device", cpu)
    except ImportError:
        pass


@pytest.fixture
def client():
    """FakeForecaster가 로딩된 TestClient.

    lifespan이 load_models()를 호출하므로, TestClient 시작 후 FakeForecaster로 교체한다.
    """
    with TestClient(app) as c:
        _model_cache[f"xgboost_v{MODEL_VERSION}"] = FakeForecaster()
        yield c
    _model_cache.clear()


@pytest.fixture
def client_no_model():
    """모델 미로딩 상태 TestClient (503 테스트용).

    lifespan이 load_models()를 호출하므로, TestClient 시작 후 registry를 clear한다.
    """
    with TestClient(app) as c:
        _model_cache.clear()  # lifespan 완료 후 클리어
        yield c
    _model_cache.clear()
