"""XGBoost 수요 예측 모델 래퍼."""
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor

from edupulse.constants import classify_demand
from edupulse.model.base import (
    BaseForecaster,
    ModelMetadata,
    PredictionResult,
    _extract_data_info,
    _get_package_version,
    ensure_feature_columns,
    save_metadata,
    warn_feature_mismatch,
)

FEATURE_COLUMNS = [
    # --- 시계열 (5) ---
    "lag_1w", "lag_2w", "lag_4w", "lag_8w",
    "rolling_mean_4w",
    # --- 날짜/분야 인코딩 (3) ---
    "month_sin", "month_cos", "field_encoded",
    # --- 외부 지표 (2) ---
    "search_volume", "job_count",
    # --- 내부 선행지표 (2) ---
    "consultation_count", "page_views",
    # --- 자격증 일정 (2) ---
    "has_cert_exam", "weeks_to_exam",
    # --- 경쟁사 (2) ---
    "competitor_openings", "competitor_avg_price",
    # --- 계절 이벤트 (3) ---
    "is_vacation", "is_exam_season", "is_semester_start",
]
TARGET_COLUMN = "enrollment_count"

HYPERPARAMS = {
    "n_estimators": 300,
    "max_depth": 4,
    "learning_rate": 0.03,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
    "n_jobs": -1,
}


class XGBoostForecaster(BaseForecaster):
    """XGBoost 기반 수강 수요 예측 모델."""

    def __init__(self):
        super().__init__()
        self._model: XGBRegressor | None = None
        self._mape: float | None = None

    def train(self, df: pd.DataFrame) -> None:
        """feature/target 분리 후 XGBRegressor 학습.

        Args:
            df: feature_columns + target_column을 포함한 DataFrame
        """
        df = ensure_feature_columns(df, FEATURE_COLUMNS, "XGBoost.train")
        X = df[FEATURE_COLUMNS].fillna(0)
        y = df[TARGET_COLUMN]

        self._model = XGBRegressor(**HYPERPARAMS)
        self._model.fit(X, y)

    def _predict(self, features: pd.DataFrame) -> PredictionResult:
        """xgb 예측 → classify_demand() → PredictionResult 반환.

        Args:
            features: feature_columns에 해당하는 DataFrame (1행 이상)
        """
        if self._model is None:
            raise RuntimeError("Model not trained or loaded. Call train() or load() first.")

        features = ensure_feature_columns(features, FEATURE_COLUMNS, "XGBoost.predict")
        X = features[FEATURE_COLUMNS].fillna(0)
        raw_pred = float(self._model.predict(X)[0])
        predicted_enrollment = max(0, round(raw_pred))

        demand_tier = classify_demand(predicted_enrollment)

        margin = (self._mape / 100.0 * raw_pred) if self._mape else (raw_pred * 0.15)
        confidence_lower = max(0.0, round(raw_pred - margin, 1))
        confidence_upper = round(raw_pred + margin, 1)

        return PredictionResult(
            predicted_enrollment=predicted_enrollment,
            demand_tier=demand_tier,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            model_used="xgboost",
            mape=self._mape,
        )

    def evaluate(self, df: pd.DataFrame, n_splits: int = 5) -> dict:
        """TimeSeriesSplit K-Fold 교차검증. 분야별 분리 평가 후 평균 MAPE 반환.

        Args:
            df: feature_columns + target_column을 포함한 DataFrame
            n_splits: K-Fold 분할 수

        Returns:
            {'mape': float, 'n_splits': int}
        """
        df = ensure_feature_columns(df, FEATURE_COLUMNS, "XGBoost.evaluate")

        if "field" in df.columns and df["field"].nunique() > 1:
            return self._evaluate_per_field(df, n_splits)
        return self._evaluate_single(df, n_splits)

    def _evaluate_single(self, df: pd.DataFrame, n_splits: int) -> dict:
        """단일 시계열 평가."""
        X = df[FEATURE_COLUMNS].fillna(0).values
        y = df[TARGET_COLUMN].values
        mapes = self._evaluate_fold(X, y, n_splits)
        avg_mape = float(np.mean(mapes)) if mapes else float("nan")
        if self._mape is None:
            self._mape = avg_mape
        return {"mape": avg_mape, "n_splits": n_splits}

    def _evaluate_per_field(self, df: pd.DataFrame, n_splits: int) -> dict:
        """분야별 분리 평가 후 평균 MAPE 반환."""
        all_mapes: list[float] = []
        for field in df["field"].unique():
            field_df = df[df["field"] == field].sort_values("date").reset_index(drop=True)
            X = field_df[FEATURE_COLUMNS].fillna(0).values
            y = field_df[TARGET_COLUMN].values
            all_mapes.extend(self._evaluate_fold(X, y, n_splits))
        avg_mape = float(np.mean(all_mapes)) if all_mapes else float("nan")
        if self._mape is None:
            self._mape = avg_mape
        return {"mape": avg_mape, "n_splits": n_splits}

    def _evaluate_fold(
        self, X: np.ndarray, y: np.ndarray, n_splits: int,
    ) -> list[float]:
        """K-Fold 평가 공통 로직."""
        tscv = TimeSeriesSplit(n_splits=n_splits)
        mapes: list[float] = []

        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            model = XGBRegressor(**HYPERPARAMS)
            model.fit(X_train, y_train)
            preds = model.predict(X_val)

            nonzero = y_val != 0
            if nonzero.any():
                fold_mape = float(np.mean(np.abs((y_val[nonzero] - preds[nonzero]) / y_val[nonzero])) * 100)
                mapes.append(fold_mape)

        return mapes

    def save(self, path: str, version: int, df: pd.DataFrame | None = None) -> None:
        """모델을 joblib으로 직렬화 저장.

        Args:
            path: 저장 루트 경로 (예: edupulse/model/saved/xgboost)
            version: 버전 번호
            df: 학습 DataFrame (메타데이터 생성용, None이면 메타데이터 생략)
        """
        save_dir = Path(path) / f"v{version}"
        save_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"model": self._model, "mape": self._mape},
            save_dir / "model.joblib",
        )

        if df is not None:
            from datetime import datetime, timezone

            data_info = _extract_data_info(df)
            metadata = ModelMetadata(
                model_name="xgboost",
                version=version,
                trained_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                data_rows=data_info["data_rows"],
                data_date_range=data_info["data_date_range"],
                feature_columns=[c for c in FEATURE_COLUMNS if c in df.columns],
                hyperparameters=HYPERPARAMS,
                mape=self._mape,
                fields=data_info["fields"],
                package_versions={
                    "xgboost": _get_package_version("xgboost"),
                    "scikit-learn": _get_package_version("scikit-learn"),
                },
            )
            save_metadata(path, version, metadata)

    def load(self, path: str, version: int) -> None:
        """저장된 모델을 joblib으로 로딩.

        Args:
            path: 저장 루트 경로 (예: edupulse/model/saved/xgboost)
            version: 버전 번호
        """
        model_path = Path(path) / f"v{version}" / "model.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        data = joblib.load(model_path)
        self._model = data["model"]
        self._mape = data.get("mape")
        warn_feature_mismatch(path, version, FEATURE_COLUMNS)
