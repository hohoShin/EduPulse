"""마케팅 비즈니스 로직 서비스 레이어."""
import logging

from edupulse.constants import CONSULTATION_PATH, WEB_LOGS_PATH
from edupulse.model.predict import load_csv_cached

logger = logging.getLogger(__name__)


def predict_lead_conversion(field: str) -> dict:
    """잠재 수강생 전환율 예측.

    consultation_logs.csv + web_logs.csv를 집계하여 최근 8주간
    전환율 추세와 상담 건수 추세를 분석하고, 예상 전환 수강생 수와
    마케팅 권고안을 반환한다.

    Args:
        field: 분야 ('coding', 'security', 'game', 'art')

    Returns:
        estimated_conversions, conversion_rate_trend, consultation_count_trend,
        recommendations를 포함한 dict
    """
    import pandas as pd

    consult_df = load_csv_cached(CONSULTATION_PATH)
    web_df = load_csv_cached(WEB_LOGS_PATH)

    conversion_rate_trend: list[float] = []
    consultation_count_trend: list[float] = []
    estimated_conversions = 0
    recommendations: list[str] = []

    # consultation_logs.csv: 전환율 + 상담 건수 추세
    if consult_df is not None and len(consult_df) > 0 and "field" in consult_df.columns:
        try:
            cdf = consult_df.copy()
            cdf["date"] = pd.to_datetime(cdf["date"])
            field_df = cdf[cdf["field"] == field].sort_values("date")

            if len(field_df) > 0:
                # 최근 8주 데이터 추출
                recent = field_df.tail(8)

                if "conversion_rate" in recent.columns:
                    conversion_rate_trend = [round(float(v), 4) for v in recent["conversion_rate"].tolist()]

                if "consultation_count" in recent.columns:
                    consultation_count_trend = [round(float(v), 4) for v in recent["consultation_count"].tolist()]

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
                        round(float(v) / 100.0, 2) for v in recent_web["page_views"].tolist()
                    ]
        except Exception as exc:
            logger.warning("웹 로그 집계 실패 (field=%s): %s", field, exc)

    # 예상 전환 수강생 수 계산
    if conversion_rate_trend and consultation_count_trend:
        avg_conversion_rate = sum(conversion_rate_trend) / len(conversion_rate_trend)
        avg_consultation_count = sum(consultation_count_trend) / len(consultation_count_trend)
        estimated_conversions = max(0, int(avg_consultation_count * avg_conversion_rate))
    elif consultation_count_trend:
        avg_consultation_count = sum(consultation_count_trend) / len(consultation_count_trend)
        estimated_conversions = max(0, int(avg_consultation_count * 0.3))  # 기본 전환율 30%

    # 추세 분석 및 권고안 생성
    recommendations = _generate_recommendations(
        field=field,
        conversion_rate_trend=conversion_rate_trend,
        consultation_count_trend=consultation_count_trend,
    )

    return {
        "estimated_conversions": estimated_conversions,
        "conversion_rate_trend": conversion_rate_trend,
        "consultation_count_trend": consultation_count_trend,
        "recommendations": recommendations,
    }


def _generate_recommendations(
    field: str,
    conversion_rate_trend: list[float],
    consultation_count_trend: list[float],
) -> list[str]:
    """추세 방향에 따라 마케팅 권고안 생성.

    Args:
        field: 분야
        conversion_rate_trend: 최근 8주 전환율 목록
        consultation_count_trend: 최근 8주 상담 건수 목록

    Returns:
        마케팅 권고안 문자열 리스트
    """
    recs: list[str] = []

    def _trend_direction(values: list[float]) -> str:
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

    conv_direction = _trend_direction(conversion_rate_trend) if conversion_rate_trend else "stable"
    consult_direction = _trend_direction(consultation_count_trend) if consultation_count_trend else "stable"

    # 전환율 추세 기반 권고
    if conv_direction == "up":
        recs.append("전환율이 상승 중입니다. 현재 마케팅 메시지와 채널을 유지하세요.")
    elif conv_direction == "down":
        recs.append("전환율이 하락 중입니다. 랜딩 페이지 개선 및 상담 프로세스 점검을 권장합니다.")
    else:
        recs.append("전환율이 안정적입니다. A/B 테스트로 추가 최적화를 시도해보세요.")

    # 상담 건수 추세 기반 권고
    if consult_direction == "up":
        recs.append("상담 문의가 증가하고 있습니다. 상담 인력 확충 또는 자동 응답 시스템 도입을 검토하세요.")
    elif consult_direction == "down":
        recs.append("상담 문의가 감소하고 있습니다. SNS 광고 또는 콘텐츠 마케팅 강화를 권장합니다.")
    else:
        recs.append("상담 문의가 일정 수준을 유지하고 있습니다. 리타게팅 광고로 잠재 수강생을 재유치하세요.")

    # 분야별 특화 권고
    field_tips = {
        "coding": "취업/이직 시즌(1~2월, 7~8월) 집중 광고를 권장합니다.",
        "security": "자격증 시험 일정에 맞춰 3~4주 전 집중 마케팅을 실시하세요.",
        "game": "게임쇼/콘퍼런스 시즌과 연계한 이벤트 마케팅을 고려하세요.",
        "art": "포트폴리오 공개 시즌 전후로 마케팅을 강화하세요.",
    }
    if field in field_tips:
        recs.append(field_tips[field])

    return recs
