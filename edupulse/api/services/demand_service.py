"""수요 트렌드 서비스 — 과거 8주 실적 + 미래 4주 예측 시계열."""

import logging
from datetime import date, timedelta

import pandas as pd

from edupulse.constants import ENROLLMENT_PATH, ENROLLMENT_SCALE
from edupulse.model.predict import load_csv_cached, predict_demand

logger = logging.getLogger(__name__)


def _build_weekly_series(field: str) -> pd.Series | None:
    """enrollment_history.csv에서 field별 주간 합계 시리즈 반환.

    Returns:
        DatetimeIndex(W-MON) 기반 Series 또는 데이터 없으면 None
    """
    enroll_raw = load_csv_cached(ENROLLMENT_PATH)
    if enroll_raw is None:
        return None

    df = enroll_raw.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["field"] == field]
    if df.empty:
        return None

    # 주간 집계 (W = W-SUN → 월~일, start_time = 월요일)
    df["week"] = df["date"].dt.to_period("W").dt.start_time
    series = df.groupby("week")["enrollment_count"].sum().sort_index()
    return series


def get_demand_trend(field: str, model_name: str = "ensemble") -> dict:
    """CSV 마지막 8주 실적 + 그 뒤 4주 예측 주간 시계열 반환.

    Args:
        field: 분야 ('coding', 'security', 'game', 'art')
        model_name: 사용할 모델

    Returns:
        {"field", "points": [...], "model_used"} dict
    """
    weekly = _build_weekly_series(field)

    # --- 과거 8주 실적 ---
    historical_points = _build_historical_points(weekly)

    # forecast 시작점: 실적 마지막 주 다음 월요일 (데이터 없으면 이번 주 월요일)
    if weekly is not None and len(weekly) > 0:
        last_data_monday = weekly.index[-1].date()
        forecast_start = last_data_monday + timedelta(weeks=1)
    else:
        today = date.today()
        forecast_start = today - timedelta(days=today.weekday())

    # --- 미래 4주 예측 ---
    forecast_points, model_used = _build_forecast_points(
        field, model_name, forecast_start,
    )

    return {
        "field": field,
        "points": historical_points + forecast_points,
        "model_used": model_used,
    }


def _build_historical_points(weekly: pd.Series | None) -> list[dict]:
    """주간 시리즈에서 마지막 8주 실적 포인트 생성."""
    if weekly is None or weekly.empty:
        return []

    last_8 = weekly.tail(8)
    points: list[dict] = []
    for ts, count in last_8.items():
        points.append({
            "date": str(ts.date()),
            "value": round(float(count) * ENROLLMENT_SCALE, 1),
            "upper": None,
            "lower": None,
            "category": "actual",
        })
    return points


def _build_forecast_points(
    field: str, model_name: str, forecast_start: date,
) -> tuple[list[dict], str]:
    """미래 4주 예측 포인트. predict_demand() 호출 (ENROLLMENT_SCALE 이미 적용됨).

    Returns:
        (포인트 리스트, 실제 사용된 모델명) 튜플
    """
    points: list[dict] = []
    actual_model = model_name

    for i in range(4):
        week_date = forecast_start + timedelta(weeks=i)
        try:
            result = predict_demand(
                "트렌드예측", str(week_date), field,
                model_name=model_name,
            )
            actual_model = result.model_used
            points.append({
                "date": str(week_date),
                "value": float(result.predicted_enrollment),
                "upper": round(result.confidence_upper, 1),
                "lower": round(result.confidence_lower, 1),
                "category": "forecast",
            })
        except Exception as e:
            logger.warning("미래 %d주차 예측 실패: %s", i, e)
            points.append({
                "date": str(week_date),
                "value": 0.0,
                "upper": None,
                "lower": None,
                "category": "forecast",
            })

    return points, actual_model
