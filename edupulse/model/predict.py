"""수요 예측 진입점 — API에서 호출.

Usage:
    from edupulse.model.predict import predict_demand
    result = predict_demand('Python 웹개발', '2026-05-01', 'coding')
    result = predict_demand('Python 웹개발', '2026-05-01', 'coding', model_name='ensemble')
"""
import logging
import os
import threading

import numpy as np
import pandas as pd

from edupulse.constants import (
    ENROLLMENT_PATH as _ENROLLMENT_PATH,
    SEARCH_TRENDS_PATH as _SEARCH_TRENDS_PATH,
    JOB_POSTINGS_PATH as _JOB_POSTINGS_PATH,
    CONSULTATION_PATH as _CONSULTATION_PATH,
    STUDENT_PROFILES_PATH as _STUDENT_PROFILES_PATH,
    WEB_LOGS_PATH as _WEB_LOGS_PATH,
    CERT_EXAM_PATH as _CERT_EXAM_PATH,
    COMPETITOR_PATH as _COMPETITOR_PATH,
    SEASONAL_PATH as _SEASONAL_PATH,
)
from edupulse.model.base import BaseForecaster, PredictionResult
from edupulse.model.xgboost_model import FEATURE_COLUMNS
from edupulse.preprocessing.transformer import compute_field_encoding, compute_month_encoding

logger = logging.getLogger(__name__)

# dependencies.py에서도 이 값을 참조한다.
MODEL_VERSION = 1

_model_cache: dict[str, BaseForecaster] = {}
_model_mtime: dict[str, float] = {}
_cache_lock = threading.Lock()

_data_cache: dict[str, pd.DataFrame] = {}
_data_cache_lock = threading.Lock()

_MODEL_PATHS = {
    "xgboost": "edupulse/model/saved/xgboost",
    "prophet": "edupulse/model/saved/prophet",
    "lstm": "edupulse/model/saved/lstm",
}


def _get_model_mtime(model_name: str, version: int) -> float:
    """모델 파일의 mtime 반환. 파일 미존재 시 0.0."""
    from pathlib import Path

    base = _MODEL_PATHS.get(model_name, "")
    if not base:
        return 0.0
    model_dir = Path(base) / f"v{version}"
    if not model_dir.exists():
        return 0.0
    mtimes = [f.stat().st_mtime for f in model_dir.iterdir() if f.is_file()]
    return max(mtimes) if mtimes else 0.0


def clear_model_cache() -> None:
    """모델 캐시 및 데이터 캐시 초기화. 테스트 또는 리로딩 시 사용."""
    with _cache_lock:
        _model_cache.clear()
        _model_mtime.clear()
    with _data_cache_lock:
        _data_cache.clear()


def load_model(model_name: str, version: int = MODEL_VERSION) -> BaseForecaster:
    """모델 캐시에서 반환하거나 새로 로딩 (스레드 안전).

    retrain으로 모델 파일이 갱신되면 mtime 비교를 통해 자동 리로딩한다.
    I/O(모델 파일 로딩)는 잠금 바깥에서 수행하여 동시성을 보장한다.

    Args:
        model_name: 모델 이름 ('xgboost', 'prophet', 'lstm', 'ensemble')
        version: 모델 버전

    Returns:
        로딩된 BaseForecaster 인스턴스
    """
    key = f"{model_name}_v{version}"

    with _cache_lock:
        if key in _model_cache:
            current_mtime = _get_model_mtime(model_name, version)
            if current_mtime <= _model_mtime.get(key, 0.0):
                return _model_cache[key]
            logger.info("모델 파일 갱신 감지: %s (리로딩)", key)
            del _model_cache[key]

    # 잠금 바깥에서 I/O 수행 (동시 로딩 허용)
    model = _do_load_model(model_name, version)
    current_mtime = _get_model_mtime(model_name, version)

    with _cache_lock:
        if key not in _model_cache:
            _model_cache[key] = model
            _model_mtime[key] = current_mtime
        return _model_cache[key]


def _do_load_model(model_name: str, version: int) -> BaseForecaster:
    """모델 인스턴스를 생성하고 디스크에서 로딩. 잠금 없이 호출된다."""
    if model_name == "xgboost":
        from edupulse.model.xgboost_model import XGBoostForecaster

        model: BaseForecaster = XGBoostForecaster()
        model.load("edupulse/model/saved/xgboost", version=version)

    elif model_name == "prophet":
        try:
            from edupulse.model.prophet_model import ProphetForecaster

            model = ProphetForecaster()
            model.load("edupulse/model/saved/prophet", version=version)
        except ImportError as exc:
            raise ImportError("Prophet 미설치. pip install prophet") from exc

    elif model_name == "lstm":
        try:
            from edupulse.model.lstm_model import LSTMForecaster

            model = LSTMForecaster()
            model.load("edupulse/model/saved/lstm", version=version)
        except ImportError as exc:
            raise ImportError("PyTorch 미설치. pip install torch") from exc

    elif model_name == "ensemble":
        model = _load_ensemble(version=version)

    else:
        raise ValueError(f"Unknown model_name: {model_name}")

    return model


def _load_ensemble(version: int = MODEL_VERSION) -> "BaseForecaster":
    """가용한 모델을 모두 로딩하여 EnsembleForecaster 반환.

    각 모델 로딩 실패 시 조용히 건너뛴다. 1개 이상 로딩되면 앙상블 반환.

    Args:
        version: 모델 버전

    Returns:
        EnsembleForecaster 인스턴스
    """
    from edupulse.model.ensemble import EnsembleForecaster

    ensemble = EnsembleForecaster()

    try:
        from edupulse.model.xgboost_model import XGBoostForecaster

        xgb = XGBoostForecaster()
        xgb.load("edupulse/model/saved/xgboost", version=version)
        ensemble.add_model("xgboost", xgb)
    except Exception as exc:
        logger.warning("앙상블: XGBoost 로딩 실패 — %s", exc)

    try:
        from edupulse.model.prophet_model import ProphetForecaster

        prophet = ProphetForecaster()
        prophet.load("edupulse/model/saved/prophet", version=version)
        ensemble.add_model("prophet", prophet)
    except Exception as exc:
        logger.warning("앙상블: Prophet 로딩 실패 — %s", exc)

    try:
        from edupulse.model.lstm_model import LSTMForecaster

        lstm = LSTMForecaster()
        lstm.load("edupulse/model/saved/lstm", version=version)
        ensemble.add_model("lstm", lstm)
    except Exception as exc:
        logger.warning("앙상블: LSTM 로딩 실패 — %s", exc)

    if ensemble.model_count == 0:
        raise RuntimeError("앙상블 로딩 실패: 사용 가능한 모델이 없습니다.")

    return ensemble


def load_csv_cached(path: str) -> pd.DataFrame | None:
    """CSV를 캐시에서 반환하거나 디스크에서 로딩 (스레드 안전).

    Args:
        path: CSV 파일 경로

    Returns:
        DataFrame 또는 파일 미존재 시 None
    """
    with _data_cache_lock:
        if path in _data_cache:
            return _data_cache[path]
        if os.path.exists(path):
            _data_cache[path] = pd.read_csv(path)
            return _data_cache[path]
        return None  # 파일 생성 시 자동 감지를 위해 캐시하지 않음


def build_features(course_name: str, start_date: str, field: str) -> pd.DataFrame:
    """API raw 입력 → feature DataFrame 변환.

    실제 CSV 데이터에서 해당 분야/시점의 피처를 조립한다.
    - enrollment_history.csv → lag_1w~8w, rolling_mean_4w
    - search_trends.csv → search_volume
    - job_postings.csv → job_count
    - 날짜 → month_sin, month_cos
    - 분야 → field_encoded

    Args:
        course_name: 과정명 (현재 모델에서 미사용 — 향후 과정별 세분화 시 활용 예정)
        start_date: 시작일 (YYYY-MM-DD)
        field: 분야 ('coding', 'security', 'game', 'art')

    Returns:
        FEATURE_COLUMNS에 해당하는 1행 DataFrame
    """
    import datetime

    dt = datetime.date.fromisoformat(start_date)
    target_date = pd.Timestamp(start_date)

    from edupulse.constants import FIELD_ENCODING

    if field not in FIELD_ENCODING:
        raise ValueError(f"미등록 분야: '{field}'. 허용: {list(FIELD_ENCODING.keys())}")

    month_sin, month_cos = compute_month_encoding(dt.month)
    field_encoded = compute_field_encoding(field)

    # lag features + rolling_mean (enrollment_history.csv)
    # 학습 파이프라인(merger.py)과 동일하게 연속 주간 시계열(asfreq)로 정렬 후
    # 인덱스 기반 shift(N) = 정확히 N주 전 보장 (결측 주 있어도 일치)
    target_date_aligned = pd.Timestamp(start_date).to_period("W").start_time
    lag_1w, lag_2w, lag_4w, lag_8w, rolling_mean_4w = 0.0, 0.0, 0.0, 0.0, 0.0
    enroll_raw = load_csv_cached(_ENROLLMENT_PATH)
    if enroll_raw is not None:
        try:
            enroll_df = enroll_raw.copy()
            enroll_df["date"] = pd.to_datetime(enroll_df["date"]).dt.to_period("W").dt.start_time
            # 분야별 주간 집계 후 연속 시계열로 변환 (누락 주 = ffill)
            field_series = (
                enroll_df[enroll_df["field"] == field]
                .groupby("date")["enrollment_count"]
                .sum()
                .asfreq("W-MON")
                .ffill()
            )
            # target_date 이전 인덱스에서 lag 계산
            prior_idx = field_series.index[field_series.index < target_date_aligned]
            idx = len(prior_idx)
            if idx >= 1:
                lag_1w = float(field_series.iloc[idx - 1])
            if idx >= 2:
                lag_2w = float(field_series.iloc[idx - 2])
            if idx >= 4:
                lag_4w = float(field_series.iloc[idx - 4])
            if idx >= 8:
                lag_8w = float(field_series.iloc[idx - 8])
            if idx >= 4:
                rolling_mean_4w = float(field_series.iloc[idx - 4:idx].mean())
            elif idx >= 1:
                rolling_mean_4w = float(field_series.iloc[:idx].mean())
        except Exception as e:
            logger.warning("등록 이력 로딩 실패, lag=0 사용: %s", e)

    search_volume = 0.0
    search_raw = load_csv_cached(_SEARCH_TRENDS_PATH)
    if search_raw is not None:
        try:
            search_df = search_raw.copy()
            search_df["date"] = pd.to_datetime(search_df["date"]).dt.to_period("W").dt.start_time
            field_search = search_df[search_df["field"] == field].sort_values("date")
            prior_search = field_search[field_search["date"] < target_date_aligned]
            if len(prior_search) >= 1:
                search_volume = float(prior_search.iloc[-1]["search_volume"])
        except Exception as e:
            logger.warning("검색 트렌드 로딩 실패, search_volume=0 사용: %s", e)

    job_count = 0.0
    job_raw = load_csv_cached(_JOB_POSTINGS_PATH)
    if job_raw is not None:
        try:
            job_df = job_raw.copy()
            job_df["date"] = pd.to_datetime(job_df["date"]).dt.to_period("W").dt.start_time
            field_jobs = job_df[job_df["field"] == field].sort_values("date")
            prior_jobs = field_jobs[field_jobs["date"] < target_date_aligned]
            if len(prior_jobs) >= 1:
                job_count = float(prior_jobs.iloc[-1]["job_count"])
        except Exception as e:
            logger.warning("채용 공고 로딩 실패, job_count=0 사용: %s", e)

    # --- 6) consultation_count, conversion_rate (consultation_logs.csv) ---
    consultation_count = 0.0
    conversion_rate = 0.0
    if os.path.exists(_CONSULTATION_PATH):
        try:
            consult_df = pd.read_csv(_CONSULTATION_PATH)
            consult_df["date"] = pd.to_datetime(consult_df["date"])
            field_consult = consult_df[consult_df["field"] == field].sort_values("date")
            prior_consult = field_consult[field_consult["date"] < target_date]
            if len(prior_consult) >= 1:
                consultation_count = float(prior_consult.iloc[-1]["consultation_count"])
                conversion_rate = float(prior_consult.iloc[-1]["conversion_rate"])
        except Exception as e:
            logger.warning("상담 로그 로딩 실패, consultation=0 사용: %s", e)

    # --- 7) age_group_diversity (student_profiles.csv) ---
    age_group_diversity = 0.0
    if os.path.exists(_STUDENT_PROFILES_PATH):
        try:
            profile_df = pd.read_csv(_STUDENT_PROFILES_PATH)
            profile_df["date"] = pd.to_datetime(profile_df["date"])
            field_profile = profile_df[profile_df["field"] == field].sort_values("date")
            prior_profile = field_profile[field_profile["date"] < target_date]
            if len(prior_profile) >= 1:
                row_p = prior_profile.iloc[-1]
                age_cols = [row_p.get("age_20s_ratio", 0.0), row_p.get("age_30s_ratio", 0.0), row_p.get("age_40plus_ratio", 0.0)]
                import numpy as _np
                eps = 1e-10
                age_arr = _np.array(age_cols, dtype=float)
                age_group_diversity = float(-_np.sum(age_arr * _np.log(age_arr + eps)))
        except Exception as e:
            logger.warning("학생 프로필 로딩 실패, age_group_diversity=0 사용: %s", e)

    # --- 8) page_views, cart_abandon_rate (web_logs.csv) ---
    page_views = 0.0
    cart_abandon_rate = 0.0
    if os.path.exists(_WEB_LOGS_PATH):
        try:
            web_df = pd.read_csv(_WEB_LOGS_PATH)
            web_df["date"] = pd.to_datetime(web_df["date"])
            field_web = web_df[web_df["field"] == field].sort_values("date")
            prior_web = field_web[field_web["date"] < target_date]
            if len(prior_web) >= 1:
                page_views = float(prior_web.iloc[-1]["page_views"])
                cart_abandon_rate = float(prior_web.iloc[-1]["cart_abandon_rate"])
        except Exception as e:
            logger.warning("웹 로그 로딩 실패, page_views=0 사용: %s", e)

    # --- 9) has_cert_exam, weeks_to_exam (cert_exam_schedule.csv) ---
    has_cert_exam = 0
    weeks_to_exam = 0.0
    if os.path.exists(_CERT_EXAM_PATH):
        try:
            cert_df = pd.read_csv(_CERT_EXAM_PATH)
            cert_df["date"] = pd.to_datetime(cert_df["date"])
            field_cert = cert_df[cert_df["field"] == field].sort_values("date")
            prior_cert = field_cert[field_cert["date"] < target_date]
            if len(prior_cert) >= 1:
                has_cert_exam = int(prior_cert.iloc[-1]["has_cert_exam"])
                weeks_to_exam = float(prior_cert.iloc[-1]["weeks_to_exam"])
        except Exception as e:
            logger.warning("자격증 일정 로딩 실패, cert=0 사용: %s", e)

    # --- 10) competitor_openings, competitor_avg_price (competitor_data.csv) ---
    competitor_openings = 0.0
    competitor_avg_price = 0.0
    if os.path.exists(_COMPETITOR_PATH):
        try:
            comp_df = pd.read_csv(_COMPETITOR_PATH)
            comp_df["date"] = pd.to_datetime(comp_df["date"])
            field_comp = comp_df[comp_df["field"] == field].sort_values("date")
            prior_comp = field_comp[field_comp["date"] < target_date]
            if len(prior_comp) >= 1:
                competitor_openings = float(prior_comp.iloc[-1]["competitor_openings"])
                competitor_avg_price = float(prior_comp.iloc[-1]["competitor_avg_price"])
        except Exception as e:
            logger.warning("경쟁사 데이터 로딩 실패, competitor=0 사용: %s", e)

    # --- 11) is_vacation, is_exam_season, is_semester_start (seasonal_events.csv) ---
    is_vacation = 0
    is_exam_season = 0
    is_semester_start = 0
    if os.path.exists(_SEASONAL_PATH):
        try:
            seasonal_df = pd.read_csv(_SEASONAL_PATH)
            seasonal_df["date"] = pd.to_datetime(seasonal_df["date"])
            prior_seasonal = seasonal_df[seasonal_df["date"] < target_date].sort_values("date")
            if len(prior_seasonal) >= 1:
                is_vacation = int(prior_seasonal.iloc[-1]["is_vacation"])
                is_exam_season = int(prior_seasonal.iloc[-1]["is_exam_season"])
                is_semester_start = int(prior_seasonal.iloc[-1]["is_semester_start"])
        except Exception as e:
            logger.warning("계절 이벤트 로딩 실패, seasonal=0 사용: %s", e)

    # --- 조립 ---
    row = {
        "date": start_date,
        "field": field,
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
        "consultation_count": consultation_count,
        "conversion_rate": conversion_rate,
        "page_views": page_views,
        "cart_abandon_rate": cart_abandon_rate,
        "age_group_diversity": age_group_diversity,
        "has_cert_exam": has_cert_exam,
        "weeks_to_exam": weeks_to_exam,
        "competitor_openings": competitor_openings,
        "competitor_avg_price": competitor_avg_price,
        "is_vacation": is_vacation,
        "is_exam_season": is_exam_season,
        "is_semester_start": is_semester_start,
    }

    return pd.DataFrame([row])


def predict_demand(
    course_name: str,
    start_date: str,
    field: str,
    model_name: str = "ensemble",
    version: int = 2,
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
    model = load_model(model_name, version)
    features = build_features(course_name, start_date, field)
    return model.predict(features)
