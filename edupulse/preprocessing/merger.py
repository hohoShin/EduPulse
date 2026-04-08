"""데이터 병합 모듈.

내부(enrollment) + 외부(search_trends, job_postings) 데이터를 [field, date] 기준으로 병합.
"""
import os
import pandas as pd


def merge_datasets(
    enrollment_df: pd.DataFrame,
    search_df: pd.DataFrame | None = None,
    job_df: pd.DataFrame | None = None,
    date_col: str = "date",
) -> pd.DataFrame:
    """내부 수강 데이터와 외부 데이터를 [field, date] 기준 left join으로 병합.

    Args:
        enrollment_df: 수강 이력 DataFrame. field, date 컬럼 필수.
        search_df: 검색 트렌드 DataFrame (optional). field, date, search_volume 필요.
        job_df: 채용 공고 DataFrame (optional). field, date, job_count 필요.
        date_col: 날짜 컬럼명 (datetime 변환용).

    Returns:
        병합된 DataFrame. 결측치는 forward fill 처리.
    """
    merged = enrollment_df.copy()
    merged[date_col] = pd.to_datetime(merged[date_col])
    # 주간 정렬: 날짜를 주 시작일(월요일)로 정규화
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

    # 병합 후 결측치 forward fill
    numeric_cols = merged.select_dtypes(include="number").columns
    merged[numeric_cols] = merged[numeric_cols].ffill()

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
    # 내부 데이터 로딩
    enrollment_path = os.path.join(raw_internal_dir, "enrollment_history.csv")
    enrollment_df = pd.read_csv(enrollment_path)

    # 외부 데이터 로딩 (파일 없으면 빈 DataFrame)
    search_df = _load_csv_safe(os.path.join(raw_external_dir, "search_trends.csv"))
    job_df = _load_csv_safe(os.path.join(raw_external_dir, "job_postings.csv"))

    merged = merge_datasets(enrollment_df, search_df, job_df)

    # 전처리: 결측치 보간 + 이상치 클리핑
    from edupulse.preprocessing.cleaner import clean_data
    merged = clean_data(merged, target_col="enrollment_count")

    # lag feature 추가 (XGBoost 피처 생성)
    from edupulse.preprocessing.transformer import add_lag_features
    merged = add_lag_features(merged, target_col="enrollment_count")

    # warehouse 디렉토리 생성 후 저장
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged.to_csv(output_path, index=False)

    return merged


def _load_csv_safe(path: str) -> pd.DataFrame | None:
    """CSV 파일이 존재하면 로딩, 없으면 None 반환."""
    if os.path.exists(path):
        return pd.read_csv(path)
    return None
