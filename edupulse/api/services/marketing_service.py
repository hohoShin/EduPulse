"""마케팅 비즈니스 로직 서비스 레이어."""
import logging

from edupulse.constants import CONSULTATION_PATH, WEB_LOGS_PATH
from edupulse.model.predict import load_csv_cached

logger = logging.getLogger(__name__)

# 기본 전환율 (상담 → 등록). 실제 데이터 확보 시 분야별 동적 계산으로 전환 예정.
DEFAULT_CONVERSION_RATE = 0.3


def predict_lead_conversion(field: str) -> dict:
    """잠재 수강생 전환율 예측.

    consultation_logs.csv + web_logs.csv를 집계하여 최근 8주간
    상담 건수 추세를 분석하고, 예상 전환 수강생 수와
    마케팅 권고안을 반환한다.

    Args:
        field: 분야 ('coding', 'security', 'game', 'art')

    Returns:
        estimated_conversions, consultation_count_trend,
        recommendations를 포함한 dict
    """
    import pandas as pd

    consult_df = load_csv_cached(CONSULTATION_PATH)
    web_df = load_csv_cached(WEB_LOGS_PATH)

    consultation_count_trend: list[int] = []
    estimated_conversions = 0
    recommendations: list[dict] = []

    # consultation_logs.csv: 상담 건수 추세
    if consult_df is not None and len(consult_df) > 0 and "field" in consult_df.columns:
        try:
            cdf = consult_df.copy()
            cdf["date"] = pd.to_datetime(cdf["date"])
            field_df = cdf[cdf["field"] == field].sort_values("date")

            if len(field_df) > 0:
                recent = field_df.tail(8)

                if "consultation_count" in recent.columns:
                    consultation_count_trend = [int(v) for v in recent["consultation_count"].tolist()]

        except Exception as exc:
            logger.warning("상담 로그 집계 실패 (field=%s): %s", field, exc)

    # web_logs.csv: page_views 기반 보완 (상담 데이터 없을 때)
    if not consultation_count_trend and web_df is not None and len(web_df) > 0 and "field" in web_df.columns:
        try:
            wdf = web_df.copy()
            wdf["date"] = pd.to_datetime(wdf["date"])
            field_web = wdf[wdf["field"] == field].sort_values("date")

            if len(field_web) > 0:
                recent_web = field_web.tail(8)
                if "page_views" in recent_web.columns:
                    # page_views를 상담 건수 대리 지표로 활용 (스케일 조정)
                    consultation_count_trend = [
                        int(float(v) / 100.0) for v in recent_web["page_views"].tolist()
                    ]
        except Exception as exc:
            logger.warning("웹 로그 집계 실패 (field=%s): %s", field, exc)

    # 예상 전환 수강생 수 계산 (기본 전환율 적용)
    previous_conversions: int | None = None
    current_demand_tier: str | None = None

    if consultation_count_trend:
        avg_consultation_count = sum(consultation_count_trend) / len(consultation_count_trend)
        estimated_conversions = max(0, int(avg_consultation_count * DEFAULT_CONVERSION_RATE))

        # previous_conversions: 전반부 평균 기반
        mid = len(consultation_count_trend) // 2
        first_half = consultation_count_trend[:mid]
        second_half = consultation_count_trend[mid:]
        if first_half:
            prev_avg = sum(first_half) / len(first_half)
            previous_conversions = int(prev_avg * DEFAULT_CONVERSION_RATE)

        # current_demand_tier: 후반부 vs 전반부 비교
        if first_half and second_half:
            recent_avg = sum(second_half) / len(second_half)
            older_avg = sum(first_half) / len(first_half)
            if older_avg > 0:
                if recent_avg > older_avg * 1.05:
                    current_demand_tier = "High"
                elif recent_avg < older_avg * 0.95:
                    current_demand_tier = "Low"
                else:
                    current_demand_tier = "Mid"
            else:
                current_demand_tier = "Mid"

    # 추세 분석 및 권고안 생성
    recommendations = _generate_recommendations(
        field=field,
        consultation_count_trend=consultation_count_trend,
    )

    return {
        "estimated_conversions": estimated_conversions,
        "consultation_count_trend": consultation_count_trend,
        "recommendations": recommendations,
        "previous_conversions": previous_conversions,
        "current_demand_tier": current_demand_tier,
    }


def _generate_recommendations(
    field: str,
    consultation_count_trend: list[int],
) -> list[dict]:
    """추세 방향에 따라 마케팅 권고안 생성.

    Args:
        field: 분야
        consultation_count_trend: 최근 8주 상담 건수 목록

    Returns:
        마케팅 권고안 dict 리스트 (text, link 포함)
    """
    recs: list[dict] = []

    def _trend_direction(values: list[int]) -> str:
        """목록의 후반부 평균과 전반부 평균을 비교하여 추세 반환."""
        if len(values) < 2:
            return "stable"
        mid = len(values) // 2
        recent_avg = sum(values[mid:]) / len(values[mid:])
        older_avg = sum(values[:mid]) / len(values[:mid]) if values[:mid] else recent_avg
        if older_avg == 0:
            return "stable"
        change_rate = (recent_avg - older_avg) / abs(older_avg)
        if change_rate > 0.05:
            return "up"
        elif change_rate < -0.05:
            return "down"
        return "stable"

    consult_direction = _trend_direction(consultation_count_trend) if consultation_count_trend else "stable"

    # 상담 건수 추세 기반 권고
    if consult_direction == "up":
        recs.append({
            "text": "상담 문의가 증가하고 있습니다. 상담 인력 확충 또는 자동 응답 시스템 도입을 검토하세요.",
            "link": "/operations",
        })
    elif consult_direction == "down":
        recs.append({
            "text": "상담 문의가 감소하고 있습니다. SNS 광고 또는 콘텐츠 마케팅 강화를 권장합니다.",
            "link": "/marketing",
        })
    else:
        recs.append({
            "text": "상담 문의가 일정 수준을 유지하고 있습니다. 리타게팅 광고로 잠재 수강생을 재유치하세요.",
            "link": "/marketing",
        })

    # 분야별 특화 권고
    field_tips = {
        "coding": "취업/이직 시즌(1~2월, 7~8월) 집중 광고를 권장합니다.",
        "security": "자격증 시험 일정에 맞춰 3~4주 전 집중 마케팅을 실시하세요.",
        "game": "게임쇼/콘퍼런스 시즌과 연계한 이벤트 마케팅을 고려하세요.",
        "art": "포트폴리오 공개 시즌 전후로 마케팅을 강화하세요.",
    }
    if field in field_tips:
        recs.append({"text": field_tips[field], "link": None})

    return recs
