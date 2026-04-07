"""수강 이력 합성 데이터 생성기.

계절성과 트렌드를 반영한 기수별 등록 인원 데이터를 생성한다.
"""
import numpy as np
import pandas as pd
from datetime import date, timedelta


# 분야별 기본 수요 (~20% High / ~50% Mid / ~30% Low 목표 분포)
BASE_ENROLLMENT = {
    "coding": 20,
    "security": 17,
    "game": 19,
    "art": 14,
}

# 월별 계절성 보정값
SEASONAL_FACTOR = {
    1: +7,   # 1월: 방학
    2: +3,   # 2월: 방학 말
    3: -5,   # 3월: 학기 시작
    4: -5,   # 4월: 학기 중
    5: -4,   # 5월: 학기 중
    6:  0,   # 6월: 중립
    7: +8,   # 7월: 여름방학
    8: +7,   # 8월: 여름방학
    9: -4,   # 9월: 2학기 시작
    10: -4,  # 10월: 학기 중
    11: -3,  # 11월: 학기 중
    12: +2,  # 12월: 연말
}


def generate_enrollment_history(
    n_cohorts: int = 8,
    start_year: int = 2024,
    seed: int = 42,
) -> pd.DataFrame:
    """기수별 수강 이력 합성 데이터 생성.

    Args:
        n_cohorts: 분야별 기수 수 (기본 8기수 = 약 2년치)
        start_year: 시작 연도
        seed: 재현성을 위한 난수 시드

    Returns:
        DataFrame with columns: date, field, cohort, enrollment_count, ds, y
    """
    rng = np.random.default_rng(seed)
    fields = list(BASE_ENROLLMENT.keys())

    records = []
    for field in fields:
        base = BASE_ENROLLMENT[field]
        # 각 분야의 기수 시작일: 약 2개월 간격
        for cohort_idx in range(n_cohorts):
            # 시작일 계산: 2개월 간격으로 분산
            days_offset = cohort_idx * 60 + rng.integers(0, 14)
            cohort_date = date(start_year, 1, 1) + timedelta(days=int(days_offset))

            month = cohort_date.month
            seasonal = SEASONAL_FACTOR.get(month, 0)
            noise = rng.normal(0, 5)

            enrollment = int(round(max(1, base + seasonal + noise)))

            date_str = cohort_date.strftime("%Y-%m-%d")
            records.append({
                "date": date_str,
                "field": field,
                "cohort": cohort_idx + 1,
                "enrollment_count": enrollment,
                # Prophet 호환 컬럼
                "ds": date_str,
                "y": enrollment,
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["field", "cohort"]).reset_index(drop=True)
    return df
