"""피처 변환 모듈.

lag feature, 이동평균, 순환 인코딩 생성.
"""
import pandas as pd
import numpy as np
from typing import List


def add_lag_features(
    df: pd.DataFrame,
    target_col: str = "enrollment_count",
    lags: List[int] = None,
) -> pd.DataFrame:
    """lag feature, 이동평균, 순환 인코딩을 추가한다.

    Args:
        df: 입력 DataFrame. 'date' 또는 'ds' 컬럼 필요.
        target_col: lag를 생성할 대상 컬럼.
        lags: lag 주(week) 단위 목록. 기본값 [1, 2, 4, 8].

    Returns:
        피처가 추가된 DataFrame (원본 변경 없이 복사본 반환).
    """
    if lags is None:
        lags = [1, 2, 4, 8]

    df = df.copy()

    # 날짜 컬럼 파싱
    date_col = _detect_date_col(df)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])

    # lag features (분야별 groupby로 경계 넘김 방지)
    if target_col in df.columns:
        if "field" in df.columns:
            for lag in lags:
                df[f"lag_{lag}w"] = df.groupby("field")[target_col].shift(lag)
            df["rolling_mean_4w"] = (
                df.groupby("field")[target_col]
                .rolling(window=4, min_periods=1).mean()
                .reset_index(level=0, drop=True)
            )
        else:
            for lag in lags:
                df[f"lag_{lag}w"] = df[target_col].shift(lag)
            df["rolling_mean_4w"] = (
                df[target_col].rolling(window=4, min_periods=1).mean()
            )

    # 순환 인코딩 (month_sin, month_cos)
    if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
        month = df[date_col].dt.month
        df["month_sin"] = np.sin(2 * np.pi * month / 12)
        df["month_cos"] = np.cos(2 * np.pi * month / 12)

    # 분야 label encoding (constants.py의 FIELD_ENCODING을 단일 진실 소스로 사용)
    if "field" in df.columns:
        from edupulse.constants import FIELD_ENCODING
        df["field_encoded"] = df["field"].map(FIELD_ENCODING).fillna(0).astype(int)

    return df


def _detect_date_col(df: pd.DataFrame) -> str | None:
    """'date' 또는 'ds' 컬럼을 감지하여 반환."""
    for candidate in ("date", "ds"):
        if candidate in df.columns:
            return candidate
    # date가 포함된 컬럼명 폴백
    date_cols = [c for c in df.columns if "date" in c.lower()]
    return date_cols[0] if date_cols else None
