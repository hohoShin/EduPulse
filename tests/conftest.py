"""pytest fixtures. FakeForecaster mock 포함."""
import pytest
from fastapi.testclient import TestClient

from edupulse.api.main import app
from edupulse.model.predict import _model_cache, _model_mtime, MODEL_VERSION
from edupulse.constants import DemandTier
from edupulse.model.base import BaseForecaster, PredictionResult

import pandas as pd


class FakeForecaster(BaseForecaster):
    """테스트용 가짜 모델. 모델 파일 불필요, 결정론적 결과."""

    def __init__(
        self,
        enrollment: int = 20,
        tier: DemandTier = DemandTier.MID,
        lower: float = 15.0,
        upper: float = 25.0,
    ) -> None:
        super().__init__()
        self._enrollment = enrollment
        self._tier = tier
        self._lower = lower
        self._upper = upper

    def train(self, df: pd.DataFrame) -> None:
        pass

    def _predict(self, features: pd.DataFrame) -> PredictionResult:
        return PredictionResult(
            predicted_enrollment=self._enrollment,
            demand_tier=self._tier,
            confidence_lower=self._lower,
            confidence_upper=self._upper,
            model_used="fake",
            mape=None,
        )

    def evaluate(self, df: pd.DataFrame, n_splits: int = 5) -> dict:
        return {"mape": 0.1}

    def save(self, path: str, version: int) -> None:
        pass

    def load(self, path: str, version: int) -> None:
        pass


@pytest.fixture
def make_fake_forecaster():
    """FakeForecaster 팩토리 픽스처. 파라미터를 커스터마이즈 가능."""
    def _factory(
        enrollment: int = 20,
        tier: DemandTier = DemandTier.MID,
        lower: float = 15.0,
        upper: float = 25.0,
    ) -> FakeForecaster:
        return FakeForecaster(enrollment=enrollment, tier=tier, lower=lower, upper=upper)
    return _factory


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
    xgboost, ensemble 키를 모두 교체하여 실제 모델이 호출되지 않도록 한다.
    _model_mtime도 함께 설정하여 mtime 기반 리로딩이 발생하지 않도록 한다.
    """
    with TestClient(app) as c:
        for model_name in ("xgboost", "ensemble"):
            key = f"{model_name}_v{MODEL_VERSION}"
            _model_cache[key] = FakeForecaster()
            _model_mtime[key] = float("inf")  # mtime 리로딩 방지
        yield c
    _model_cache.clear()
    _model_mtime.clear()


@pytest.fixture
def client_no_model():
    """모델 미로딩 상태 TestClient (503 테스트용).

    lifespan이 load_models()를 호출하므로, TestClient 시작 후 registry를 clear한다.
    """
    with TestClient(app) as c:
        _model_cache.clear()  # lifespan 완료 후 클리어
        _model_mtime.clear()
        yield c
    _model_cache.clear()
    _model_mtime.clear()
