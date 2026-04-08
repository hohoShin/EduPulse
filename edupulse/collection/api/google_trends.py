"""Google Trends 검색량 수집 클라이언트 (캐시 전용).

pytrends 라이브러리를 사용하여 구글 트렌드 데이터를 수집한다.
이 데이터는 파이프라인 출력에 포함되지 않으며,
향후 분석/연구를 위해 캐시에만 저장된다.

- TooManyRequestsError 지수적 백오프 처리
- 캐시 노후화 경고 (4주 초과)
"""
import logging
import os
import time
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)

RETRY_DELAYS = [1, 2, 4]
MAX_RETRIES = 3
STALENESS_WEEKS = 4


def fetch_google_trends(
    keywords: list[str],
    timeframe: str = "today 12-m",
    geo: str = "KR",
) -> pd.DataFrame | None:
    """Google Trends 데이터를 수집.

    Args:
        keywords: 검색 키워드 목록 (최대 5개).
        timeframe: 조회 기간 (pytrends 형식, 기본 최근 12개월).
        geo: 지역 코드 (기본 KR).

    Returns:
        DataFrame (날짜 인덱스, 키워드별 검색량) 또는 실패 시 None.
        이 데이터는 캐시 전용이며 파이프라인 출력에 사용하지 않는다.
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        logger.error("pytrends 패키지 미설치. pip install pytrends 필요.")
        return None

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            pytrends = TrendReq(hl="ko", tz=540)
            pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
            df = pytrends.interest_over_time()

            if df.empty:
                logger.warning("Google Trends 결과 없음: keywords=%s", keywords)
                return None

            # isPartial 컬럼 제거
            if "isPartial" in df.columns:
                df = df.drop(columns=["isPartial"])

            return df

        except Exception as e:
            error_name = type(e).__name__
            if "TooManyRequestsError" in error_name or "429" in str(e):
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                logger.warning(
                    "Google Trends 429 오류, %ds 후 재시도 (%d/%d)",
                    delay, attempt + 1, MAX_RETRIES,
                )
                time.sleep(delay)
                last_error = e
                continue

            logger.error("Google Trends 수집 실패: %s: %s", error_name, e)
            return None

    logger.error("Google Trends 최대 재시도 초과: %s", last_error)
    return None


def cache_google_trends(
    output_dir: str = "edupulse/data/raw/external/cache/google",
    timeframe: str = "today 12-m",
    staleness_weeks: int = STALENESS_WEEKS,
) -> None:
    """모든 분야의 Google Trends 데이터를 캐시에 저장.

    파이프라인 출력에는 포함되지 않으며, 향후 연구/분석용이다.

    Args:
        output_dir: 캐시 저장 디렉토리.
        timeframe: 조회 기간.
        staleness_weeks: 캐시 노후화 경고 기준 (주).
    """
    from edupulse.collection.api.keywords import FIELD_KEYWORDS_EN, FIELDS

    os.makedirs(output_dir, exist_ok=True)

    for field in FIELDS:
        keywords = FIELD_KEYWORDS_EN[field]
        cache_path = os.path.join(output_dir, f"google_{field}.csv")

        # 노후화 경고
        if os.path.exists(cache_path):
            mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
            age_weeks = (datetime.now() - mtime).days / 7
            if age_weeks > staleness_weeks:
                logger.warning(
                    "Google Trends 캐시 노후화: %s (%.1f주 경과, 기준: %d주)",
                    cache_path, age_weeks, staleness_weeks,
                )

        logger.info("Google Trends 캐시 수집: field=%s, keywords=%s", field, keywords)
        df = fetch_google_trends(keywords, timeframe=timeframe)

        if df is not None:
            # 원자적 쓰기
            tmp_path = cache_path + ".tmp"
            df.to_csv(tmp_path)
            os.replace(tmp_path, cache_path)
            logger.info("Google Trends 캐시 저장: %s (%d행)", cache_path, len(df))
        else:
            logger.warning("Google Trends 수집 실패, 캐시 미갱신: field=%s", field)

        # pytrends 요청 간 딜레이 (비공식 API 보호)
        time.sleep(2)