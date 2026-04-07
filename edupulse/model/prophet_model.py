"""Prophet 수요 예측 모델 래퍼."""
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from edupulse.constants import classify_demand
from edupulse.model.base import BaseForecaster, PredictionResult

# Prophet은 선택적 의존성 — 미설치 환경(torch-only)에서도 임포트 안전
try:
    from prophet import Prophet
    _PROPHET_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PROPHET_AVAILABLE = False

# Prophet이 필요로 하는 컬럼
DATE_COLUMN = "date"
TARGET_COLUMN = "enrollment_count"

# 추가 회귀자 (외부 데이터)
REGRESSOR_COLUMNS = ["search_volume", "job_count"]


class ProphetForecaster(BaseForecaster):
    """Facebook Prophet 기반 수강 수요 예측 모델.

    Prophet은 ds(날짜) / y(목표값) 형식의 DataFrame을 요구한다.
    내부적으로 date + enrollment_count 컬럼을 ds/y로 변환한 뒤 학습한다.
    search_volume, job_count가 있으면 추가 회귀자로 활용한다.
    """

    def __init__(
        self,
        seasonality_mode: str = "multiplicative",
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = False,
        changepoint_prior_scale: float = 0.05,
    ):
        """ProphetForecaster 초기화.

        Args:
            seasonality_mode: 계절성 모드 ('multiplicative' 또는 'additive')
            yearly_seasonality: 연간 계절성 활성화 여부
            weekly_seasonality: 주간 계절성 활성화 여부
            changepoint_prior_scale: 변화점 민감도 (높을수록 유연)
        """
        super().__init__()
        if not _PROPHET_AVAILABLE:
            raise ImportError(
                "prophet 패키지가 설치되지 않았습니다. "
                "`pip install prophet` 또는 `conda install -c conda-forge prophet`으로 설치하세요."
            )
        self._seasonality_mode = seasonality_mode
        self._yearly_seasonality = yearly_seasonality
        self._weekly_seasonality = weekly_seasonality
        self._changepoint_prior_scale = changepoint_prior_scale
        self._model: "Prophet | None" = None
        self._mape: float | None = None
        self._regressors: list[str] = []

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _to_prophet_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """DataFrame을 Prophet 형식(ds, y, regressors)으로 변환.

        Args:
            df: date + enrollment_count (+ 선택적 회귀자) 컬럼을 포함한 DataFrame

        Returns:
            ds, y 및 회귀자 컬럼이 포함된 DataFrame
        """
        prophet_df = pd.DataFrame()
        prophet_df["ds"] = pd.to_datetime(df[DATE_COLUMN])
        prophet_df["y"] = df[TARGET_COLUMN].astype(float)

        for col in REGRESSOR_COLUMNS:
            if col in df.columns:
                prophet_df[col] = df[col].fillna(0).astype(float)

        return prophet_df

    def _build_model(self, regressors: list[str]) -> "Prophet":
        """Prophet 모델 인스턴스 생성 및 회귀자 등록.

        Args:
            regressors: 추가할 회귀자 컬럼 이름 목록

        Returns:
            설정이 완료된 Prophet 인스턴스
        """
        model = Prophet(
            seasonality_mode=self._seasonality_mode,
            yearly_seasonality=self._yearly_seasonality,
            weekly_seasonality=self._weekly_seasonality,
            changepoint_prior_scale=self._changepoint_prior_scale,
        )
        for reg in regressors:
            model.add_regressor(reg)
        return model

    # ------------------------------------------------------------------
    # BaseForecaster 구현
    # ------------------------------------------------------------------

    def train(self, df: pd.DataFrame) -> None:
        """Prophet 모델 학습.

        Args:
            df: date, enrollment_count (+ 선택적 search_volume, job_count) 컬럼 포함 DataFrame
        """
        prophet_df = self._to_prophet_df(df)
        self._regressors = [c for c in REGRESSOR_COLUMNS if c in prophet_df.columns]

        self._model = self._build_model(self._regressors)
        self._model.fit(prophet_df)

    def _predict(self, features: pd.DataFrame) -> PredictionResult:
        """Prophet 예측 → classify_demand() → PredictionResult 반환.

        Args:
            features: date 컬럼 (+ 선택적 회귀자)을 포함한 DataFrame (1행 이상)
                      date 컬럼이 없을 경우 현재 날짜를 사용한다.

        Returns:
            PredictionResult 인스턴스
        """
        if self._model is None:
            raise RuntimeError("모델이 학습되지 않았습니다. train() 또는 load()를 먼저 호출하세요.")

        # ds 컬럼 구성
        if DATE_COLUMN in features.columns:
            future = pd.DataFrame({"ds": pd.to_datetime(features[DATE_COLUMN])})
        else:
            future = pd.DataFrame({"ds": [pd.Timestamp.today().normalize()]})

        # 회귀자 추가
        for reg in self._regressors:
            if reg in features.columns:
                future[reg] = features[reg].fillna(0).values[: len(future)]
            else:
                future[reg] = 0.0

        forecast = self._model.predict(future)
        raw_pred = float(forecast["yhat"].iloc[0])
        predicted_enrollment = max(0, round(raw_pred))

        demand_tier = classify_demand(predicted_enrollment)

        # Prophet의 yhat_lower / yhat_upper를 신뢰구간으로 활용
        confidence_lower = max(0.0, round(float(forecast["yhat_lower"].iloc[0]), 1))
        confidence_upper = round(float(forecast["yhat_upper"].iloc[0]), 1)

        return PredictionResult(
            predicted_enrollment=predicted_enrollment,
            demand_tier=demand_tier,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            model_used="prophet",
            mape=self._mape,
        )

    def evaluate(self, df: pd.DataFrame, n_splits: int = 5) -> dict:
        """TimeSeriesSplit K-Fold 교차검증. MAPE 반환.

        시계열 데이터 특성상 랜덤 셔플 없이 순서를 유지한 채 분할한다.

        Args:
            df: date + enrollment_count (+ 선택적 회귀자) 컬럼 포함 DataFrame
            n_splits: K-Fold 분할 수

        Returns:
            {'mape': float, 'n_splits': int}
        """
        prophet_df = self._to_prophet_df(df)
        regressors = [c for c in REGRESSOR_COLUMNS if c in prophet_df.columns]

        tscv = TimeSeriesSplit(n_splits=n_splits)
        indices = np.arange(len(prophet_df))
        mapes = []

        for train_idx, val_idx in tscv.split(indices):
            train_df = prophet_df.iloc[train_idx].reset_index(drop=True)
            val_df = prophet_df.iloc[val_idx].reset_index(drop=True)

            fold_model = self._build_model(regressors)
            fold_model.fit(train_df)

            future = val_df[["ds"] + regressors].copy() if regressors else val_df[["ds"]].copy()
            forecast = fold_model.predict(future)

            y_true = val_df["y"].values
            y_pred = forecast["yhat"].values

            nonzero = y_true != 0
            if nonzero.any():
                fold_mape = float(
                    np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100
                )
                mapes.append(fold_mape)

        avg_mape = float(np.mean(mapes)) if mapes else float("nan")
        self._mape = avg_mape
        return {"mape": avg_mape, "n_splits": n_splits}

    # ------------------------------------------------------------------
    # 저장 / 로딩
    # ------------------------------------------------------------------

    def save(self, path: str, version: int) -> None:
        """모델을 joblib으로 직렬화 저장.

        Args:
            path: 저장 루트 경로 (예: edupulse/model/saved/prophet)
            version: 버전 번호
        """
        if self._model is None:
            raise RuntimeError("저장할 모델이 없습니다. train()을 먼저 호출하세요.")

        save_dir = Path(path) / f"v{version}"
        save_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": self._model,
                "mape": self._mape,
                "regressors": self._regressors,
                "seasonality_mode": self._seasonality_mode,
                "yearly_seasonality": self._yearly_seasonality,
                "weekly_seasonality": self._weekly_seasonality,
                "changepoint_prior_scale": self._changepoint_prior_scale,
            },
            save_dir / "model.joblib",
        )

    def load(self, path: str, version: int) -> None:
        """저장된 모델을 joblib으로 로딩.

        Args:
            path: 저장 루트 경로 (예: edupulse/model/saved/prophet)
            version: 버전 번호
        """
        model_path = Path(path) / f"v{version}" / "model.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")

        data = joblib.load(model_path)
        self._model = data["model"]
        self._mape = data.get("mape")
        self._regressors = data.get("regressors", [])
        self._seasonality_mode = data.get("seasonality_mode", "multiplicative")
        self._yearly_seasonality = data.get("yearly_seasonality", True)
        self._weekly_seasonality = data.get("weekly_seasonality", False)
        self._changepoint_prior_scale = data.get("changepoint_prior_scale", 0.05)
