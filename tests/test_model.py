"""모델 관련 테스트."""
import pandas as pd
import pytest

from edupulse.constants import DemandTier, classify_demand, DEMAND_THRESHOLDS
from edupulse.model.base import ModelMetadata, PredictionResult, load_metadata, save_metadata
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

    rng = np.random.default_rng(0)
    n_seq, seq_len, n_feat = 20, 12, 10
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


def test_xgboost_save_metadata(tmp_path):
    """XGBoost save(df=...)가 metadata.json을 올바르게 생성해야 한다."""
    import json

    df = _make_training_df(n=100)
    model = XGBoostForecaster()
    model.train(df)

    save_dir = str(tmp_path / "xgboost")
    model.save(save_dir, version=1, df=df)

    meta_path = tmp_path / "xgboost" / "v1" / "metadata.json"
    assert meta_path.exists(), "metadata.json이 생성되지 않았습니다"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["model_name"] == "xgboost"
    assert meta["version"] == 1
    assert meta["data_rows"] == 100
    assert "trained_at" in meta
    assert isinstance(meta["feature_columns"], list)
    assert len(meta["feature_columns"]) > 0
    assert isinstance(meta["hyperparameters"], dict)
    assert meta["hyperparameters"]["n_estimators"] == 300
    assert "coding" in meta["fields"]
    assert meta["python_version"]
    assert isinstance(meta["package_versions"], dict)


def test_metadata_save_and_load(tmp_path):
    """save_metadata → load_metadata 왕복이 올바르게 동작해야 한다."""
    metadata = ModelMetadata(
        model_name="test_model",
        version=1,
        trained_at="2026-04-09T14:30:00+00:00",
        data_rows=500,
        data_date_range={"start": "2020-01-01", "end": "2025-12-31"},
        feature_columns=["lag_1w", "lag_2w"],
        hyperparameters={"lr": 0.01},
        mape=12.5,
        fields=["coding", "art"],
        package_versions={"xgboost": "2.0.0"},
    )

    save_dir = str(tmp_path / "test_model")
    save_metadata(save_dir, version=1, metadata=metadata)

    loaded = load_metadata(save_dir, version=1)
    assert loaded.model_name == "test_model"
    assert loaded.version == 1
    assert loaded.data_rows == 500
    assert loaded.mape == 12.5
    assert loaded.fields == ["coding", "art"]
    assert loaded.data_date_range["start"] == "2020-01-01"
    assert loaded.hyperparameters["lr"] == 0.01


def test_save_without_df_no_metadata(tmp_path):
    """df=None으로 save하면 metadata.json이 생성되지 않아야 한다 (하위 호환)."""
    df = _make_training_df(n=100)
    model = XGBoostForecaster()
    model.train(df)

    save_dir = str(tmp_path / "xgboost_no_meta")
    model.save(save_dir, version=1)  # df 미전달

    meta_path = tmp_path / "xgboost_no_meta" / "v1" / "metadata.json"
    assert not meta_path.exists(), "df=None인데 metadata.json이 생성되었습니다"

    # 모델 파일은 정상 생성
    model_path = tmp_path / "xgboost_no_meta" / "v1" / "model.joblib"
    assert model_path.exists()


def test_ensemble_uses_public_predict():
    """앙상블이 서브모델의 public predict() (lock 포함)를 호출해야 한다."""
    from unittest.mock import MagicMock, patch

    from edupulse.model.ensemble import EnsembleForecaster

    df = _make_training_df(n=100)
    xgb = XGBoostForecaster()
    xgb.train(df)

    ensemble = EnsembleForecaster()
    ensemble.add_model("xgboost", xgb)

    sample = df.iloc[[-1]].copy()

    # predict (public)가 호출되는지, _predict (private)가 아닌지 검증
    with patch.object(xgb, "predict", wraps=xgb.predict) as mock_predict, \
         patch.object(xgb, "_predict", wraps=xgb._predict) as mock_private:
        ensemble.predict(sample)
        mock_predict.assert_called_once()
        # _predict는 predict() 내부에서 1번 호출되지만, 앙상블에서 직접 호출하면 안 됨
        # predict → _predict 체이닝으로 1번만 호출되어야 함
        assert mock_private.call_count == 1


def test_load_metadata_not_found(tmp_path):
    """존재하지 않는 metadata.json 로딩 시 FileNotFoundError가 발생해야 한다."""
    with pytest.raises(FileNotFoundError):
        load_metadata(str(tmp_path / "nonexistent"), version=1)
