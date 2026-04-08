"""외부 지표 합성 데이터 생성기.

수강 이력 기반으로 검색 트렌드와 채용 공고 데이터를 합성한다.
- 검색량: 등록 수 2-4주 선행 (lag)
- 채용 공고: 분야별 상관 계수 적용
"""
import numpy as np
import pandas as pd
from datetime import timedelta


# 분야별 검색량 상관 계수
SEARCH_CORRELATION = {
    "coding": 1.8,
    "security": 1.5,
    "game": 1.6,
    "art": 1.2,
}

# 분야별 채용 공고 상관 계수
JOB_CORRELATION = {
    "coding": 2.5,
    "security": 3.0,
    "game": 1.8,
    "art": 1.0,
}


def generate_search_trends(
    enrollment_df: pd.DataFrame,
    seed: int = 42,
) -> pd.DataFrame:
    """검색 트렌드 합성 데이터 생성.

    enrollment_df의 [field, date] 그리드를 재사용하여 주간 검색량을 생성한다.
    검색량은 등록 수에 2-4주 선행하는 상관관계를 반영한다.

    Args:
        enrollment_df: generate_enrollment_history() 결과 DataFrame
        seed: 난수 시드

    Returns:
        DataFrame with columns: date, field, search_volume, ds, y
    """
    rng = np.random.default_rng(seed)
    records = []

    for field in enrollment_df["field"].unique():
        field_df = enrollment_df[enrollment_df["field"] == field].sort_values("date")
        enrollments = field_df["enrollment_count"].values
        dates = field_df["date"].values

        for i, (dt, enrollment) in enumerate(zip(dates, enrollments)):
            # 2-4주 후의 enrollment을 기반으로 현재 검색량 생성
            future_idx = min(i + rng.integers(2, 5), len(enrollments) - 1)
            future_enrollment = enrollments[future_idx]

            correlation = SEARCH_CORRELATION.get(field, 1.5)
            noise = rng.normal(0, 1.5)
            search_volume = int(round(max(1, future_enrollment * correlation + noise)))

            dt_ts = pd.Timestamp(dt)
            date_str = dt_ts.strftime("%Y-%m-%d")
            records.append({
                "date": date_str,
                "field": field,
                "search_volume": search_volume,
                # Prophet 호환 컬럼
                "ds": date_str,
                "y": search_volume,
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["field", "date"]).reset_index(drop=True)
    return df


def generate_job_postings(
    enrollment_df: pd.DataFrame,
    seed: int = 43,
) -> pd.DataFrame:
    """채용 공고 합성 데이터 생성.

    enrollment_df의 [field, date] 그리드를 재사용하여 주간 채용 공고 수를 생성한다.

    Args:
        enrollment_df: generate_enrollment_history() 결과 DataFrame
        seed: 난수 시드

    Returns:
        DataFrame with columns: date, field, job_count, ds, y
    """
    rng = np.random.default_rng(seed)
    records = []

    for _, row in enrollment_df.iterrows():
        field = row["field"]
        enrollment = row["enrollment_count"]
        cohort_date = pd.Timestamp(row["date"])

        correlation = JOB_CORRELATION.get(field, 1.5)
        noise = rng.normal(0, 2.0)
        job_count = int(round(max(0, enrollment * correlation + noise)))

        date_str = cohort_date.strftime("%Y-%m-%d")
        records.append({
            "date": date_str,
            "field": field,
            "job_count": job_count,
            # Prophet 호환 컬럼
            "ds": date_str,
            "y": job_count,
        })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["field", "date"]).reset_index(drop=True)
    return df
