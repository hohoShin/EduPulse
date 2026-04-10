"""검색 트렌드 수집 오케스트레이터.

네이버 DataLab API에서 검색량을 수집하여
파이프라인 호환 search_trends.csv를 생성한다.

Fallback 체인:
1. 네이버 API 호출 성공 → 신규 데이터 사용
2. 네이버 API 실패 → 최근 캐시된 네이버 JSON 사용
3. 캐시 없음 → 건너뜀 (경고 로그)

Google Trends는 파이프라인 출력에 포함되지 않으며,
also_cache_google=True 시 별도 캐시에만 저장한다.

사용법:
    python -m edupulse.collection.api.collect_search_trends
"""
import glob
import logging
import os
from datetime import datetime, timedelta

import pandas as pd

from edupulse.collection.api.keywords import FIELDS

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_PATH = "edupulse/data/raw/external/search_trends.csv"
DEFAULT_CACHE_DIR = "edupulse/data/raw/external/cache"
STALENESS_WEEKS = 4


def collect_search_trends(
    output_path: str = DEFAULT_OUTPUT_PATH,
    cache_dir: str = DEFAULT_CACHE_DIR,
    start_date: str | None = None,
    end_date: str | None = None,
    max_daily_calls: int = 1000,
    also_cache_google: bool = False,
) -> str | None:
    """검색 트렌드를 수집하고 파이프라인 호환 CSV를 생성.

    Args:
        output_path: 출력 CSV 경로 (기본: edupulse/data/raw/external/search_trends.csv).
        cache_dir: 캐시 디렉토리 경로.
        start_date: 수집 시작일 (YYYY-MM-DD). None이면 52주 전.
        end_date: 수집 종료일 (YYYY-MM-DD). None이면 오늘.
        max_daily_calls: 네이버 API 일일 최대 호출 횟수.
        also_cache_google: True면 Google Trends도 캐시에 수집.

    Returns:
        성공 시 output_path, 실패 시 None.
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_dt = datetime.now() - timedelta(weeks=52)
        start_date = start_dt.strftime("%Y-%m-%d")

    logger.info("검색 트렌드 수집 시작: %s ~ %s", start_date, end_date)

    # Step 1: 네이버 API에서 수집 시도
    df = _try_fetch_naver(start_date, end_date, max_daily_calls, cache_dir)

    # Step 2: 실패 시 캐시 fallback
    if df is None or df.empty:
        logger.warning("네이버 API 수집 실패, 캐시 fallback 시도")
        df = _load_cached_naver(os.path.join(cache_dir, "naver"))
        if df is None or df.empty:
            logger.warning("캐시된 네이버 데이터 없음, 수집 건너뜀")
            return None

    # Step 3: 주간 정규화
    df = normalize_to_weekly(df)

    # Step 4: 원자적 쓰기
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tmp_path = output_path + ".tmp"
    df.to_csv(tmp_path, index=False)
    os.replace(tmp_path, output_path)
    logger.info("검색 트렌드 저장 완료: %s (%d행)", output_path, len(df))

    # Step 5: Google Trends 캐시 (선택)
    if also_cache_google:
        try:
            from edupulse.collection.api.google_trends import cache_google_trends
            cache_google_trends(
                output_dir=os.path.join(cache_dir, "google"),
                staleness_weeks=STALENESS_WEEKS,
            )
        except Exception as e:
            logger.warning("Google Trends 캐시 실패 (무시): %s", e)

    return output_path


def normalize_to_weekly(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """날짜를 주간 단위(월요일 시작)로 정규화.

    일간 또는 주간 입력 모두 처리 가능.
    (field, week) 기준으로 search_volume을 합산한다.

    Args:
        df: date, field, search_volume 컬럼을 포함한 DataFrame.
        date_col: 날짜 컬럼명.

    Returns:
        주간 정규화된 DataFrame [date, field, search_volume, ds, y].
    """
    if df.empty:
        return df

    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col])
    result[date_col] = result[date_col].dt.to_period("W").dt.start_time

    result = (
        result.groupby(["field", date_col], as_index=False)["search_volume"]
        .sum()
    )

    result["ds"] = result[date_col]
    result["y"] = result["search_volume"]
    result = result[["date", "field", "search_volume", "ds", "y"]]
    result = result.sort_values(["field", date_col]).reset_index(drop=True)

    return result


def _try_fetch_naver(
    start_date: str,
    end_date: str,
    max_daily_calls: int,
    cache_dir: str,
) -> pd.DataFrame | None:
    """네이버 API 수집을 시도. 실패 시 None 반환."""
    try:
        from edupulse.collection.api.naver_datalab import fetch_all_fields
        from edupulse.config import settings

        return fetch_all_fields(
            start_date=start_date,
            end_date=end_date,
            client_id=settings.naver_client_id,
            client_secret=settings.naver_client_secret,
            max_daily_calls=max_daily_calls,
            cache_dir=os.path.join(cache_dir, "naver"),
        )
    except Exception as e:
        logger.error("네이버 API 수집 중 예외: %s", e)
        return None


def _load_cached_naver(cache_dir: str) -> pd.DataFrame | None:
    """가장 최근 캐시된 네이버 JSON 데이터를 로드.

    캐시 디렉토리에서 모든 분야의 가장 최근 파일을 찾아 합산한다.
    4주 이상 경과한 캐시는 경고를 출력한다.

    Returns:
        합산 DataFrame 또는 캐시 없으면 None.
    """
    if not os.path.exists(cache_dir):
        return None

    all_dfs = []

    for field in FIELDS:
        pattern = os.path.join(cache_dir, f"naver_{field}_*.json")
        files = sorted(glob.glob(pattern), reverse=True)

        if not files:
            logger.warning("캐시된 네이버 데이터 없음: field=%s", field)
            continue

        latest = files[0]
        mtime = datetime.fromtimestamp(os.path.getmtime(latest))
        age_weeks = (datetime.now() - mtime).days / 7

        if age_weeks > STALENESS_WEEKS:
            logger.warning(
                "네이버 캐시 노후화: %s (%.1f주 경과, 기준: %d주)",
                latest, age_weeks, STALENESS_WEEKS,
            )

        try:
            df = pd.read_json(latest, orient="records")
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df["ds"] = pd.to_datetime(df["ds"])
                all_dfs.append(df)
                logger.info("캐시 로드: %s (%d행, %.1f주 전)", latest, len(df), age_weeks)
        except Exception as e:
            logger.error("캐시 파일 로드 실패: %s: %s", latest, e)

    if not all_dfs:
        return None

    return pd.concat(all_dfs, ignore_index=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    result = collect_search_trends()
    if result:
        logger.info("수집 완료: %s", result)
    else:
        logger.warning("수집 실패 또는 데이터 없음")