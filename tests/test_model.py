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


def _make_training_df(n=100):
    """테스트용 학습 데이터 DataFrame 생성 (lag feature 포함)."""
    import numpy as np
    rng = np.random.default_rng(42)
    dates = pd.date_range("2021-01-04", periods=n, freq="W-MON")
    counts = rng.integers(1, 10, size=n).tolist()
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "field": ["coding"] * n,
        "enrollment_count": counts,
        "search_volume": [c * 1.5 for c in counts],
        "job_count": [c * 2.0 for c in counts],
        "consultation_count": rng.integers(0, 30, size=n).tolist(),
        "conversion_rate": rng.uniform(0.05, 0.65, size=n).tolist(),
        "page_views": rng.integers(10, 200, size=n).tolist(),
        "cart_abandon_rate": rng.uniform(0.2, 0.95, size=n).tolist(),
        "age_group_diversity": rng.uniform(0.5, 1.1, size=n).tolist(),
        "has_cert_exam": rng.choice([0, 1], size=n).tolist(),
        "weeks_to_exam": rng.integers(0, 27, size=n).tolist(),
        "competitor_openings": rng.integers(0, 15, size=n).tolist(),
        "competitor_avg_price": rng.integers(300000, 800000, size=n).tolist(),
        "is_vacation": rng.choice([0, 1], size=n).tolist(),
        "is_exam_season": rng.choice([0, 1], size=n).tolist(),
        "is_semester_start": rng.choice([0, 1], size=n).tolist(),
    })
    df = add_lag_features(df, target_col="enrollment_count")
    return df


def test_xgboost_train_predict():
    """XGBoost 학습 후 predict()가 유효한 PredictionResult를 반환해야 한다."""
    df = _make_training_df(n=100)
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

    df = _make_training_df(n=100)
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

    df = _make_training_df(n=100)
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

    df = _make_training_df(n=100)
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

    df = _make_training_df(n=100)
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


def test_augment_sequences():
    """_augment_sequences가 feature-aware하게 동작하는지 검증한다."""
    if not _TORCH_AVAILABLE:
        pytest.skip("PyTorch 미설치")

    import numpy as np
    from edupulse.model.lstm_model import (
        _augment_sequences, AUGMENTABLE_FEATURES, PROTECTED_FEATURES,
    )
    from edupulse.model.xgboost_model import FEATURE_COLUMNS

    rng = np.random.default_rng(0)
    n_seq, seq_len, n_feat = 20, 12, len(FEATURE_COLUMNS)
    xs = rng.random((n_seq, seq_len, n_feat)).astype(np.float32)
    ys = rng.random(n_seq).astype(np.float32)

    aug_xs, aug_ys = _augment_sequences(xs, ys, n_augments=2, seed=99)

    # 출력 크기: 원본 + 2 증강 = 3배
    assert aug_xs.shape == (n_seq * 3, seq_len, n_feat)
    assert aug_ys.shape == (n_seq * 3,)

    # 원본은 그대로 보존
    np.testing.assert_array_equal(aug_xs[:n_seq], xs)
    np.testing.assert_array_equal(aug_ys[:n_seq], ys)

    # Protected features (month_sin, month_cos, field_encoded)는 불변
    for i in range(1, 3):  # 증강 복사본 1, 2
        start = i * n_seq
        end = start + n_seq
        for feat_idx in PROTECTED_FEATURES:
            np.testing.assert_array_equal(
                aug_xs[start:end, :, feat_idx],
                xs[:, :, feat_idx],
                err_msg=f"Protected feature {feat_idx} was modified in augment {i}",
            )

    # Augmentable features는 변형됨
    for i in range(1, 3):
        start = i * n_seq
        end = start + n_seq
        diff = np.abs(aug_xs[start:end, :, AUGMENTABLE_FEATURES] - xs[:, :, AUGMENTABLE_FEATURES])
        assert diff.sum() > 0, f"Augmentable features unchanged in augment {i}"

    # 동일 seed → 동일 결과 (결정론적)
    aug_xs2, aug_ys2 = _augment_sequences(xs, ys, n_augments=2, seed=99)
    np.testing.assert_array_equal(aug_xs, aug_xs2)
    np.testing.assert_array_equal(aug_ys, aug_ys2)
