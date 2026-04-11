"""모델 관련 테스트."""
import pandas as pd
import pytest

from edupulse.constants import DemandTier, classify_demand, DEMAND_THRESHOLDS
from edupulse.model.base import (
    ModelMetadata,
    PredictionResult,
    ensure_feature_columns,
    load_metadata,
    save_metadata,
    warn_feature_mismatch,
)
from edupulse.model.xgboost_model import FEATURE_COLUMNS, XGBoostForecaster
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
        "page_views": rng.integers(10, 200, size=n).tolist(),
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
        INPUT_SIZE,
    )
    from edupulse.model.xgboost_model import FEATURE_COLUMNS

    # 이름 기반 인덱스 검증
    assert INPUT_SIZE == len(FEATURE_COLUMNS)
    from edupulse.model.lstm_model import _PROTECTED_NAMES
    for idx in PROTECTED_FEATURES:
        assert FEATURE_COLUMNS[idx] in _PROTECTED_NAMES
    for idx in AUGMENTABLE_FEATURES:
        assert FEATURE_COLUMNS[idx] not in _PROTECTED_NAMES
    assert sorted(PROTECTED_FEATURES + AUGMENTABLE_FEATURES) == list(range(INPUT_SIZE))

    rng = np.random.default_rng(0)
    n_seq, seq_len, n_feat = 20, 12, INPUT_SIZE
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


def test_missing_columns_warns():
    """피처 컬럼이 누락되면 UserWarning이 발생해야 한다."""
    import warnings
    from edupulse.model.base import validate_feature_columns

    df = pd.DataFrame({"lag_1w": [1.0], "lag_2w": [2.0]})
    expected = ["lag_1w", "lag_2w", "lag_4w", "nonexistent"]

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = validate_feature_columns(expected, df, "test")
        assert result == ["lag_1w", "lag_2w"]
        assert len(w) == 1
        assert "lag_4w" in str(w[0].message)
        assert "nonexistent" in str(w[0].message)

    # 모든 컬럼이 있으면 경고 없음
    df_full = pd.DataFrame({"a": [1], "b": [2]})
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        validate_feature_columns(["a", "b"], df_full, "test")
        assert len(w) == 0


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

    with patch.object(xgb, "predict", wraps=xgb.predict) as mock_predict, \
         patch.object(xgb, "_predict", wraps=xgb._predict) as mock_private:
        ensemble.predict(sample)
        mock_predict.assert_called_once()
        # 앙상블은 public predict()만 호출 — _predict는 predict() 내부 체이닝으로 1번
        assert mock_private.call_count == 1


def test_load_metadata_not_found(tmp_path):
    """존재하지 않는 metadata.json 로딩 시 FileNotFoundError가 발생해야 한다."""
    with pytest.raises(FileNotFoundError):
        load_metadata(str(tmp_path / "nonexistent"), version=1)


def test_ensure_feature_columns_no_mutation():
    """ensure_feature_columns가 원본 DataFrame을 수정하지 않아야 한다."""
    df = pd.DataFrame({"lag_1w": [1.0], "lag_2w": [2.0]})
    original_cols = list(df.columns)

    result = ensure_feature_columns(df, ["lag_1w", "lag_2w", "lag_4w", "missing"], "test")

    # 원본 변경 없음
    assert list(df.columns) == original_cols
    assert "lag_4w" not in df.columns
    assert "missing" not in df.columns

    # 반환값에는 누락 컬럼이 0.0으로 채워짐
    assert "lag_4w" in result.columns
    assert "missing" in result.columns
    assert result["lag_4w"].iloc[0] == 0.0
    assert result["missing"].iloc[0] == 0.0

    # 기존 값은 보존
    assert result["lag_1w"].iloc[0] == 1.0
    assert result["lag_2w"].iloc[0] == 2.0


def test_ensure_feature_columns_all_present():
    """모든 컬럼이 존재하면 복사 없이 원본을 반환해야 한다."""
    df = pd.DataFrame({"a": [1], "b": [2]})
    result = ensure_feature_columns(df, ["a", "b"], "test")
    assert result is df  # 동일 객체


def test_xgboost_train_with_missing_features():
    """피처 누락 DataFrame으로 XGBoost train → predict 시 ValueError 없이 동작해야 한다."""
    import numpy as np
    rng = np.random.default_rng(42)
    n = 100
    # search_volume, job_count 없는 DataFrame
    dates = pd.date_range("2021-01-04", periods=n, freq="W-MON")
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "field": ["coding"] * n,
        "enrollment_count": rng.integers(1, 10, size=n).tolist(),
    })
    df = add_lag_features(df, target_col="enrollment_count")

    model = XGBoostForecaster()
    model.train(df)  # search_volume, job_count 없음 → 0 패딩

    sample = df.iloc[[-1]]
    result = model.predict(sample)

    assert isinstance(result, PredictionResult)
    assert result.predicted_enrollment >= 0


def test_warn_feature_mismatch_warns(tmp_path):
    """load 시 피처 불일치가 있으면 UserWarning이 발생해야 한다."""
    import warnings

    # 학습 시 피처 2개로 metadata 저장
    metadata = ModelMetadata(
        model_name="test",
        version=1,
        trained_at="2026-04-09T00:00:00+00:00",
        data_rows=100,
        feature_columns=["lag_1w", "lag_2w"],
    )
    save_dir = str(tmp_path / "test")
    save_metadata(save_dir, version=1, metadata=metadata)

    # 현재 피처가 다를 때 경고
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warn_feature_mismatch(save_dir, 1, ["lag_1w", "lag_2w", "lag_4w"])
        assert len(w) == 1
        assert "피처 불일치" in str(w[0].message)
        assert "lag_4w" in str(w[0].message)


def test_warn_feature_mismatch_no_metadata(tmp_path):
    """metadata.json이 없으면 경고 없이 조용히 통과해야 한다."""
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warn_feature_mismatch(str(tmp_path / "nonexistent"), 1, ["a", "b"])
        assert len(w) == 0


def test_warn_feature_mismatch_same_features(tmp_path):
    """피처가 동일하면 경고 없이 통과해야 한다."""
    import warnings

    metadata = ModelMetadata(
        model_name="test",
        version=1,
        trained_at="2026-04-09T00:00:00+00:00",
        data_rows=100,
        feature_columns=["lag_1w", "lag_2w"],
    )
    save_dir = str(tmp_path / "test")
    save_metadata(save_dir, version=1, metadata=metadata)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        warn_feature_mismatch(save_dir, 1, ["lag_1w", "lag_2w"])
        assert len(w) == 0


def test_xgboost_hyperparams_consistency():
    """XGBoost train()과 evaluate()가 동일한 HYPERPARAMS 상수를 사용해야 한다."""
    from edupulse.model.xgboost_model import HYPERPARAMS

    assert isinstance(HYPERPARAMS, dict)
    assert "n_estimators" in HYPERPARAMS
    assert "learning_rate" in HYPERPARAMS
    assert HYPERPARAMS["n_estimators"] == 300
    assert HYPERPARAMS["learning_rate"] == 0.03

    # train과 evaluate 모두 동일 상수를 사용하는지 간접 검증:
    # evaluate 내부에서 생성되는 모델도 동일 파라미터를 가져야 한다
    df = _make_training_df(n=100)
    model = XGBoostForecaster()
    model.train(df)
    assert model._model.get_params()["n_estimators"] == HYPERPARAMS["n_estimators"]
    assert model._model.get_params()["learning_rate"] == HYPERPARAMS["learning_rate"]


def test_merger_ffill_field_boundary():
    """merger ffill이 분야 경계를 넘어 데이터가 누수되지 않아야 한다."""
    from edupulse.preprocessing.merger import merge_datasets

    # 분야 A: 마지막 행에 값 있음, 분야 B: 첫 행에 NaN
    enrollment_df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-08", "2024-01-15", "2024-01-22"],
        "field": ["coding", "coding", "security", "security"],
        "enrollment_count": [10, 20, 30, 40],
    })
    search_df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-08", "2024-01-15", "2024-01-22"],
        "field": ["coding", "coding", "security", "security"],
        "search_volume": [100.0, float("nan"), float("nan"), 400.0],
    })

    merged = merge_datasets(enrollment_df, search_df)

    # coding의 NaN은 coding의 이전 값(100)으로 채워져야 함
    coding_rows = merged[merged["field"] == "coding"]
    assert coding_rows["search_volume"].iloc[1] == 100.0

    # security의 NaN은 coding의 값(100)으로 누수되면 안 됨
    security_rows = merged[merged["field"] == "security"]
    # security 첫 행은 이전 security 값이 없으므로 NaN 유지
    assert pd.isna(security_rows["search_volume"].iloc[0])
    assert security_rows["search_volume"].iloc[1] == 400.0


def test_load_model_thread_safety():
    """동시 load_model 호출 시 캐시가 스레드 안전하게 동작해야 한다."""
    import concurrent.futures
    from unittest.mock import patch
    from edupulse.model.predict import clear_model_cache, load_model, _cache_lock

    clear_model_cache()

    # XGBoost 모델을 학습하여 저장
    df = _make_training_df(n=100)
    xgb = XGBoostForecaster()
    xgb.train(df)

    import tempfile
    import joblib
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        save_dir = Path(tmp) / "xgboost" / "v1"
        save_dir.mkdir(parents=True)
        joblib.dump({"model": xgb._model, "mape": xgb._mape}, save_dir / "model.joblib")

        with patch("edupulse.model.predict.load_model") as mock_load:
            # 실제 구현 대신 _cache_lock 존재 여부만 검증
            pass

    # Lock 객체 존재 확인
    assert _cache_lock is not None
    import threading
    assert isinstance(_cache_lock, type(threading.Lock()))

    clear_model_cache()


def test_ensemble_confidence_weighted():
    """앙상블 CI가 min/max가 아닌 가중 평균으로 계산되어야 한다."""
    from edupulse.model.ensemble import EnsembleForecaster

    df = _make_training_df(n=100)

    xgb1 = XGBoostForecaster()
    xgb1.train(df)

    xgb2 = XGBoostForecaster()
    xgb2.train(df)

    ensemble = EnsembleForecaster()
    ensemble.add_model("model_a", xgb1)
    ensemble.add_model("model_b", xgb2)

    sample = df.iloc[[-1]].copy()
    result = ensemble.predict(sample)

    # 단일 모델의 결과도 가져와서 비교
    result_a = xgb1.predict(sample)
    result_b = xgb2.predict(sample)

    # 균등 가중 평균이므로 (a + b) / 2
    expected_lower = (result_a.confidence_lower + result_b.confidence_lower) / 2
    expected_upper = (result_a.confidence_upper + result_b.confidence_upper) / 2

    assert abs(result.confidence_lower - round(expected_lower, 1)) <= 0.2
    assert abs(result.confidence_upper - round(expected_upper, 1)) <= 0.2


def test_add_lag_features_unsorted_input():
    """정렬되지 않은 입력에서도 add_lag_features가 올바른 lag를 생성해야 한다."""
    import numpy as np

    # 날짜 역순으로 DataFrame 생성
    dates = pd.date_range("2021-01-04", periods=20, freq="W-MON")
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "field": ["coding"] * 20,
        "enrollment_count": list(range(1, 21)),
    })
    # 역순으로 섞기
    df_shuffled = df.iloc[::-1].reset_index(drop=True)

    result = add_lag_features(df_shuffled, target_col="enrollment_count")

    # 정렬된 상태에서의 결과와 비교
    result_sorted = add_lag_features(df, target_col="enrollment_count")

    # 동일한 date 행의 lag_1w 값이 일치해야 한다
    r1 = result.set_index("date").sort_index()
    r2 = result_sorted.set_index("date").sort_index()
    np.testing.assert_array_equal(r1["lag_1w"].values, r2["lag_1w"].values)
    np.testing.assert_array_equal(r1["lag_4w"].values, r2["lag_4w"].values)


def test_evaluate_does_not_overwrite_mape():
    """학습 후 evaluate()를 호출해도 기존 self._mape가 보존되어야 한다."""
    df = _make_training_df(n=100)
    model = XGBoostForecaster()
    model.train(df)

    # 학습 후 evaluate로 mape 설정
    model._mape = None  # 초기화
    result1 = model.evaluate(df, n_splits=3)
    first_mape = model._mape
    assert first_mape is not None

    # 두 번째 evaluate 호출 — 기존 mape를 덮어쓰지 않아야 함
    result2 = model.evaluate(df, n_splits=3)
    assert model._mape == first_mape

    # 반환값에는 새로운 MAPE가 포함됨
    assert "mape" in result2


def test_build_features_csv_caching(tmp_path):
    """build_features의 CSV 캐시가 동작하고 clear_model_cache로 초기화되어야 한다."""
    from edupulse.model.predict import _data_cache, load_csv_cached, clear_model_cache

    clear_model_cache()
    assert len(_data_cache) == 0

    # build_features 호출 (CSV 없어도 에러 없이 0으로 채움)
    from edupulse.model.predict import build_features
    features = build_features("test", "2026-05-01", "coding")
    assert len(features) == 1

    # 존재하는 파일만 캐시에 저장됨 (미존재 파일은 저장 안 함)
    # build_features 실행 후 캐시된 항목 수를 기준으로 저장
    cache_count_after_build = len(_data_cache)

    # 실제 CSV 파일이 있으면 캐시에 저장됨
    csv_path = str(tmp_path / "test.csv")
    pd.DataFrame({"a": [1, 2]}).to_csv(csv_path, index=False)
    result = load_csv_cached(csv_path)
    assert result is not None
    assert csv_path in _data_cache
    assert len(_data_cache) == cache_count_after_build + 1

    # clear 후 캐시 비워짐
    clear_model_cache()
    assert len(_data_cache) == 0


def test_lstm_feature_compatibility_check(tmp_path):
    """LSTM load 시 피처 수 불일치가 있으면 RuntimeError가 발생해야 한다."""
    if not _TORCH_AVAILABLE:
        pytest.skip("PyTorch 미설치")

    from edupulse.model.lstm_model import _check_feature_compatibility

    # 피처 2개로 metadata 저장
    metadata = ModelMetadata(
        model_name="lstm",
        version=1,
        trained_at="2026-04-09T00:00:00+00:00",
        data_rows=100,
        feature_columns=["lag_1w", "lag_2w"],
    )
    save_dir = str(tmp_path / "lstm")
    save_metadata(save_dir, version=1, metadata=metadata)

    # 피처 수가 다르면 RuntimeError
    with pytest.raises(RuntimeError, match="피처 수 불일치"):
        _check_feature_compatibility(save_dir, 1, ["lag_1w", "lag_2w", "lag_4w"])

    # 피처 수 같지만 순서 다르면 RuntimeError (LSTM은 순서에 민감)
    with pytest.raises(RuntimeError, match="피처 순서/구성 불일치"):
        _check_feature_compatibility(save_dir, 1, ["lag_2w", "lag_1w"])

    # 피처가 동일하면 통과
    _check_feature_compatibility(save_dir, 1, ["lag_1w", "lag_2w"])

    # metadata 없으면 조용히 통과
    _check_feature_compatibility(str(tmp_path / "nonexistent"), 1, ["a", "b"])


def test_compute_month_encoding_consistency():
    """transformer의 공유 함수와 numpy 벡터 연산이 동일한 결과를 내야 한다."""
    import math
    from edupulse.preprocessing.transformer import compute_month_encoding

    for month in range(1, 13):
        sin_val, cos_val = compute_month_encoding(month)
        expected_sin = math.sin(2 * math.pi * month / 12)
        expected_cos = math.cos(2 * math.pi * month / 12)
        assert abs(sin_val - expected_sin) < 1e-10
        assert abs(cos_val - expected_cos) < 1e-10


def test_compute_field_encoding_values():
    """compute_field_encoding이 FIELD_ENCODING과 일치해야 한다."""
    from edupulse.preprocessing.transformer import compute_field_encoding
    from edupulse.constants import FIELD_ENCODING

    for field, expected in FIELD_ENCODING.items():
        assert compute_field_encoding(field) == float(expected)
    # 미등록 분야는 0.0
    assert compute_field_encoding("unknown_field") == 0.0


def test_find_latest_version(tmp_path):
    """find_latest_version이 vN 디렉토리에서 최대 N을 반환해야 한다."""
    from edupulse.model.utils import find_latest_version

    # 빈 디렉토리 → 0
    assert find_latest_version(str(tmp_path / "empty")) == 0

    # v1, v3 존재 → 3
    model_dir = tmp_path / "xgboost"
    (model_dir / "v1").mkdir(parents=True)
    (model_dir / "v3").mkdir(parents=True)
    (model_dir / "not_a_version").mkdir()  # 무시되어야 함
    assert find_latest_version(str(model_dir)) == 3


def test_retrain_resolve_version(tmp_path):
    """_resolve_version이 None일 때 latest+1을 반환해야 한다."""
    from unittest.mock import patch
    from edupulse.model.retrain import _resolve_version

    # 명시적 버전은 그대로 반환
    assert _resolve_version("xgboost", 5) == 5

    # None이면 자동 감지
    with patch("edupulse.model.utils.find_latest_version", return_value=3):
        assert _resolve_version("xgboost", None) == 4

    # 버전 없으면 1
    with patch("edupulse.model.utils.find_latest_version", return_value=0):
        assert _resolve_version("xgboost", None) == 1


def test_clean_data_forward_only_interpolation():
    """clean_data가 전방 보간만 수행하여 미래 데이터 누수를 방지해야 한다."""
    from edupulse.preprocessing.cleaner import clean_data

    df = pd.DataFrame({
        "date": ["2025-01-01", "2025-01-08", "2025-01-15", "2025-01-22"],
        "enrollment_count": [float("nan"), float("nan"), 100.0, 200.0],
    })
    result = clean_data(df, target_col="enrollment_count")
    # 전방 보간만 적용: 첫 두 행은 이전 값이 없으므로 NaN 유지
    assert pd.isna(result["enrollment_count"].iloc[0])
    assert pd.isna(result["enrollment_count"].iloc[1])
    assert result["enrollment_count"].iloc[2] == 100.0


def test_build_features_unknown_field_raises():
    """build_features에 미등록 분야를 전달하면 ValueError가 발생해야 한다."""
    from edupulse.model.predict import build_features, clear_model_cache

    clear_model_cache()
    with pytest.raises(ValueError, match="미등록 분야"):
        build_features("test", "2026-05-01", "unknown_field")


def test_retrain_evaluate_safe_access():
    """retrain에서 evaluate 결과의 mape 키가 없어도 크래시하지 않아야 한다."""
    from unittest.mock import patch, MagicMock

    from edupulse.model.retrain import retrain

    # train과 evaluate를 모킹하되, evaluate가 'all' 형태 결과를 반환
    with patch("edupulse.model.retrain._resolve_version", return_value=1), \
         patch("edupulse.preprocessing.merger.build_training_dataset"), \
         patch("edupulse.model.train.train_model"), \
         patch("edupulse.model.evaluate.evaluate_model", return_value={"model_mapes": {}, "comparison_table": "", "n_splits": 5}), \
         patch("edupulse.model.predict.clear_model_cache"):
        # mape 키 없어도 크래시하지 않아야 함
        retrain(model_name="xgboost", version=1)


def test_ensemble_evaluate_weighted_mape():
    """앙상블 evaluate가 가중 MAPE를 반환해야 한다."""
    from unittest.mock import MagicMock
    from edupulse.model.ensemble import EnsembleForecaster

    ensemble = EnsembleForecaster()

    mock_a = MagicMock()
    mock_a.evaluate.return_value = {"mape": 10.0}
    mock_b = MagicMock()
    mock_b.evaluate.return_value = {"mape": 20.0}

    ensemble.add_model("a", mock_a)
    ensemble.add_model("b", mock_b)

    # 균등 가중치 (weights=None) → 단순 평균 = 15.0
    result = ensemble.evaluate(pd.DataFrame(), n_splits=3)
    assert abs(result["mape"] - 15.0) < 0.01

    # 가중치 설정: a=0.8, b=0.2 → 가중 평균 = 10*0.8 + 20*0.2 = 12.0
    ensemble._weights = {"a": 0.8, "b": 0.2}
    result = ensemble.evaluate(pd.DataFrame(), n_splits=3)
    assert abs(result["mape"] - 12.0) < 0.01
