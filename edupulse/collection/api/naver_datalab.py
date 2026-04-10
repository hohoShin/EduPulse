"""네이버 DataLab 검색어 트렌드 API 클라이언트.

POST https://openapi.naver.com/v1/datalab/search 를 호출하여
분야별 주간 검색량을 수집한다.

- httpx 기반 HTTP 클라이언트
- 지수적 백오프 재시도 (1s, 2s, 4s / 최대 3회)
- 일일 쿼터 추적 (quota.py 연동)
- JSON 캐시 저장 (cache/naver/ 디렉토리)

Note: 네이버 DataLab은 상대 검색 지수(0-100)를 반환한다.
search_volume = 분야 내 키워드별 ratio 합산값.
모델 재학습 시 스케일 차이를 고려해야 한다.
"""
import json
import logging
import os
import time
from datetime import datetime, timedelta

import httpx
import pandas as pd

from edupulse.collection.api.keywords import FIELD_KEYWORDS, FIELDS
from edupulse.collection.api.quota import check_quota, increment_quota

logger = logging.getLogger(__name__)

NAVER_API_URL = "https://openapi.naver.com/v1/datalab/search"
RETRY_DELAYS = [1, 2, 4]  # 지수적 백오프 (초)
MAX_RETRIES = 3


class NaverAPIError(Exception):
    """네이버 API 호출 실패 (재시도 후에도 실패)."""


def fetch_naver_trends(
    keywords: list[str],
    start_date: str,
    end_date: str,
    client_id: str,
    client_secret: str,
    time_unit: str = "week",
) -> list[dict]:
    """네이버 DataLab 검색어 트렌드 API를 호출.

    Args:
        keywords: 검색 키워드 목록 (최대 5개).
        start_date: 시작일 (YYYY-MM-DD).
        end_date: 종료일 (YYYY-MM-DD).
        client_id: 네이버 API 클라이언트 ID.
        client_secret: 네이버 API 클라이언트 시크릿.
        time_unit: 시간 단위 ("date", "week", "month").

    Returns:
        [{"period": "YYYY-MM-DD", "ratio": float}, ...] 키워드별 결과 리스트.

    Raises:
        NaverAPIError: 재시도 후에도 API 호출 실패.
    """
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json",
    }
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": [
            {"groupName": kw, "keywords": [kw]} for kw in keywords
        ],
    }

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(NAVER_API_URL, headers=headers, json=body)

            if response.status_code == 200:
                return response.json().get("results", [])

            if response.status_code == 429 or response.status_code >= 500:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                logger.warning(
                    "네이버 API %d 응답, %ds 후 재시도 (%d/%d)",
                    response.status_code, delay, attempt + 1, MAX_RETRIES,
                )
                time.sleep(delay)
                last_error = NaverAPIError(
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                continue

            # 4xx (429 제외): 즉시 실패
            raise NaverAPIError(
                f"HTTP {response.status_code}: {response.text[:200]}"
            )

        except httpx.HTTPError as e:
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            logger.warning(
                "네이버 API 네트워크 오류, %ds 후 재시도 (%d/%d): %s",
                delay, attempt + 1, MAX_RETRIES, e,
            )
            time.sleep(delay)
            last_error = NaverAPIError(f"네트워크 오류: {e}")

    raise last_error or NaverAPIError("최대 재시도 횟수 초과")


def fetch_field_trends(
    field: str,
    start_date: str,
    end_date: str,
    client_id: str,
    client_secret: str,
) -> pd.DataFrame:
    """특정 분야의 검색 트렌드를 수집하고 집계.

    FIELD_KEYWORDS[field]의 모든 키워드를 조회하여
    주간 단위로 ratio를 합산한 search_volume을 생성한다.

    Args:
        field: 분야명 (coding, security, game, art).
        start_date: 시작일 (YYYY-MM-DD).
        end_date: 종료일 (YYYY-MM-DD).
        client_id: 네이버 API 클라이언트 ID.
        client_secret: 네이버 API 클라이언트 시크릿.

    Returns:
        DataFrame [date, field, search_volume, ds, y].
    """
    keywords = FIELD_KEYWORDS[field]
    results = fetch_naver_trends(
        keywords, start_date, end_date, client_id, client_secret,
    )

    # 키워드별 결과를 주간 단위로 합산
    weekly_totals: dict[str, float] = {}
    for group in results:
        for item in group.get("data", []):
            period = item["period"]
            ratio = item.get("ratio", 0.0)
            weekly_totals[period] = weekly_totals.get(period, 0.0) + ratio

    records = []
    for period, total in sorted(weekly_totals.items()):
        records.append({
            "date": period,
            "field": field,
            "search_volume": int(round(total)),
            "ds": period,
            "y": int(round(total)),
        })

    df = pd.DataFrame(records)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["ds"] = pd.to_datetime(df["ds"])
    return df


def fetch_all_fields(
    start_date: str,
    end_date: str,
    client_id: str,
    client_secret: str,
    max_daily_calls: int = 1000,
    cache_dir: str = "edupulse/data/raw/external/cache/naver",
) -> pd.DataFrame | None:
    """모든 분야의 검색 트렌드를 수집.

    쿼터를 확인하며 각 분야별로 API를 호출하고,
    원본 JSON 응답을 캐시 디렉토리에 저장한다.

    Args:
        start_date: 시작일 (YYYY-MM-DD).
        end_date: 종료일 (YYYY-MM-DD).
        client_id: 네이버 API 클라이언트 ID.
        client_secret: 네이버 API 클라이언트 시크릿.
        max_daily_calls: 일일 최대 API 호출 횟수.
        cache_dir: JSON 캐시 저장 디렉토리.

    Returns:
        모든 분야 합산 DataFrame, 또는 수집 실패 시 None.
    """
    if not client_id or not client_secret:
        logger.error("네이버 API 인증 정보 미설정 (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)")
        return None

    os.makedirs(cache_dir, exist_ok=True)
    all_dfs = []

    for field in FIELDS:
        if not check_quota(max_daily_calls):
            logger.warning("쿼터 소진으로 나머지 분야 건너뜀: %s부터", field)
            break

        try:
            increment_quota()
            logger.info("네이버 트렌드 수집 시작: field=%s, %s ~ %s", field, start_date, end_date)
            df = fetch_field_trends(field, start_date, end_date, client_id, client_secret)

            # 캐시 저장
            cache_path = os.path.join(
                cache_dir,
                f"naver_{field}_{start_date.replace('-', '')}_{end_date.replace('-', '')}.json",
            )
            df.to_json(cache_path, orient="records", date_format="iso", force_ascii=False)
            logger.info("캐시 저장: %s (%d행)", cache_path, len(df))

            all_dfs.append(df)

        except NaverAPIError as e:
            logger.error("네이버 API 실패 (field=%s): %s", field, e)
            continue

    if not all_dfs:
        return None

    result = pd.concat(all_dfs, ignore_index=True)
    result = result.sort_values(["field", "date"]).reset_index(drop=True)
    return result