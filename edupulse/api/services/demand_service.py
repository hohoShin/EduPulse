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


def _prev_monday(d: date) -> date:
    """주어진 날짜 이전(또는 당일) 가장 가까운 월요일."""
    return d - timedelta(days=d.weekday())


def get_demand_trend(field: str, model_name: str = "ensemble") -> dict:
    """과거 8주 실적 + 오늘 이후 4주 예측 주간 시계열 반환.

    CSV 데이터가 오늘보다 과거에서 끝나는 경우, CSV 끝 ~ 오늘 구간도
    forecast로 채워서 시계열이 현재 시점까지 이어지도록 한다.

    Args:
        field: 분야 ('coding', 'security', 'game', 'art')
        model_name: 사용할 모델

    Returns:
        {"field", "points": [...], "model_used"} dict
    """
    today = date.today()
    current_monday = _prev_monday(today)
    weekly = _build_weekly_series(field)

    # --- 과거 8주 실적 (오늘 기준) ---
    historical_points = _build_historical_points(weekly, current_monday)

    # --- 미래 4주 예측 (오늘 기준) ---
    forecast_start = current_monday
    forecast_end = current_monday + timedelta(weeks=3)
    forecast_points, model_used = _build_forecast_points(
        field, model_name, forecast_start, forecast_end,
    )

    return {
        "field": field,
        "points": historical_points + forecast_points,
        "model_used": model_used,
    }


def _build_historical_points(
    weekly: pd.Series | None, current_monday: date,
) -> list[dict]:
    """오늘 기준 과거 8주 중 CSV 데이터가 존재하는 주만 actual 포인트로 반환."""
    if weekly is None or weekly.empty:
        return []

    points: list[dict] = []
    for i in range(8, 0, -1):
        week_date = current_monday - timedelta(weeks=i)
        ts = pd.Timestamp(week_date)
        if ts in weekly.index:
            value = float(weekly[ts]) * ENROLLMENT_SCALE
            points.append({
                "date": str(week_date),
                "value": round(value, 1),
                "upper": None,
                "lower": None,
                "category": "actual",
            })
    return points


def _build_forecast_points(
    field: str, model_name: str, forecast_start: date, forecast_end: date,
) -> tuple[list[dict], str]:
    """forecast_start부터 forecast_end까지 주간 예측 포인트 생성.

    Returns:
        (포인트 리스트, 실제 사용된 모델명) 튜플
    """
    points: list[dict] = []
    actual_model = model_name
    week_date = forecast_start

    while week_date <= forecast_end:
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
            logger.warning("%s 예측 실패: %s", week_date, e)
            points.append({
                "date": str(week_date),
                "value": 0.0,
                "upper": None,
                "lower": None,
                "category": "forecast",
            })
        week_date += timedelta(weeks=1)

    return points, actual_model
