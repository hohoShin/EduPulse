"""피처 변환 모듈.

lag feature, 이동평균, 순환 인코딩 생성.
공유 인코딩 함수(compute_month_encoding, compute_field_encoding)는
predict.py:build_features()에서도 사용한다. 수정 시 양쪽 동작을 확인할 것.
"""
import math

import numpy as np
import pandas as pd

from edupulse.constants import FIELD_ENCODING


def compute_month_encoding(month: int) -> tuple[float, float]:
    """월(1~12) → (month_sin, month_cos) 순환 인코딩.

    add_lag_features()와 build_features() 모두 이 함수를 단일 소스로 사용한다.

    Args:
        month: 월 (1~12)

    Returns:
        (month_sin, month_cos) 튜플
    """
    rad = 2 * math.pi * month / 12
    return math.sin(rad), math.cos(rad)


def compute_field_encoding(field: str) -> float:
    """분야 문자열 → 숫자 인코딩.

    constants.py의 FIELD_ENCODING을 단일 진실 소스로 사용한다.

    Args:
        field: 분야 ('coding', 'security', 'game', 'art')

    Returns:
        인코딩된 float 값 (미등록 분야는 0.0)
    """
    return float(FIELD_ENCODING.get(field, 0))


def add_lag_features(
    df: pd.DataFrame,
    target_col: str = "enrollment_count",
    lags: list[int] = None,
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

    date_col = _detect_date_col(df)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])

    # shift()가 행 위치 기반이므로 lag 계산 전 반드시 날짜순 정렬
    if date_col and "field" in df.columns:
        df = df.sort_values(["field", date_col]).reset_index(drop=True)
    elif date_col:
        df = df.sort_values(date_col).reset_index(drop=True)

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

    if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
        month = df[date_col].dt.month
        df["month_sin"] = month.apply(lambda m: compute_month_encoding(m)[0])
        df["month_cos"] = month.apply(lambda m: compute_month_encoding(m)[1])

    if "field" in df.columns:
        df["field_encoded"] = df["field"].apply(compute_field_encoding)

    return df


def _detect_date_col(df: pd.DataFrame) -> str | None:
    """'date' 또는 'ds' 컬럼을 감지하여 반환."""
    for candidate in ("date", "ds"):
        if candidate in df.columns:
            return candidate
    date_cols = [c for c in df.columns if "date" in c.lower()]
    return date_cols[0] if date_cols else None
