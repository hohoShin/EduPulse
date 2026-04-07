"""BaseForecaster ABC + PredictionResult dataclass."""
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from edupulse.constants import DemandTier


@dataclass
class PredictionResult:
    """모델 예측 결과."""

    predicted_enrollment: int
    demand_tier: DemandTier
    confidence_lower: float
    confidence_upper: float
    model_used: str
    mape: float | None


class BaseForecaster(ABC):
    """모든 예측 모델의 추상 기반 클래스."""

    def __init__(self):
        self._lock = threading.Lock()

    @abstractmethod
    def train(self, df: pd.DataFrame) -> None:
        """모델 학습."""
        ...

    @abstractmethod
    def _predict(self, features: pd.DataFrame) -> PredictionResult:
        """내부 예측 로직 (Lock 없이 호출)."""
        ...

    def predict(self, features: pd.DataFrame) -> PredictionResult:
        """스레드 안전 예측. 동시 요청에서 내부 상태 충돌 방지."""
        with self._lock:
            return self._predict(features)

    @abstractmethod
    def evaluate(self, df: pd.DataFrame, n_splits: int = 5) -> dict:
        """시계열 K-Fold 교차검증. MAPE 반환."""
        ...

    def save(self, path: str, version: int) -> None:
        """모델 저장. 하위 클래스에서 오버라이드."""
        ...

    def load(self, path: str, version: int) -> None:
        """모델 로딩. 하위 클래스에서 오버라이드."""
        ...
