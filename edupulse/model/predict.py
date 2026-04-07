"""수요 예측 진입점 — API에서 호출.

Usage:
    from edupulse.model.predict import predict_demand
    result = predict_demand('Python 웹개발', '2026-05-01', 'coding')
    result = predict_demand('Python 웹개발', '2026-05-01', 'coding', model_name='ensemble')
"""
import math

import pandas as pd

from edupulse.model.base import BaseForecaster, PredictionResult
from edupulse.model.xgboost_model import FEATURE_COLUMNS

# 모듈 레벨 모델 캐시 (직접 로딩 전략 — api.dependencies.MODEL_REGISTRY와 별도)
_model_cache: dict[str, BaseForecaster] = {}


def _load_model(model_name: str, version: int = 1) -> BaseForecaster:
    """모델 캐시에서 반환하거나 새로 로딩.

    Args:
        model_name: 모델 이름 ('xgboost', 'prophet', 'lstm', 'ensemble')
        version: 모델 버전

    Returns:
        로딩된 BaseForecaster 인스턴스
    """
    key = f"{model_name}_v{version}"
    if key not in _model_cache:
        if model_name == "xgboost":
            from edupulse.model.xgboost_model import XGBoostForecaster

            model: BaseForecaster = XGBoostForecaster()
            model.load(f"edupulse/model/saved/xgboost", version=version)

        elif model_name == "prophet":
            try:
                from edupulse.model.prophet_model import ProphetForecaster

                model = ProphetForecaster()
                model.load(f"edupulse/model/saved/prophet", version=version)
            except ImportError as exc:
                raise ImportError("Prophet 미설치. pip install prophet") from exc

        elif model_name == "lstm":
            try:
                from edupulse.model.lstm_model import LSTMForecaster

                model = LSTMForecaster()
                model.load(f"edupulse/model/saved/lstm", version=version)
            except ImportError as exc:
                raise ImportError("PyTorch 미설치. pip install torch") from exc

        elif model_name == "ensemble":
            model = _load_ensemble(version=version)

        else:
            raise ValueError(f"Unknown model_name: {model_name}")

        _model_cache[key] = model

    return _model_cache[key]


def _load_ensemble(version: int = 1) -> "BaseForecaster":
    """가용한 모델을 모두 로딩하여 EnsembleForecaster 반환.

    각 모델 로딩 실패 시 조용히 건너뛴다. 1개 이상 로딩되면 앙상블 반환.

    Args:
        version: 모델 버전

    Returns:
        EnsembleForecaster 인스턴스
    """
    from edupulse.model.ensemble import EnsembleForecaster

    ensemble = EnsembleForecaster()

    # XGBoost (항상 시도)
    try:
        from edupulse.model.xgboost_model import XGBoostForecaster

        xgb = XGBoostForecaster()
        xgb.load("edupulse/model/saved/xgboost", version=version)
        ensemble.add_model("xgboost", xgb)
    except Exception:
        pass

    # Prophet (선택적)
    try:
        from edupulse.model.prophet_model import ProphetForecaster

        prophet = ProphetForecaster()
        prophet.load("edupulse/model/saved/prophet", version=version)
        ensemble.add_model("prophet", prophet)
    except Exception:
        pass

    # LSTM (선택적)
    try:
        from edupulse.model.lstm_model import LSTMForecaster

        lstm = LSTMForecaster()
        lstm.load("edupulse/model/saved/lstm", version=version)
        ensemble.add_model("lstm", lstm)
    except Exception:
        pass

    if ensemble.model_count == 0:
        raise RuntimeError("앙상블 로딩 실패: 사용 가능한 모델이 없습니다.")

    return ensemble


def _build_features(course_name: str, start_date: str, field: str) -> pd.DataFrame:
    """API raw 입력 → feature DataFrame 변환.

    실제 피처 엔지니어링은 Phase 3에서 전처리 모듈과 연동.
    현재는 zero-filled 기본 피처를 반환하여 모델 호출 가능 상태 유지.

    Args:
        course_name: 과정명
        start_date: 시작일 (YYYY-MM-DD)
        field: 분야 ('coding', 'security', 'game', 'art')

    Returns:
        feature_columns에 해당하는 1행 DataFrame
    """
    import datetime

    dt = datetime.date.fromisoformat(start_date)
    month_rad = (dt.month - 1) / 12.0 * 2 * math.pi

    row = {col: 0.0 for col in FEATURE_COLUMNS}
    row["month_sin"] = math.sin(month_rad)
    row["month_cos"] = math.cos(month_rad)

    return pd.DataFrame([row])


def predict_demand(
    course_name: str,
    start_date: str,
    field: str,
    model_name: str = "ensemble",
    version: int = 1,
) -> PredictionResult:
    """API에서 호출하는 수요 예측 진입점.

    1. raw 입력 → feature DataFrame 구성
    2. 모델 로딩 (모듈 레벨 캐시)
    3. model.predict(features) 호출
    4. PredictionResult 반환

    Args:
        course_name: 과정명
        start_date: 시작일 (YYYY-MM-DD)
        field: 분야 ('coding', 'security', 'game', 'art')
        model_name: 사용할 모델 ('xgboost', 'prophet', 'lstm', 'ensemble')
        version: 모델 버전

    Returns:
        PredictionResult
    """
    model = _load_model(model_name, version)
    features = _build_features(course_name, start_date, field)
    return model.predict(features)
