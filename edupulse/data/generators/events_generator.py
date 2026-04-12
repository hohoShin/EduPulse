"""이벤트 및 외부 환경 합성 데이터 생성기.

자격증 시험 일정, 경쟁 학원 데이터, 계절성 이벤트를 생성한다.
- 자격증 일정: 캘린더 기반 결정론적 생성
- 경쟁 학원: 수강 이력 기반 합성
- 계절성 이벤트: 캘린더 기반 결정론적 생성
"""
import numpy as np
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta


# 분야별 자격증 시험 월 (실제 시험 일정 근사)
# 정보처리기사: 3월, 5월, 8월 / 정보보안기사: 3월, 9월
CERT_EXAM_MONTHS = {
    "coding":   [3, 5, 8],
    "security": [3, 9],
    "game":     [6],
    "art":      [5, 11],
}

# 분야별 경쟁 학원 개강 상관 계수
COMP_RATIO = {
    "coding": 1.2,
    "security": 0.8,
    "game": 0.6,
    "art": 0.5,
}

# 분야별 경쟁 학원 기준 수강료 (원)
BASE_PRICE = {
    "coding": 500000,
    "security": 600000,
    "game": 450000,
    "art": 400000,
}


def _weeks_to_next_exam(current_date: date, field: str) -> int:
    """다음 자격증 시험까지 남은 주 수 계산.

    각 분야의 시험 날짜는 해당 월 15일로 설정한다.
    current_date 이후 가장 가까운 시험일을 탐색하며 최대 26주로 제한한다.

    Args:
        current_date: 기준 날짜
        field: 분야명

    Returns:
        다음 시험까지 남은 주 수 (최대 26)
    """
    exam_months = sorted(CERT_EXAM_MONTHS[field])

    # 현재 연도 및 다음 연도 시험일 목록 생성
    candidates = []
    for year_offset in range(2):
        target_year = current_date.year + year_offset
        for month in exam_months:
            exam_date = date(target_year, month, 15)
            if exam_date >= current_date:
                candidates.append(exam_date)

    if not candidates:
        return 26

    next_exam = min(candidates)
    weeks = (next_exam - current_date).days // 7
    return min(weeks, 26)


def generate_cert_exam_schedule(
    start_year: int = 2018,
    n_years: int | None = None,
    seed: int = 47,
) -> pd.DataFrame:
    """자격증 시험 일정 합성 데이터 생성.

    분야별 자격증 시험 월에 기반하여 주간 단위로 has_cert_exam 플래그와
    다음 시험까지 남은 주 수를 생성한다. 결정론적 출력으로 seed 무관하게
    동일한 결과를 반환한다.

    Args:
        start_year: 시작 연도
        n_years: 생성할 연도 수. None이면 현재 연도까지 자동 계산.
        seed: API 일관성을 위한 시드 (출력에 영향 없음)

    Returns:
        DataFrame with columns: date, field, has_cert_exam, weeks_to_exam, ds, y
    """
    if n_years is None:
        from edupulse.data.generators.enrollment_generator import _default_n_years
        n_years = _default_n_years(start_year)

    start_date = date(start_year, 1, 4)  # 첫 번째 월요일 근사
    end_date = date(start_year + n_years - 1, 12, 31)

    weeks = pd.date_range(
        start=str(start_date),
        end=str(end_date),
        freq="W-MON",
    )

    records = []
    for field, exam_months in CERT_EXAM_MONTHS.items():
        for week_ts in weeks:
            current = week_ts.date()
            has_exam = int(current.month in exam_months)
            weeks_to_exam = _weeks_to_next_exam(current, field)

            date_str = current.strftime("%Y-%m-%d")
            records.append({
                "date": date_str,
                "field": field,
                "has_cert_exam": has_exam,
                "weeks_to_exam": weeks_to_exam,
                "ds": date_str,
                "y": weeks_to_exam,
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["field", "date"]).reset_index(drop=True)
    return df


def generate_competitor_data(
    enrollment_df: pd.DataFrame,
    seed: int = 48,
) -> pd.DataFrame:
    """경쟁 학원 합성 데이터 생성.

    수강 이력 기반으로 경쟁 학원 개강 수와 평균 수강료를 생성한다.

    경고: enrollment_df에서 값을 파생하므로 합성 상관 관계가 인위적으로
    증폭된다(synthetic correlation inflation). 실제 데이터로 대체 전까지
    모델 정확도 지표는 낙관적으로 편향된다.

    Args:
        enrollment_df: generate_enrollment_history() 결과 DataFrame
        seed: 재현성을 위한 난수 시드

    Returns:
        DataFrame with columns: date, field, competitor_openings, competitor_avg_price, ds, y
    """
    rng = np.random.default_rng(seed)
    records = []

    for field in enrollment_df["field"].unique():
        field_df = enrollment_df[enrollment_df["field"] == field].sort_values("date")
        enrollments = field_df["enrollment_count"].values
        dates = field_df["date"].values
        max_enrollment = max(enrollments.max(), 1)

        comp_ratio = COMP_RATIO.get(field, 0.7)
        base_price = BASE_PRICE.get(field, 450000)

        for dt, enrollment in zip(dates, enrollments):
            # 계절성 반영 (월별 약간의 변동)
            dt_ts = pd.Timestamp(dt)
            seasonal = rng.normal(0, 0.5)
            noise_open = rng.normal(0, 0.3)
            competitor_openings = int(round(max(0, enrollment * comp_ratio + seasonal + noise_open)))

            # 수강료: 수요 정규화 후 가격 변동
            norm_enrollment = enrollment / max_enrollment
            noise_price = rng.normal(0, 0.05)
            raw_price = base_price * (1 + 0.1 * norm_enrollment + noise_price)
            # max(0, ...) 가드: 음수 수강료 방지
            competitor_avg_price = int(round(max(0, raw_price), -4))

            date_str = dt_ts.strftime("%Y-%m-%d")
            records.append({
                "date": date_str,
                "field": field,
                "competitor_openings": competitor_openings,
                "competitor_avg_price": competitor_avg_price,
                "ds": date_str,
                "y": competitor_openings,
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["field", "date"]).reset_index(drop=True)
    return df


def generate_seasonal_events(
    start_year: int = 2018,
    n_years: int | None = None,
    seed: int = 47,
) -> pd.DataFrame:
    """계절성 이벤트 합성 데이터 생성.

    방학, 시험 시즌, 학기 시작 등 캘린더 기반 이진 플래그를 주간 단위로 생성한다.
    분야 구분 없이 전체 공통 적용되며 결정론적 출력을 보장한다.
    seed 파라미터는 API 일관성을 위해 존재하나 출력에 영향을 주지 않는다.

    Args:
        start_year: 시작 연도
        n_years: 생성할 연도 수. None이면 현재 연도까지 자동 계산.
        seed: API 일관성을 위한 시드 (출력에 영향 없음)

    Returns:
        DataFrame with columns: date, is_vacation, is_exam_season, is_semester_start
        (field 컬럼 없음 -- 전체 공통 적용)
    """
    if n_years is None:
        from edupulse.data.generators.enrollment_generator import _default_n_years
        n_years = _default_n_years(start_year)

    start_date = date(start_year, 1, 4)
    end_date = date(start_year + n_years - 1, 12, 31)

    weeks = pd.date_range(
        start=str(start_date),
        end=str(end_date),
        freq="W-MON",
    )

    records = []
    for week_ts in weeks:
        month = week_ts.month
        date_str = week_ts.strftime("%Y-%m-%d")
        records.append({
            "date": date_str,
            "is_vacation": int(month in [1, 2, 7, 8]),
            "is_exam_season": int(month in [6, 11, 12]),
            "is_semester_start": int(month in [3, 9]),
        })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df
