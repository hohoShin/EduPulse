"""내부 지표 합성 데이터 생성기.

수강 이력 기반으로 상담 로그, 학생 프로필, 웹 로그 데이터를 합성한다.

경고: 이 모듈의 모든 생성기는 enrollment_df에서 값을 파생시키므로,
합성 데이터 간 인위적 상관 관계(synthetic correlation inflation)가 발생한다.
모델 정확도 지표는 실제 데이터 대비 낙관적으로 편향될 수 있다.
"""
import numpy as np
import pandas as pd


# 분야별 상담 배율 (등록 1명당 선행 상담 건수)
CONSULT_MULTIPLIER = {
    "coding": 3.0,
    "security": 2.5,
    "game": 2.0,
    "art": 1.5,
}

# 분야별 연령대 Dirichlet alpha (20대, 30대, 40대+)
FIELD_AGE_ALPHA = {
    "coding":   [5, 3, 1],   # 20대 집중
    "security": [3, 4, 2],   # 30대 중심 (커리어 전환)
    "game":     [6, 2, 1],   # 20대 집중
    "art":      [3, 3, 3],   # 균등 분포
}

# 분야별 수강 목적 Dirichlet alpha (취업, 취미, 자격증)
FIELD_PURPOSE_ALPHA = {
    "coding":   [5, 2, 2],   # 취업 중심
    "security": [3, 1, 5],   # 자격증 중심
    "game":     [3, 4, 1],   # 취미 중심
    "art":      [2, 5, 1],   # 취미 중심
}

# 분야별 페이지뷰 배율 (등록 1명당 선행 페이지뷰 수)
PV_MULTIPLIER = {
    "coding": 15.0,
    "security": 12.0,
    "game": 18.0,
    "art": 10.0,
}


def generate_consultation_logs(
    enrollment_df: pd.DataFrame,
    seed: int = 44,
) -> pd.DataFrame:
    """상담 로그 합성 데이터 생성.

    등록 수에 1-2주 선행하는 상담 건수를 생성한다.

    경고: enrollment_df에서 값을 파생하므로 합성 상관 관계가 인위적으로
    증폭된다(synthetic correlation inflation). 실제 데이터로 대체 전까지
    모델 정확도 지표는 낙관적으로 편향된다.

    Args:
        enrollment_df: generate_enrollment_history() 결과 DataFrame
        seed: 재현성을 위한 난수 시드

    Returns:
        DataFrame with columns: date, field, consultation_count, ds, y
    """
    rng = np.random.default_rng(seed)
    records = []

    for field in enrollment_df["field"].unique():
        field_df = enrollment_df[enrollment_df["field"] == field].sort_values("date")
        enrollments = field_df["enrollment_count"].values
        dates = field_df["date"].values
        max_enrollment = max(enrollments.max(), 1)

        multiplier = CONSULT_MULTIPLIER.get(field, 2.0)

        for i, (dt, enrollment) in enumerate(zip(dates, enrollments)):
            # 1-2주 후 등록 수 기반으로 현재 상담 건수 생성 (선행 지표)
            future_idx = min(i + rng.integers(1, 3), len(enrollments) - 1)
            future_enrollment = enrollments[future_idx]

            noise_count = rng.normal(0, 1.0)
            consultation_count = int(round(max(0, future_enrollment * multiplier + noise_count)))

            dt_ts = pd.Timestamp(dt)
            date_str = dt_ts.strftime("%Y-%m-%d")
            records.append({
                "date": date_str,
                "field": field,
                "consultation_count": consultation_count,
                "ds": date_str,
                "y": consultation_count,
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["field", "date"]).reset_index(drop=True)
    return df


def generate_student_profiles(
    enrollment_df: pd.DataFrame,
    seed: int = 45,
) -> pd.DataFrame:
    """학생 프로필 합성 데이터 생성.

    분야별 연령대 분포와 수강 목적 분포를 Dirichlet 분포로 생성한다.

    경고: enrollment_df에서 값을 파생하므로 합성 상관 관계가 인위적으로
    증폭된다(synthetic correlation inflation). 실제 데이터로 대체 전까지
    모델 정확도 지표는 낙관적으로 편향된다.

    Args:
        enrollment_df: generate_enrollment_history() 결과 DataFrame
        seed: 재현성을 위한 난수 시드

    Returns:
        DataFrame with columns:
            date, field, age_20s_ratio, age_30s_ratio, age_40plus_ratio,
            purpose_career, purpose_hobby, purpose_cert, ds, y
    """
    rng = np.random.default_rng(seed)
    records = []

    for field in enrollment_df["field"].unique():
        field_df = enrollment_df[enrollment_df["field"] == field].sort_values("date")
        dates = field_df["date"].values
        enrollments = field_df["enrollment_count"].values

        age_alpha = FIELD_AGE_ALPHA.get(field, [3, 3, 3])
        purpose_alpha = FIELD_PURPOSE_ALPHA.get(field, [3, 3, 3])

        for dt, enrollment in zip(dates, enrollments):
            age_ratios = rng.dirichlet(age_alpha)
            purpose_ratios = rng.dirichlet(purpose_alpha)

            dt_ts = pd.Timestamp(dt)
            date_str = dt_ts.strftime("%Y-%m-%d")
            records.append({
                "date": date_str,
                "field": field,
                "age_20s_ratio": round(float(age_ratios[0]), 4),
                "age_30s_ratio": round(float(age_ratios[1]), 4),
                "age_40plus_ratio": round(float(age_ratios[2]), 4),
                "purpose_career": round(float(purpose_ratios[0]), 4),
                "purpose_hobby": round(float(purpose_ratios[1]), 4),
                "purpose_cert": round(float(purpose_ratios[2]), 4),
                "ds": date_str,
                "y": int(enrollment),
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["field", "date"]).reset_index(drop=True)
    return df


def generate_web_logs(
    enrollment_df: pd.DataFrame,
    seed: int = 46,
) -> pd.DataFrame:
    """웹/앱 로그 합성 데이터 생성.

    등록 수에 1-3주 선행하는 페이지뷰와 장바구니 이탈률을 생성한다.

    경고: enrollment_df에서 값을 파생하므로 합성 상관 관계가 인위적으로
    증폭된다(synthetic correlation inflation). 실제 데이터로 대체 전까지
    모델 정확도 지표는 낙관적으로 편향된다.

    Args:
        enrollment_df: generate_enrollment_history() 결과 DataFrame
        seed: 재현성을 위한 난수 시드

    Returns:
        DataFrame with columns: date, field, page_views, ds, y
    """
    rng = np.random.default_rng(seed)
    records = []

    for field in enrollment_df["field"].unique():
        field_df = enrollment_df[enrollment_df["field"] == field].sort_values("date")
        enrollments = field_df["enrollment_count"].values
        dates = field_df["date"].values

        multiplier = PV_MULTIPLIER.get(field, 12.0)

        for i, (dt, enrollment) in enumerate(zip(dates, enrollments)):
            # 1-3주 후 등록 수 기반으로 현재 페이지뷰 생성 (선행 지표)
            future_idx = min(i + rng.integers(1, 4), len(enrollments) - 1)
            future_enrollment = enrollments[future_idx]

            noise_pv = rng.normal(0, 2.0)
            page_views = int(round(max(1, future_enrollment * multiplier + noise_pv)))

            dt_ts = pd.Timestamp(dt)
            date_str = dt_ts.strftime("%Y-%m-%d")
            records.append({
                "date": date_str,
                "field": field,
                "page_views": page_views,
                "ds": date_str,
                "y": page_views,
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["field", "date"]).reset_index(drop=True)
    return df
