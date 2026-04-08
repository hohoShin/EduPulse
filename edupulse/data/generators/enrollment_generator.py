"""수강 이력 합성 데이터 생성기.

주간 단위 계절성과 연간 성장 트렌드를 반영한 등록 인원 데이터를 생성한다.
"""
import numpy as np
import pandas as pd


# 분야별 주간 기본 수요
BASE_WEEKLY_ENROLLMENT = {
    "coding": 4,
    "security": 3,
    "game": 3,
    "art": 2,
}

# 월별 계절성 보정값 (주간 단위에 맞춰 축소)
WEEKLY_SEASONAL_FACTOR = {
    1: +1.5,   # 1월: 방학
    2: +0.8,   # 2월: 방학 말
    3: -1.2,   # 3월: 학기 시작
    4: -1.0,   # 4월: 학기 중
    5: -0.8,   # 5월: 학기 중
    6:  0.0,   # 6월: 중립
    7: +2.0,   # 7월: 여름방학
    8: +1.8,   # 8월: 여름방학
    9: -1.0,   # 9월: 2학기 시작
    10: -1.0,  # 10월: 학기 중
    11: -0.8,  # 11월: 학기 중
    12: +0.5,  # 12월: 연말
}


def _compute_trend(year: int) -> float:
    """연도별 트렌드 승수 계산. 거시 이벤트를 반영한다.

    기간별 트렌드:
        2018-2019: 연 3% 복리 성장 (안정적 성장기)
        2020:      -15% 급감 (코로나 초기 충격)
        2021-2022: 연 10% 급증 (온라인 교육 붐)
        2023-2025: 연 5% 성장 (정상화)

    Args:
        year: 대상 연도

    Returns:
        해당 연도의 트렌드 승수 (2018년 = 1.0 기준)
    """
    if year <= 2019:
        return 1.0 * (1.03 ** (year - 2018))
    elif year == 2020:
        # 2019 수준에서 -15% 충격
        base_2019 = 1.0 * (1.03 ** 1)  # ~1.03
        return base_2019 * 0.85
    elif year <= 2022:
        # 코로나 급감에서 연 10% 회복
        base_2020 = 1.0 * (1.03 ** 1) * 0.85  # ~0.8755
        return base_2020 * (1.10 ** (year - 2020))
    else:
        # 2022 수준에서 연 5% 정상 성장
        base_2022 = 1.0 * (1.03 ** 1) * 0.85 * (1.10 ** 2)  # ~1.0593
        return base_2022 * (1.05 ** (year - 2022))


def generate_enrollment_history(
    n_years: int = 8,
    start_year: int = 2018,
    seed: int = 42,
) -> pd.DataFrame:
    """주간 단위 수강 이력 합성 데이터 생성.

    Args:
        n_years: 생성할 연도 수 (기본 8년 = ~418주/분야)
        start_year: 시작 연도
        seed: 재현성을 위한 난수 시드

    Returns:
        DataFrame with columns: date, field, cohort, enrollment_count, ds, y
    """
    rng = np.random.default_rng(seed)
    fields = list(BASE_WEEKLY_ENROLLMENT.keys())

    # 주간 날짜 그리드 생성
    start_date = f"{start_year}-01-04"  # 첫 번째 월요일
    end_date = f"{start_year + n_years - 1}-12-31"
    weeks = pd.date_range(start=start_date, end=end_date, freq="W-MON")

    records = []
    for field in fields:
        base = BASE_WEEKLY_ENROLLMENT[field]
        for week_index, week_date in enumerate(weeks):
            trend = _compute_trend(week_date.year)

            month = week_date.month
            seasonal = WEEKLY_SEASONAL_FACTOR.get(month, 0.0)
            noise = rng.normal(0, 0.6)

            enrollment = int(round(max(0, base * trend + seasonal + noise)))

            # cohort 파생: 8주 단위 기수
            cohort = week_index // 8 + 1

            date_str = week_date.strftime("%Y-%m-%d")
            records.append({
                "date": date_str,
                "field": field,
                "cohort": cohort,
                "enrollment_count": enrollment,
                # Prophet 호환 컬럼
                "ds": date_str,
                "y": enrollment,
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["field", "date"]).reset_index(drop=True)
    return df
