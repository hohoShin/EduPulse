"""검색 트렌드 수집 모듈 테스트.

모든 API 호출은 mock 처리하며 실제 네트워크 요청을 하지 않는다.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from edupulse.collection.api.quota import (
    KST,
    DEFAULT_QUOTA_PATH,
    check_quota,
    increment_quota,
    read_quota,
)


# ──────────────────────────────────────────────
# Quota 테스트
# ──────────────────────────────────────────────


class TestQuota:
    """쿼터 추적기 테스트."""

    def test_read_quota_missing_file(self, tmp_path):
        """쿼터 파일 없으면 오늘 날짜 + 0회 반환."""
        path = str(tmp_path / "quota.json")
        result = read_quota(path)
        assert result["calls_today"] == 0
        assert result["date"] == datetime.now(KST).strftime("%Y-%m-%d")

    def test_read_quota_stale_date_resets(self, tmp_path):
        """어제 날짜 쿼터 파일은 0으로 리셋."""
        path = str(tmp_path / "quota.json")
        yesterday = (datetime.now(KST) - timedelta(days=1)).strftime("%Y-%m-%d")
        with open(path, "w") as f:
            json.dump({"date": yesterday, "calls_today": 500}, f)

        result = read_quota(path)
        assert result["calls_today"] == 0

    def test_read_quota_today_preserves(self, tmp_path):
        """오늘 날짜 쿼터 파일은 값 보존."""
        path = str(tmp_path / "quota.json")
        today = datetime.now(KST).strftime("%Y-%m-%d")
        with open(path, "w") as f:
            json.dump({"date": today, "calls_today": 42}, f)

        result = read_quota(path)
        assert result["calls_today"] == 42

    def test_read_quota_corrupted_file(self, tmp_path):
        """손상된 파일은 0으로 리셋."""
        path = str(tmp_path / "quota.json")
        with open(path, "w") as f:
            f.write("NOT JSON")

        result = read_quota(path)
        assert result["calls_today"] == 0

    def test_increment_quota_atomic(self, tmp_path):
        """increment_quota 원자적 증가 확인."""
        path = str(tmp_path / "quota.json")
        count1 = increment_quota(path)
        count2 = increment_quota(path)
        assert count1 == 1
        assert count2 == 2

        # 파일 내용 검증
        with open(path) as f:
            data = json.load(f)
        assert data["calls_today"] == 2

    def test_check_quota_enforces_limit(self, tmp_path):
        """한도 도달 시 False 반환."""
        path = str(tmp_path / "quota.json")
        today = datetime.now(KST).strftime("%Y-%m-%d")
        with open(path, "w") as f:
            json.dump({"date": today, "calls_today": 1000}, f)

        assert check_quota(max_daily=1000, quota_path=path) is False

    def test_check_quota_within_limit(self, tmp_path):
        """한도 미만 시 True 반환."""
        path = str(tmp_path / "quota.json")
        today = datetime.now(KST).strftime("%Y-%m-%d")
        with open(path, "w") as f:
            json.dump({"date": today, "calls_today": 999}, f)

        assert check_quota(max_daily=1000, quota_path=path) is True


# ──────────────────────────────────────────────
# Naver DataLab 클라이언트 테스트
# ──────────────────────────────────────────────

# 네이버 API 샘플 응답
NAVER_SAMPLE_RESPONSE = {
    "results": [
        {
            "title": "코딩학원",
            "keywords": ["코딩학원"],
            "data": [
                {"period": "2026-01-05", "ratio": 45.0},
                {"period": "2026-01-12", "ratio": 50.0},
            ],
        },
        {
            "title": "프로그래밍학원",
            "keywords": ["프로그래밍학원"],
            "data": [
                {"period": "2026-01-05", "ratio": 30.0},
                {"period": "2026-01-12", "ratio": 35.0},
            ],
        },
    ]
}


class TestNaverDatalab:
    """네이버 DataLab API 클라이언트 테스트."""

    @patch("edupulse.collection.api.naver_datalab.httpx.Client")
    def test_fetch_naver_trends_success(self, mock_client_cls):
        """성공적 API 호출 시 결과 반환."""
        from edupulse.collection.api.naver_datalab import fetch_naver_trends

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = NAVER_SAMPLE_RESPONSE

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        results = fetch_naver_trends(
            ["코딩학원"], "2026-01-01", "2026-03-31", "test_id", "test_secret",
        )
        assert len(results) == 2
        assert results[0]["title"] == "코딩학원"

    @patch("edupulse.collection.api.naver_datalab.time.sleep")
    @patch("edupulse.collection.api.naver_datalab.httpx.Client")
    def test_fetch_naver_trends_retry_on_429(self, mock_client_cls, mock_sleep):
        """429 응답 시 재시도."""
        from edupulse.collection.api.naver_datalab import fetch_naver_trends

        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.text = "Too Many Requests"

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = NAVER_SAMPLE_RESPONSE

        mock_client = MagicMock()
        mock_client.post.side_effect = [mock_429, mock_200]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        results = fetch_naver_trends(
            ["코딩학원"], "2026-01-01", "2026-03-31", "test_id", "test_secret",
        )
        assert len(results) == 2
        mock_sleep.assert_called_once_with(1)

    @patch("edupulse.collection.api.naver_datalab.httpx.Client")
    def test_fetch_naver_trends_fail_on_400(self, mock_client_cls):
        """400 응답 시 즉시 실패 (재시도 없음)."""
        from edupulse.collection.api.naver_datalab import NaverAPIError, fetch_naver_trends

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(NaverAPIError, match="400"):
            fetch_naver_trends(
                ["코딩학원"], "2026-01-01", "2026-03-31", "test_id", "test_secret",
            )

    @patch("edupulse.collection.api.naver_datalab.time.sleep")
    @patch("edupulse.collection.api.naver_datalab.httpx.Client")
    def test_fetch_naver_trends_max_retries(self, mock_client_cls, mock_sleep):
        """3회 재시도 후 NaverAPIError 발생."""
        from edupulse.collection.api.naver_datalab import NaverAPIError, fetch_naver_trends

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(NaverAPIError):
            fetch_naver_trends(
                ["코딩학원"], "2026-01-01", "2026-03-31", "test_id", "test_secret",
            )
        assert mock_sleep.call_count == 3

    @patch("edupulse.collection.api.naver_datalab.fetch_naver_trends")
    def test_fetch_field_trends_aggregation(self, mock_fetch):
        """키워드별 ratio를 주간 단위로 합산."""
        from edupulse.collection.api.naver_datalab import fetch_field_trends

        mock_fetch.return_value = NAVER_SAMPLE_RESPONSE["results"]

        df = fetch_field_trends("coding", "2026-01-01", "2026-03-31", "id", "secret")

        assert list(df.columns) == ["date", "field", "search_volume", "ds", "y"]
        assert len(df) == 2
        # 2026-01-05: 45 + 30 = 75
        assert df.iloc[0]["search_volume"] == 75
        # 2026-01-12: 50 + 35 = 85
        assert df.iloc[1]["search_volume"] == 85
        assert (df["field"] == "coding").all()

    @patch("edupulse.collection.api.naver_datalab.fetch_naver_trends")
    def test_fetch_field_trends_output_schema(self, mock_fetch):
        """출력 스키마 검증: [date, field, search_volume, ds, y]."""
        from edupulse.collection.api.naver_datalab import fetch_field_trends

        mock_fetch.return_value = NAVER_SAMPLE_RESPONSE["results"]

        df = fetch_field_trends("coding", "2026-01-01", "2026-03-31", "id", "secret")

        expected_cols = ["date", "field", "search_volume", "ds", "y"]
        assert list(df.columns) == expected_cols
        assert pd.api.types.is_datetime64_any_dtype(df["date"])
        assert pd.api.types.is_datetime64_any_dtype(df["ds"])
        assert df["search_volume"].dtype in ("int64", "int32")
        assert (df["y"] == df["search_volume"]).all()


# ──────────────────────────────────────────────
# Google Trends 클라이언트 테스트
# ──────────────────────────────────────────────


class TestGoogleTrends:
    """Google Trends 클라이언트 테스트 (캐시 전용)."""

    @patch("pytrends.request.TrendReq")
    def test_fetch_google_trends_success(self, mock_trendreq_cls):
        """성공적 수집 시 DataFrame 반환."""
        from edupulse.collection.api.google_trends import fetch_google_trends

        mock_pytrends = MagicMock()
        mock_trendreq_cls.return_value = mock_pytrends
        mock_df = pd.DataFrame(
            {"coding bootcamp": [10, 20, 30]},
            index=pd.date_range("2026-01-01", periods=3, freq="W"),
        )
        mock_pytrends.interest_over_time.return_value = mock_df

        result = fetch_google_trends(["coding bootcamp"])
        assert result is not None
        assert len(result) == 3

    @patch("pytrends.request.TrendReq")
    def test_fetch_google_trends_failure_returns_none(self, mock_trendreq_cls):
        """일반 예외 시 None 반환 (크래시 아님)."""
        from edupulse.collection.api.google_trends import fetch_google_trends

        mock_pytrends = MagicMock()
        mock_trendreq_cls.return_value = mock_pytrends
        mock_pytrends.interest_over_time.side_effect = RuntimeError("Connection failed")

        result = fetch_google_trends(["coding bootcamp"])
        assert result is None


# ──────────────────────────────────────────────
# 오케스트레이터 테스트
# ──────────────────────────────────────────────


class TestCollectSearchTrends:
    """수집 오케스트레이터 테스트."""

    def _make_sample_df(self) -> pd.DataFrame:
        """테스트용 샘플 DataFrame 생성."""
        return pd.DataFrame({
            "date": pd.to_datetime(["2026-01-05", "2026-01-12"]),
            "field": ["coding", "coding"],
            "search_volume": [75, 85],
            "ds": pd.to_datetime(["2026-01-05", "2026-01-12"]),
            "y": [75, 85],
        })

    @patch("edupulse.collection.api.collect_search_trends._try_fetch_naver")
    def test_collect_fresh_naver_data(self, mock_naver, tmp_path):
        """신규 네이버 데이터 정상 저장."""
        from edupulse.collection.api.collect_search_trends import collect_search_trends

        mock_naver.return_value = self._make_sample_df()
        output = str(tmp_path / "search_trends.csv")

        result = collect_search_trends(output_path=output)

        assert result == output
        assert os.path.exists(output)
        df = pd.read_csv(output)
        assert list(df.columns) == ["date", "field", "search_volume", "ds", "y"]
        assert len(df) == 2

    @patch("edupulse.collection.api.collect_search_trends._load_cached_naver")
    @patch("edupulse.collection.api.collect_search_trends._try_fetch_naver")
    def test_collect_fallback_to_cache(self, mock_naver, mock_cache, tmp_path):
        """API 실패 시 캐시 데이터 사용."""
        from edupulse.collection.api.collect_search_trends import collect_search_trends

        mock_naver.return_value = None
        mock_cache.return_value = self._make_sample_df()
        output = str(tmp_path / "search_trends.csv")

        result = collect_search_trends(output_path=output)

        assert result == output
        mock_cache.assert_called_once()

    @patch("edupulse.collection.api.collect_search_trends._load_cached_naver")
    @patch("edupulse.collection.api.collect_search_trends._try_fetch_naver")
    def test_collect_no_cache_skips(self, mock_naver, mock_cache, tmp_path):
        """API 실패 + 캐시 없음 → None 반환."""
        from edupulse.collection.api.collect_search_trends import collect_search_trends

        mock_naver.return_value = None
        mock_cache.return_value = None
        output = str(tmp_path / "search_trends.csv")

        result = collect_search_trends(output_path=output)

        assert result is None
        assert not os.path.exists(output)

    @patch("edupulse.collection.api.collect_search_trends._try_fetch_naver")
    def test_google_never_in_output(self, mock_naver, tmp_path):
        """Google 데이터가 출력 CSV에 절대 포함되지 않음을 검증."""
        from edupulse.collection.api.collect_search_trends import collect_search_trends

        mock_naver.return_value = self._make_sample_df()
        output = str(tmp_path / "search_trends.csv")

        result = collect_search_trends(output_path=output, also_cache_google=False)

        df = pd.read_csv(result)
        # source 컬럼이 없어야 함
        assert "source" not in df.columns
        # 출력 스키마 정확히 5개 컬럼
        assert list(df.columns) == ["date", "field", "search_volume", "ds", "y"]

    @patch("edupulse.collection.api.collect_search_trends._try_fetch_naver")
    def test_output_compatible_with_merger(self, mock_naver, tmp_path):
        """출력 CSV가 merger.py와 호환되는지 검증."""
        from edupulse.collection.api.collect_search_trends import collect_search_trends
        from edupulse.preprocessing.merger import merge_datasets

        # 수집기로 CSV 생성
        sample = self._make_sample_df()
        mock_naver.return_value = sample
        output = str(tmp_path / "search_trends.csv")
        collect_search_trends(output_path=output)

        # merger에서 읽기
        search_df = pd.read_csv(output)
        enrollment_df = pd.DataFrame({
            "date": pd.to_datetime(["2026-01-05", "2026-01-12"]),
            "field": ["coding", "coding"],
            "enrollment_count": [5, 6],
        })

        merged = merge_datasets(enrollment_df, search_df)
        assert "search_volume" in merged.columns
        assert len(merged) == 2

    def test_normalize_to_weekly_daily_input(self):
        """일간 입력을 주간(월요일)으로 정규화."""
        from edupulse.collection.api.collect_search_trends import normalize_to_weekly

        df = pd.DataFrame({
            "date": pd.to_datetime([
                "2026-01-05", "2026-01-06", "2026-01-07",  # 같은 주
                "2026-01-12",                                # 다음 주
            ]),
            "field": ["coding"] * 4,
            "search_volume": [10, 20, 30, 40],
        })

        result = normalize_to_weekly(df)
        assert len(result) == 2
        # 같은 주 합산: 10+20+30 = 60
        assert result.iloc[0]["search_volume"] == 60
        assert result.iloc[1]["search_volume"] == 40

    def test_normalize_to_weekly_weekly_input(self):
        """주간 입력은 그대로 통과."""
        from edupulse.collection.api.collect_search_trends import normalize_to_weekly

        df = pd.DataFrame({
            "date": pd.to_datetime(["2026-01-05", "2026-01-12"]),
            "field": ["coding", "coding"],
            "search_volume": [75, 85],
        })

        result = normalize_to_weekly(df)
        assert len(result) == 2
        assert list(result["search_volume"]) == [75, 85]

    @patch("edupulse.collection.api.collect_search_trends._try_fetch_naver")
    def test_atomic_write_no_corruption(self, mock_naver, tmp_path):
        """기존 파일이 있을 때 원자적 쓰기로 손상 방지."""
        from edupulse.collection.api.collect_search_trends import collect_search_trends

        output = str(tmp_path / "search_trends.csv")
        # 기존 파일 생성
        with open(output, "w") as f:
            f.write("existing,data\n")

        mock_naver.return_value = self._make_sample_df()
        collect_search_trends(output_path=output)

        # 새 파일로 대체됨
        df = pd.read_csv(output)
        assert "search_volume" in df.columns
        # .tmp 파일이 남아있지 않음
        assert not os.path.exists(output + ".tmp")
