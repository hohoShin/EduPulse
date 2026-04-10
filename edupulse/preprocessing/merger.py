"""데이터 병합 모듈.

내부(enrollment) + 외부(search_trends, job_postings) 데이터를 [field, date] 기준으로 병합.
신규 소스(상담, 학생 프로필, 웹 로그, 자격증 일정, 경쟁사, 계절 이벤트) 포함.
"""
import logging
import os

import pandas as pd

logger = logging.getLogger(__name__)

BINARY_FLAG_COLUMNS = ["has_cert_exam", "is_vacation", "is_exam_season", "is_semester_start"]


def merge_datasets(
    enrollment_df: pd.DataFrame,
    search_df: pd.DataFrame | None = None,
    job_df: pd.DataFrame | None = None,
    consultation_df: pd.DataFrame | None = None,
    student_profile_df: pd.DataFrame | None = None,
    web_log_df: pd.DataFrame | None = None,
    cert_exam_df: pd.DataFrame | None = None,
    competitor_df: pd.DataFrame | None = None,
    seasonal_df: pd.DataFrame | None = None,
    date_col: str = "date",
) -> pd.DataFrame:
    """내부 수강 데이터와 외부 데이터를 [field, date] 기준 left join으로 병합.

    Args:
        enrollment_df: 수강 이력 DataFrame. field, date 컬럼 필수.
        search_df: 검색 트렌드 DataFrame (optional). field, date, search_volume 필요.
        job_df: 채용 공고 DataFrame (optional). field, date, job_count 필요.
        consultation_df: 상담 로그 DataFrame (optional). field, date, consultation_count, conversion_rate 필요.
        student_profile_df: 학생 프로필 DataFrame (optional). field, date, age_20s_ratio, age_30s_ratio, age_40plus_ratio, purpose_career, purpose_hobby, purpose_cert 필요.
        web_log_df: 웹 로그 DataFrame (optional). field, date, page_views 필요.
        cert_exam_df: 자격증 시험 일정 DataFrame (optional). field, date, has_cert_exam, weeks_to_exam 필요.
        competitor_df: 경쟁사 데이터 DataFrame (optional). field, date, competitor_openings, competitor_avg_price 필요.
        seasonal_df: 계절 이벤트 DataFrame (optional). date, is_vacation, is_exam_season, is_semester_start 필요. (field 없음)
        date_col: 날짜 컬럼명 (datetime 변환용).

    Returns:
        병합된 DataFrame. 연속값 결측치는 forward fill, 이진 플래그는 0으로 채움.
    """
    merged = enrollment_df.copy()
    merged[date_col] = pd.to_datetime(merged[date_col])
    merged[date_col] = merged[date_col].dt.to_period("W").dt.start_time

    join_keys = ["field", date_col]

    if search_df is not None and not search_df.empty:
        search_df = search_df.copy()
        search_df[date_col] = pd.to_datetime(search_df[date_col])
        search_df[date_col] = search_df[date_col].dt.to_period("W").dt.start_time
        search_cols = search_df[join_keys + ["search_volume"]].copy()
        merged = merged.merge(search_cols, on=join_keys, how="left")

    if job_df is not None and not job_df.empty:
        job_df = job_df.copy()
        job_df[date_col] = pd.to_datetime(job_df[date_col])
        job_df[date_col] = job_df[date_col].dt.to_period("W").dt.start_time
        job_cols = job_df[join_keys + ["job_count"]].copy()
        merged = merged.merge(job_cols, on=join_keys, how="left")

    if consultation_df is not None and not consultation_df.empty:
        consultation_df = consultation_df.copy()
        consultation_df[date_col] = pd.to_datetime(consultation_df[date_col])
        consultation_df[date_col] = consultation_df[date_col].dt.to_period("W").dt.start_time
        consult_cols = consultation_df[join_keys + ["consultation_count", "conversion_rate"]].copy()
        merged = merged.merge(consult_cols, on=join_keys, how="left")

    if student_profile_df is not None and not student_profile_df.empty:
        student_profile_df = student_profile_df.copy()
        student_profile_df[date_col] = pd.to_datetime(student_profile_df[date_col])
        student_profile_df[date_col] = student_profile_df[date_col].dt.to_period("W").dt.start_time
        profile_cols = student_profile_df[join_keys + [
            "age_20s_ratio", "age_30s_ratio", "age_40plus_ratio",
            "purpose_career", "purpose_hobby", "purpose_cert",
        ]].copy()
        merged = merged.merge(profile_cols, on=join_keys, how="left")

    if web_log_df is not None and not web_log_df.empty:
        web_log_df = web_log_df.copy()
        web_log_df[date_col] = pd.to_datetime(web_log_df[date_col])
        web_log_df[date_col] = web_log_df[date_col].dt.to_period("W").dt.start_time
        web_cols = web_log_df[join_keys + ["page_views"]].copy()
        merged = merged.merge(web_cols, on=join_keys, how="left")

    if cert_exam_df is not None and not cert_exam_df.empty:
        cert_exam_df = cert_exam_df.copy()
        cert_exam_df[date_col] = pd.to_datetime(cert_exam_df[date_col])
        cert_exam_df[date_col] = cert_exam_df[date_col].dt.to_period("W").dt.start_time
        cert_cols = cert_exam_df[join_keys + ["has_cert_exam", "weeks_to_exam"]].copy()
        merged = merged.merge(cert_cols, on=join_keys, how="left")

    if competitor_df is not None and not competitor_df.empty:
        competitor_df = competitor_df.copy()
        competitor_df[date_col] = pd.to_datetime(competitor_df[date_col])
        competitor_df[date_col] = competitor_df[date_col].dt.to_period("W").dt.start_time
        comp_cols = competitor_df[join_keys + ["competitor_openings", "competitor_avg_price"]].copy()
        merged = merged.merge(comp_cols, on=join_keys, how="left")

    if seasonal_df is not None and not seasonal_df.empty:
        # seasonal_df: date 기준만 병합 (field 없음)
        seasonal_df = seasonal_df.copy()
        seasonal_df[date_col] = pd.to_datetime(seasonal_df[date_col])
        seasonal_df[date_col] = seasonal_df[date_col].dt.to_period("W").dt.start_time
        seasonal_cols = seasonal_df[[date_col, "is_vacation", "is_exam_season", "is_semester_start"]].copy()
        merged = merged.merge(seasonal_cols, on=date_col, how="left")

    # 분야 경계 내에서만 ffill (분야 간 데이터 누수 방지), 이진 플래그는 0으로 채움
    numeric_cols = merged.select_dtypes(include="number").columns
    continuous_cols = [c for c in numeric_cols if c not in BINARY_FLAG_COLUMNS]
    if "field" in merged.columns:
        merged[continuous_cols] = merged.groupby("field")[continuous_cols].ffill()
    else:
        merged[continuous_cols] = merged[continuous_cols].ffill()
    binary_present = [c for c in BINARY_FLAG_COLUMNS if c in merged.columns]
    merged[binary_present] = merged[binary_present].fillna(0).astype(int)

    return merged


def build_training_dataset(
    raw_internal_dir: str = "edupulse/data/raw/internal",
    raw_external_dir: str = "edupulse/data/raw/external",
    output_path: str = "edupulse/data/warehouse/training_dataset.csv",
) -> pd.DataFrame:
    """전체 파이프라인: raw 데이터 로딩 → 병합 → warehouse 저장.

    Args:
        raw_internal_dir: 내부 raw 데이터 디렉토리 경로.
        raw_external_dir: 외부 raw 데이터 디렉토리 경로.
        output_path: 최종 학습 데이터셋 저장 경로 (.csv).

    Returns:
        병합된 학습용 DataFrame.
    """
    enrollment_path = os.path.join(raw_internal_dir, "enrollment_history.csv")
    enrollment_df = pd.read_csv(enrollment_path)

    search_path = os.path.join(raw_external_dir, "search_trends.csv")
    search_df = _load_csv_safe(search_path)
    if search_df is None:
        logger.warning("[build_training_dataset] 외부 데이터 누락: %s → search_volume 컬럼 없이 진행", search_path)

    job_path = os.path.join(raw_external_dir, "job_postings.csv")
    job_df = _load_csv_safe(job_path)
    if job_df is None:
        logger.warning("[build_training_dataset] 외부 데이터 누락: %s → job_count 컬럼 없이 진행", job_path)

    # 신규 내부 소스
    consultation_df = _load_csv_safe(os.path.join(raw_internal_dir, "consultation_logs.csv"))
    student_profile_df = _load_csv_safe(os.path.join(raw_internal_dir, "student_profiles.csv"))
    web_log_df = _load_csv_safe(os.path.join(raw_internal_dir, "web_logs.csv"))

    # 신규 외부 소스
    cert_exam_df = _load_csv_safe(os.path.join(raw_external_dir, "cert_exam_schedule.csv"))
    competitor_df = _load_csv_safe(os.path.join(raw_external_dir, "competitor_data.csv"))
    seasonal_df = _load_csv_safe(os.path.join(raw_external_dir, "seasonal_events.csv"))

    merged = merge_datasets(
        enrollment_df,
        search_df=search_df,
        job_df=job_df,
        consultation_df=consultation_df,
        student_profile_df=student_profile_df,
        web_log_df=web_log_df,
        cert_exam_df=cert_exam_df,
        competitor_df=competitor_df,
        seasonal_df=seasonal_df,
    )

    from edupulse.preprocessing.cleaner import clean_data
    merged = clean_data(merged, target_col="enrollment_count")

    from edupulse.preprocessing.transformer import add_lag_features
    merged = add_lag_features(merged, target_col="enrollment_count")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged.to_csv(output_path, index=False)

    return merged


def _load_csv_safe(path: str) -> pd.DataFrame | None:
    """CSV 파일이 존재하면 로딩, 없으면 None 반환."""
    if os.path.exists(path):
        return pd.read_csv(path)
    return None
