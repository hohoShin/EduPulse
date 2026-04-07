"""데이터 정제 모듈.

결측치 보간, 이상치 처리, 날짜 컬럼 표준화.
"""
import pandas as pd
import numpy as np


def clean_data(df: pd.DataFrame, target_col: str = "enrollment_count") -> pd.DataFrame:
    """결측치 보간 + 이상치 클리핑 + 날짜 표준화.

    Args:
        df: 입력 DataFrame.
        target_col: 이상치 처리를 적용할 수치 컬럼명.

    Returns:
        정제된 DataFrame (원본 변경 없이 복사본 반환).
    """
    df = df.copy()

    # 날짜 컬럼 표준화 (YYYY-MM-DD)
    df = _standardize_date_columns(df)

    # 결측치: linear interpolation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        df[numeric_cols] = df[numeric_cols].interpolate(method="linear", limit_direction="both")

    # 이상치: IQR 방식으로 clip (target_col 존재 시)
    if target_col in df.columns:
        df = _clip_outliers_iqr(df, target_col)

    return df


def _standardize_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """날짜 관련 컬럼을 YYYY-MM-DD 문자열 형식으로 표준화."""
    date_col_candidates = [c for c in df.columns if "date" in c.lower() or c in ("ds",)]
    for col in date_col_candidates:
        try:
            df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")
        except Exception:
            pass
    return df


def _clip_outliers_iqr(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """IQR 방식으로 이상치를 클리핑 (제거 대신 경계값으로 대체).

    Q1 - 1.5*IQR 미만은 하한으로, Q3 + 1.5*IQR 초과는 상한으로 clip.
    """
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    df[col] = df[col].clip(lower=lower, upper=upper)
    return df
