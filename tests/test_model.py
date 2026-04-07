"""모델 관련 테스트."""
import pandas as pd
import pytest

from edupulse.constants import DemandTier, classify_demand, DEMAND_THRESHOLDS
from edupulse.model.base import PredictionResult
from edupulse.model.xgboost_model import XGBoostForecaster
from edupulse.preprocessing.transformer import add_lag_features

try:
    from prophet import Prophet  # noqa: F401
    _PROPHET_AVAILABLE = True
except ImportError:
    _PROPHET_AVAILABLE = False

try:
    import torch  # noqa: F401
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


def _make_training_df(n=30):
    """테스트용 학습 데이터 DataFrame 생성 (lag feature 포함)."""
    import numpy as np
    rng = np.random.default_rng(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="2W")
    counts = rng.integers(5, 35, size=n).tolist()
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "enrollment_count": counts,
        "search_volume": [c * 1.5 for c in counts],
        "job_count": [c * 2.0 for c in counts],
    })
    df = add_lag_features(df, target_col="enrollment_count")
    return df


def test_xgboost_train_predict():
    """XGBoost 학습 후 predict()가 유효한 PredictionResult를 반환해야 한다."""
    df = _make_training_df(n=30)
    model = XGBoostForecaster()
    model.train(df)

    sample = df.iloc[[-1]]
    result = model.predict(sample)

    assert isinstance(result, PredictionResult)
    assert result.predicted_enrollment >= 0
    assert result.demand_tier in list(DemandTier)
    assert result.model_used == "xgboost"
    assert result.confidence_lower <= result.confidence_upper


def test_classify_demand_thresholds():
    """classify_demand()가 임계값에 따라 정확한 등급을 반환해야 한다."""
    high_threshold = DEMAND_THRESHOLDS["high"]
    mid_threshold = DEMAND_THRESHOLDS["mid"]

    # 경계값 테스트
    assert classify_demand(high_threshold) == DemandTier.HIGH
    assert classify_demand(high_threshold + 1) == DemandTier.HIGH
    assert classify_demand(high_threshold - 1) == DemandTier.MID
    assert classify_demand(mid_threshold) == DemandTier.MID
    assert classify_demand(mid_threshold - 1) == DemandTier.LOW
    assert classify_demand(0) == DemandTier.LOW


def test_prediction_result_structure():
    """PredictionResult 데이터클래스 필드가 올바르게 설정되어야 한다."""
    result = PredictionResult(
        predicted_enrollment=20,
        demand_tier=DemandTier.MID,
        confidence_lower=15.0,
        confidence_upper=25.0,
        model_used="xgboost",
        mape=12.5,
    )

    assert result.predicted_enrollment == 20
    assert result.demand_tier == DemandTier.MID
    assert result.confidence_lower == 15.0
    assert result.confidence_upper == 25.0
    assert result.model_used == "xgboost"
    assert result.mape == 12.5


@pytest.mark.skipif(not _PROPHET_AVAILABLE, reason="prophet 미설치")
def test_prophet_train_predict():
    """Prophet 학습 후 predict()가 유효한 PredictionResult를 반환해야 한다."""
    from edupulse.model.prophet_model import ProphetForecaster

    df = _make_training_df(n=40)
    model = ProphetForecaster()
    model.train(df)

    sample = df.iloc[[-1]].copy()
    result = model.predict(sample)

    assert isinstance(result, PredictionResult)
    assert result.predicted_enrollment >= 0
    assert result.demand_tier in list(DemandTier)
    assert result.model_used == "prophet"
    assert result.confidence_lower <= result.confidence_upper


@pytest.mark.skipif(not _TORCH_AVAILABLE, reason="torch 미설치")
def test_lstm_train_predict():
    """LSTM 학습 후 predict()가 유효한 PredictionResult를 반환해야 한다."""
    from edupulse.model.lstm_model import LSTMForecaster

    df = _make_training_df(n=30)
    model = LSTMForecaster()
    model.train(df, epochs=5)

    sample = df.iloc[[-1]].copy()
    result = model.predict(sample)

    assert isinstance(result, PredictionResult)
    assert result.predicted_enrollment >= 0
    assert result.demand_tier in list(DemandTier)
    assert result.model_used == "lstm"
    assert result.confidence_lower <= result.confidence_upper


def test_ensemble_predict():
    """앙상블이 XGBoost 단독으로도 유효한 PredictionResult를 반환해야 한다 (1개 모델 fallback)."""
    from edupulse.model.ensemble import EnsembleForecaster

    df = _make_training_df(n=30)
    xgb = XGBoostForecaster()
    xgb.train(df)

    ensemble = EnsembleForecaster()
    ensemble.add_model("xgboost", xgb)

    sample = df.iloc[[-1]].copy()
    result = ensemble.predict(sample)

    assert isinstance(result, PredictionResult)
    assert result.predicted_enrollment >= 0
    assert result.demand_tier in list(DemandTier)
    assert "xgboost" in result.model_used
    assert result.confidence_lower <= result.confidence_upper


def test_model_comparison():
    """XGBoost, Prophet(설치 시), LSTM(설치 시) MAPE를 비교하고 30% 초과 시 경고를 출력한다."""
    import math

    df = _make_training_df(n=40)
    results: dict[str, float] = {}

    # XGBoost (항상)
    xgb = XGBoostForecaster()
    xgb_eval = xgb.evaluate(df, n_splits=3)
    results["xgboost"] = xgb_eval["mape"]

    # Prophet (선택)
    if _PROPHET_AVAILABLE:
        from edupulse.model.prophet_model import ProphetForecaster
        proph = ProphetForecaster()
        proph_eval = proph.evaluate(df, n_splits=3)
        results["prophet"] = proph_eval["mape"]

    # LSTM (선택)
    if _TORCH_AVAILABLE:
        from edupulse.model.lstm_model import LSTMForecaster
        lstm = LSTMForecaster()
        lstm_eval = lstm.evaluate(df, n_splits=3)
        results["lstm"] = lstm_eval["mape"]

    # 결과 출력 및 검증
    print("\n모델 MAPE 비교:")
    for name, mape in results.items():
        flag = " *** MAPE > 30% ***" if (not math.isnan(mape) and mape > 30) else ""
        print(f"  {name:<12}: {mape:.2f}%{flag}")

    # 최소 XGBoost 결과는 있어야 함
    assert "xgboost" in results
    assert not math.isnan(results["xgboost"])
