"""네이버 DataLab API 일일 쿼터 추적기.

JSON 파일 기반으로 일일 API 호출 횟수를 추적한다.
- KST(UTC+9) 기준 자정에 자동 리셋
- 원자적 쓰기(tmp + os.replace)로 파일 손상 방지
- 단일 프로세스 사용 가정 (동시 실행 미지원)
"""
import json
import logging
import os
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))
DEFAULT_QUOTA_PATH = "edupulse/data/raw/external/.naver_quota.json"


def _today_kst() -> str:
    """KST 기준 오늘 날짜를 YYYY-MM-DD 형식으로 반환."""
    return datetime.now(KST).strftime("%Y-%m-%d")


def read_quota(quota_path: str = DEFAULT_QUOTA_PATH) -> dict:
    """쿼터 파일을 읽어 현재 호출 횟수를 반환.

    파일이 없거나 날짜가 오늘(KST)과 다르면 0으로 리셋한다.

    Returns:
        {"date": "YYYY-MM-DD", "calls_today": int}
    """
    today = _today_kst()

    if not os.path.exists(quota_path):
        return {"date": today, "calls_today": 0}

    try:
        with open(quota_path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.warning("쿼터 파일 손상, 리셋합니다: %s", quota_path)
        return {"date": today, "calls_today": 0}

    if data.get("date") != today:
        logger.info("날짜 변경 감지 (KST), 쿼터 리셋: %s -> %s", data.get("date"), today)
        return {"date": today, "calls_today": 0}

    return {"date": today, "calls_today": data.get("calls_today", 0)}


def increment_quota(quota_path: str = DEFAULT_QUOTA_PATH) -> int:
    """쿼터를 1 증가시키고 새로운 호출 횟수를 반환.

    원자적 쓰기: tmp 파일에 쓴 후 os.replace()로 교체.

    Returns:
        증가 후 calls_today 값.
    """
    data = read_quota(quota_path)
    data["calls_today"] += 1

    os.makedirs(os.path.dirname(quota_path), exist_ok=True)
    tmp_path = quota_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f)
    os.replace(tmp_path, quota_path)

    return data["calls_today"]


def check_quota(max_daily: int = 1000, quota_path: str = DEFAULT_QUOTA_PATH) -> bool:
    """현재 쿼터가 한도 내인지 확인.

    Args:
        max_daily: 일일 최대 호출 횟수.
        quota_path: 쿼터 파일 경로.

    Returns:
        True면 호출 가능, False면 한도 초과.
    """
    data = read_quota(quota_path)
    remaining = max_daily - data["calls_today"]
    if remaining <= 0:
        logger.warning("네이버 API 일일 쿼터 소진 (%d/%d)", data["calls_today"], max_daily)
        return False
    return True