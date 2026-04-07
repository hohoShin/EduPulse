"""전처리 모듈 테스트."""
import numpy as np
import pandas as pd
import pytest

from edupulse.preprocessing.cleaner import clean_data
from edupulse.preprocessing.transformer import add_lag_features
from edupulse.preprocessing.merger import merge_datasets


def _make_enrollment_df(n=20, with_nulls=False):
    """테스트용 수강 이력 DataFrame 생성."""
    dates = pd.date_range("2024-01-01", periods=n, freq="2W")
    counts = list(range(10, 10 + n))
    if with_nulls:
        counts[3] = None
        counts[7] = None
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "enrollment_count": counts,
        "field": ["coding"] * n,
    })


def test_clean_data_interpolation():
    """결측치가 linear interpolation으로 채워져야 한다."""
    df = _make_enrollment_df(n=20, with_nulls=True)
    assert df["enrollment_count"].isnull().sum() == 2

    cleaned = clean_data(df, target_col="enrollment_count")
    assert cleaned["enrollment_count"].isnull().sum() == 0


def test_clean_data_outlier_clipping():
    """IQR 방식으로 극단값이 클리핑되어야 한다."""
    df = _make_enrollment_df(n=20)
    # 극단 이상치 삽입
    df.loc[0, "enrollment_count"] = 1000
    df.loc[1, "enrollment_count"] = -500

    cleaned = clean_data(df, target_col="enrollment_count")
    # 클리핑 후 원래 극단값보다 작아야 함
    assert cleaned["enrollment_count"].max() < 1000
    assert cleaned["enrollment_count"].min() >= -500


def test_add_lag_features():
    """lag 컬럼(lag_1w, lag_2w, lag_4w, lag_8w)이 생성되어야 한다."""
    df = _make_enrollment_df(n=20)
    result = add_lag_features(df, target_col="enrollment_count", lags=[1, 2, 4, 8])

    for lag in [1, 2, 4, 8]:
        assert f"lag_{lag}w" in result.columns, f"lag_{lag}w 컬럼 없음"

    # rolling_mean_4w 컬럼도 생성되어야 함
    assert "rolling_mean_4w" in result.columns

    # lag_1w의 첫 번째 값은 NaN (shift로 생성)
    assert pd.isna(result["lag_1w"].iloc[0])


def test_merge_datasets():
    """enrollment + search_trends 병합 결과에 search_volume 컬럼이 있어야 한다."""
    enrollment_df = _make_enrollment_df(n=10)
    enrollment_df["date"] = pd.to_datetime(enrollment_df["date"])

    search_df = enrollment_df[["date"]].copy()
    search_df["search_volume"] = range(100, 110)

    merged = merge_datasets(enrollment_df, search_df=search_df)
    assert "search_volume" in merged.columns
    assert len(merged) == len(enrollment_df)
