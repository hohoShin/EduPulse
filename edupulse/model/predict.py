"""수요 예측 진입점 — API에서 호출.

Usage:
    from edupulse.model.predict import predict_demand
    result = predict_demand('Python 웹개발', '2026-05-01', 'coding')
    result = predict_demand('Python 웹개발', '2026-05-01', 'coding', model_name='ensemble')
"""
import logging
import math
import os

import numpy as np
import pandas as pd

from edupulse.model.base import BaseForecaster, PredictionResult
from edupulse.model.xgboost_model import FEATURE_COLUMNS

logger = logging.getLogger(__name__)

# 분야 → 인코딩 값 (알파벳 순, transformer.py의 astype("category").cat.codes와 동일)
FIELD_ENCODING = {"art": 0, "coding": 1, "game": 2, "security": 3}

# 데이터 파일 경로
_ENROLLMENT_PATH = "edupulse/data/raw/internal/enrollment_history.csv"
_SEARCH_TRENDS_PATH = "edupulse/data/raw/external/search_trends.csv"
_JOB_POSTINGS_PATH = "edupulse/data/raw/external/job_postings.csv"

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

    실제 CSV 데이터에서 해당 분야/시점의 피처를 조립한다.
    - enrollment_history.csv → lag_1w~8w, rolling_mean_4w
    - search_trends.csv → search_volume
    - job_postings.csv → job_count
    - 날짜 → month_sin, month_cos
    - 분야 → field_encoded

    Args:
        course_name: 과정명
        start_date: 시작일 (YYYY-MM-DD)
        field: 분야 ('coding', 'security', 'game', 'art')

    Returns:
        FEATURE_COLUMNS에 해당하는 1행 DataFrame
    """
    import datetime

    dt = datetime.date.fromisoformat(start_date)
    target_date = pd.Timestamp(start_date)

    # --- 1) month_sin, month_cos ---
    month_rad = dt.month / 12.0 * 2 * math.pi
    month_sin = math.sin(month_rad)
    month_cos = math.cos(month_rad)

    # --- 2) field_encoded ---
    field_encoded = float(FIELD_ENCODING.get(field, 0))

    # --- 3) lag features + rolling_mean (enrollment_history.csv) ---
    lag_1w, lag_2w, lag_4w, lag_8w, rolling_mean_4w = 0.0, 0.0, 0.0, 0.0, 0.0
    if os.path.exists(_ENROLLMENT_PATH):
        try:
            enroll_df = pd.read_csv(_ENROLLMENT_PATH)
            enroll_df["date"] = pd.to_datetime(enroll_df["date"])
            field_enroll = (
                enroll_df[enroll_df["field"] == field]
                .sort_values("date")
            )
            # target_date 이전 데이터만 사용
            prior = field_enroll[field_enroll["date"] < target_date]
            if len(prior) >= 1:
                lag_1w = float(prior.iloc[-1]["enrollment_count"])
            if len(prior) >= 2:
                lag_2w = float(prior.iloc[-2]["enrollment_count"])
            if len(prior) >= 4:
                lag_4w = float(prior.iloc[-4]["enrollment_count"])
            if len(prior) >= 8:
                lag_8w = float(prior.iloc[-8]["enrollment_count"])
            # rolling_mean_4w: 최근 4주 평균
            if len(prior) >= 4:
                rolling_mean_4w = float(prior.iloc[-4:]["enrollment_count"].mean())
            elif len(prior) >= 1:
                rolling_mean_4w = float(prior.tail(4)["enrollment_count"].mean())
        except Exception as e:
            logger.warning("등록 이력 로딩 실패, lag=0 사용: %s", e)

    # --- 4) search_volume (search_trends.csv) ---
    search_volume = 0.0
    if os.path.exists(_SEARCH_TRENDS_PATH):
        try:
            search_df = pd.read_csv(_SEARCH_TRENDS_PATH)
            search_df["date"] = pd.to_datetime(search_df["date"])
            field_search = search_df[search_df["field"] == field].sort_values("date")
            prior_search = field_search[field_search["date"] < target_date]
            if len(prior_search) >= 1:
                search_volume = float(prior_search.iloc[-1]["search_volume"])
        except Exception as e:
            logger.warning("검색 트렌드 로딩 실패, search_volume=0 사용: %s", e)

    # --- 5) job_count (job_postings.csv) ---
    job_count = 0.0
    if os.path.exists(_JOB_POSTINGS_PATH):
        try:
            job_df = pd.read_csv(_JOB_POSTINGS_PATH)
            job_df["date"] = pd.to_datetime(job_df["date"])
            field_jobs = job_df[job_df["field"] == field].sort_values("date")
            prior_jobs = field_jobs[field_jobs["date"] < target_date]
            if len(prior_jobs) >= 1:
                job_count = float(prior_jobs.iloc[-1]["job_count"])
        except Exception as e:
            logger.warning("채용 공고 로딩 실패, job_count=0 사용: %s", e)

    # --- 조립 ---
    row = {
        "date": start_date,
        "lag_1w": lag_1w,
        "lag_2w": lag_2w,
        "lag_4w": lag_4w,
        "lag_8w": lag_8w,
        "rolling_mean_4w": rolling_mean_4w,
        "month_sin": month_sin,
        "month_cos": month_cos,
        "search_volume": search_volume,
        "job_count": job_count,
        "field_encoded": field_encoded,
    }

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
