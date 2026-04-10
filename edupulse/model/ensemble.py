"""앙상블 수요 예측 모델 — 여러 모델의 가중 평균으로 최종 예측."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from edupulse.constants import classify_demand
from edupulse.model.base import (
    BaseForecaster,
    ModelMetadata,
    PredictionResult,
    _extract_data_info,
    _get_package_version,
    save_metadata,
)

logger = logging.getLogger(__name__)


class EnsembleForecaster(BaseForecaster):
    """여러 BaseForecaster의 예측을 가중 평균하여 앙상블 결과를 반환.

    모델이 1개만 있어도 동작한다 (단일 모델 fallback).
    weights가 None이면 균등 가중치를 사용한다.
    """

    def __init__(
        self,
        models: dict[str, BaseForecaster] | None = None,
        weights: dict[str, float] | None = None,
    ):
        """EnsembleForecaster 초기화.

        Args:
            models: {'xgboost': XGBoostForecaster, ...} 형태의 모델 딕셔너리.
                    None이면 빈 앙상블로 시작 (나중에 add_model로 추가).
            weights: {'xgboost': 0.5, 'prophet': 0.5} 형태의 가중치 딕셔너리.
                     None이면 균등 가중치 사용.
        """
        super().__init__()
        self._models: dict[str, BaseForecaster] = models or {}
        self._weights: dict[str, float] | None = weights

    def add_model(self, name: str, model: BaseForecaster) -> None:
        """앙상블에 모델 추가.

        Args:
            name: 모델 식별자 (예: 'xgboost', 'prophet', 'lstm')
            model: 학습된 BaseForecaster 인스턴스
        """
        self._models[name] = model

    @property
    def model_count(self) -> int:
        """앙상블에 포함된 모델 수."""
        return len(self._models)

    def auto_weight(self, df: pd.DataFrame, n_splits: int = 5) -> dict[str, float]:
        """각 모델의 MAPE 역수로 가중치를 자동 설정하고 반환.

        MAPE가 낮을수록 높은 가중치를 부여한다.
        MAPE가 NaN이거나 0인 모델은 균등 가중치로 처리한다.

        Args:
            df: 평가용 DataFrame
            n_splits: K-Fold 분할 수

        Returns:
            정규화된 가중치 딕셔너리 {'xgboost': 0.6, 'prophet': 0.4, ...}
        """
        inv_mapes: dict[str, float] = {}

        for name, model in self._models.items():
            try:
                result = model.evaluate(df, n_splits=n_splits)
                mape = result.get("mape", float("nan"))
                if mape and not np.isnan(mape) and mape > 0:
                    inv_mapes[name] = 1.0 / mape
                else:
                    inv_mapes[name] = 1.0  # fallback: 균등
            except Exception:
                inv_mapes[name] = 1.0  # fallback: 균등

        total = sum(inv_mapes.values())
        weights = {name: v / total for name, v in inv_mapes.items()}
        self._weights = weights
        return weights

    def _get_effective_weights(self, names: list[str]) -> list[float]:
        """예측에 참여한 모델들의 정규화된 가중치 반환.

        Args:
            names: 예측에 성공한 모델 이름 목록

        Returns:
            정규화된 가중치 리스트 (names 순서 대응)
        """
        if self._weights is None:
            n = len(names)
            return [1.0 / n] * n

        raw = [self._weights.get(name, 1.0) for name in names]
        total = sum(raw)
        if total == 0:
            n = len(names)
            return [1.0 / n] * n
        return [w / total for w in raw]

    def train(self, df: pd.DataFrame) -> None:
        """각 모델의 train()을 순서대로 호출.

        Args:
            df: 모든 모델이 공통으로 사용할 학습 DataFrame
        """
        for name, model in self._models.items():
            try:
                model.train(df)
            except Exception as exc:
                logger.warning("앙상블: %s 학습 실패 (건너뜀) — %s", name, exc)

    def _predict(self, features: pd.DataFrame) -> PredictionResult:
        """각 모델의 예측을 수집하고 가중 평균하여 앙상블 결과 반환.

        모델이 0개이면 RuntimeError를 발생시킨다.
        일부 모델이 실패해도 성공한 모델의 가중 평균으로 계속 진행한다.

        Args:
            features: 예측에 사용할 feature DataFrame

        Returns:
            앙상블 PredictionResult
        """
        if not self._models:
            raise RuntimeError("앙상블에 등록된 모델이 없습니다. add_model()로 모델을 추가하세요.")

        enrollments: list[float] = []
        lowers: list[float] = []
        uppers: list[float] = []
        mapes: list[float] = []
        used_names: list[str] = []

        for name, model in self._models.items():
            try:
                result = model.predict(features)
                enrollments.append(float(result.predicted_enrollment))
                lowers.append(result.confidence_lower)
                uppers.append(result.confidence_upper)
                if result.mape is not None:
                    mapes.append(result.mape)
                used_names.append(name)
            except Exception as exc:
                logger.warning("앙상블: %s 예측 실패 (건너뜀) — %s", name, exc)

        if not enrollments:
            raise RuntimeError("앙상블 내 모든 모델 예측에 실패했습니다.")

        weights = self._get_effective_weights(used_names)

        avg_enrollment = float(np.average(enrollments, weights=weights))
        predicted_enrollment = max(0, round(avg_enrollment))
        demand_tier = classify_demand(predicted_enrollment)

        confidence_lower = max(0.0, round(float(np.average(lowers, weights=weights)), 1))
        confidence_upper = round(float(np.average(uppers, weights=weights)), 1)
        confidence_upper = max(confidence_upper, confidence_lower)

        avg_mape = float(np.mean(mapes)) if mapes else None
        model_used = f"ensemble({'+'.join(used_names)})"

        return PredictionResult(
            predicted_enrollment=predicted_enrollment,
            demand_tier=demand_tier,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            model_used=model_used,
            mape=avg_mape,
        )

    def evaluate(self, df: pd.DataFrame, n_splits: int = 5) -> dict:
        """각 모델의 evaluate() 결과를 수집하고 가중 평균 MAPE 반환.

        Args:
            df: 평가용 DataFrame
            n_splits: K-Fold 분할 수

        Returns:
            {'mape': float, 'n_splits': int, 'model_mapes': dict}
        """
        model_mapes: dict[str, float] = {}
        valid_names: list[str] = []
        valid_mapes: list[float] = []

        for name, model in self._models.items():
            try:
                result = model.evaluate(df, n_splits=n_splits)
                mape_val = result.get("mape", float("nan"))
                model_mapes[name] = mape_val
                if not np.isnan(mape_val):
                    valid_names.append(name)
                    valid_mapes.append(mape_val)
            except Exception as exc:
                logger.warning("앙상블: %s 평가 실패 (건너뜀) — %s", name, exc)
                model_mapes[name] = float("nan")

        if valid_names:
            weights = self._get_effective_weights(valid_names)
            avg_mape = float(np.average(valid_mapes, weights=weights))
        else:
            avg_mape = float("nan")
        return {"mape": avg_mape, "n_splits": n_splits, "model_mapes": model_mapes}

    def save(self, path: str, version: int, df: pd.DataFrame | None = None) -> None:
        """각 모델을 개별 하위 디렉터리에 저장.

        Args:
            path: 저장 루트 경로 (예: edupulse/model/saved/ensemble)
            version: 버전 번호
            df: 학습 DataFrame (메타데이터 생성용, None이면 메타데이터 생략)
        """
        for name, model in self._models.items():
            model.save(f"{path}/{name}", version=version, df=df)

        if df is not None:
            from datetime import datetime, timezone

            data_info = _extract_data_info(df)
            metadata = ModelMetadata(
                model_name="ensemble",
                version=version,
                trained_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                data_rows=data_info["data_rows"],
                data_date_range=data_info["data_date_range"],
                feature_columns=[],
                hyperparameters={
                    "weights": self._weights,
                    "models": list(self._models.keys()),
                },
                mape=None,
                fields=data_info["fields"],
            )
            save_metadata(path, version, metadata)

    def load(self, path: str, version: int) -> None:
        """각 모델을 개별 하위 디렉터리에서 로딩.

        Args:
            path: 저장 루트 경로 (예: edupulse/model/saved/ensemble)
            version: 버전 번호
        """
        for name, model in self._models.items():
            model.load(f"{path}/{name}", version=version)
