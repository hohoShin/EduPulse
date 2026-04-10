"""시뮬레이션 비즈니스 로직 서비스 레이어."""
import logging
from datetime import date, timedelta

from edupulse.constants import (
    COMPETITOR_PATH,
    JOB_POSTINGS_PATH,
    SEARCH_TRENDS_PATH,
    SEASONAL_PATH,
    STUDENT_PROFILES_PATH,
    classify_demand,
)
from edupulse.model.predict import load_csv_cached

logger = logging.getLogger(__name__)


def _next_monday(d: date) -> date:
    """주어진 날짜 이후 첫 번째 월요일 반환 (당일 포함)."""
    days_ahead = (7 - d.weekday()) % 7
    return d + timedelta(days=days_ahead)


def find_optimal_start_dates(
    course_name: str,
    field: str,
    window_start: date,
    window_end: date,
) -> list[dict]:
    """검색 윈도우 내 최적 개강일 후보 반환 (최대 5개).

    각 월요일 후보에 대해 수요 예측을 수행하고 복합 점수를 계산하여
    상위 5개를 반환한다.

    Args:
        course_name: 과정명
        field: 분야 ('coding', 'security', 'game', 'art')
        window_start: 검색 시작일
        window_end: 검색 종료일

    Returns:
        StartDateCandidate 형식의 dict 리스트 (composite_score 내림차순)
    """
    from edupulse.model.predict import predict_demand

    # 윈도우 내 모든 월요일 생성
    first_monday = _next_monday(window_start)
    mondays: list[date] = []
    current = first_monday
    while current <= window_end:
        mondays.append(current)
        current += timedelta(weeks=1)

    # 채용 공고 데이터 로딩 (job_score 계산용)
    job_df = load_csv_cached(JOB_POSTINGS_PATH)
    comp_df = load_csv_cached(COMPETITOR_PATH)

    # 분야별 채용 공고 평균 (정규화 기준)
    job_avg = 1.0
    if job_df is not None and "field" in job_df.columns and "job_count" in job_df.columns:
        field_jobs = job_df[job_df["field"] == field]
        if len(field_jobs) > 0:
            job_avg = max(field_jobs["job_count"].mean(), 1.0)

    # 분야별 경쟁사 개강 평균 (경쟁 강도 계산용)
    comp_avg = 1.0
    if comp_df is not None and "field" in comp_df.columns and "competitor_openings" in comp_df.columns:
        field_comp = comp_df[comp_df["field"] == field]
        if len(field_comp) > 0:
            comp_avg = max(field_comp["competitor_openings"].mean(), 1.0)

    candidates = []
    for monday in mondays:
        date_str = monday.isoformat()
        try:
            result = predict_demand(course_name, date_str, field)
            enrollment = result.predicted_enrollment
            tier = result.demand_tier
        except Exception as exc:
            logger.warning("수요 예측 실패 (%s): %s — 기본값 사용", date_str, exc)
            enrollment = 0
            tier = classify_demand(0)

        # 채용 공고 점수: 해당 날짜 이전 최근 job_count 정규화
        job_score = 0.0
        if job_df is not None and "date" in job_df.columns:
            try:
                import pandas as pd

                jdf = job_df.copy()
                jdf["date"] = pd.to_datetime(jdf["date"])
                prior = jdf[(jdf["field"] == field) & (jdf["date"] < pd.Timestamp(date_str))]
                if len(prior) > 0:
                    job_score = float(prior.sort_values("date").iloc[-1]["job_count"]) / job_avg
            except Exception as exc:
                logger.debug("job_score 계산 실패: %s", exc)

        # 경쟁 강도 낮을수록 유리 (low_competition = 1 - 포화도)
        low_competition = 1.0
        if comp_df is not None and "date" in comp_df.columns:
            try:
                import pandas as pd

                cdf = comp_df.copy()
                cdf["date"] = pd.to_datetime(cdf["date"])
                prior_c = cdf[(cdf["field"] == field) & (cdf["date"] < pd.Timestamp(date_str))]
                if len(prior_c) > 0:
                    current_openings = float(prior_c.sort_values("date").iloc[-1]["competitor_openings"])
                    saturation = min(current_openings / comp_avg, 2.0) / 2.0
                    low_competition = 1.0 - saturation
            except Exception as exc:
                logger.debug("low_competition 계산 실패: %s", exc)

        # 복합 점수 = enrollment*0.5 + job_score*0.3 + low_competition*0.2
        # enrollment 정규화: 최대값 기준 상대값 (0~1 범위로 후처리)
        composite_score = float(enrollment) * 0.5 + job_score * 0.3 + low_competition * 0.2

        candidates.append({
            "date": monday,
            "predicted_enrollment": enrollment,
            "demand_tier": tier,
            "composite_score": composite_score,
            "_raw_enrollment": float(enrollment),
        })

    if not candidates:
        return []

    # enrollment 정규화 (0~1): 전체 후보 중 최대 enrollment 기준
    max_enroll = max(c["_raw_enrollment"] for c in candidates) or 1.0
    for c in candidates:
        normalized = c["_raw_enrollment"] / max_enroll
        c["composite_score"] = normalized * 0.5 + (c["composite_score"] - c["_raw_enrollment"] * 0.5)
        del c["_raw_enrollment"]

    # composite_score 내림차순 정렬 후 상위 5개
    candidates.sort(key=lambda x: x["composite_score"], reverse=True)
    return candidates[:5]


def simulate_new_course(
    course_name: str,
    field: str,
    start_date: date,
    price_per_student: float,
) -> dict:
    """신규 과정 개설 시나리오 시뮬레이션.

    기준/낙관/비관 세 시나리오의 예상 수강생 수와 매출을 반환한다.

    Args:
        course_name: 과정명
        field: 분야
        start_date: 시작일
        price_per_student: 수강생 1인당 수강료 (원)

    Returns:
        baseline/optimistic/pessimistic ScenarioResult + market_context dict
    """
    from edupulse.model.predict import predict_demand

    date_str = start_date.isoformat()

    try:
        result = predict_demand(course_name, date_str, field)
        baseline_enrollment = result.predicted_enrollment
    except Exception as exc:
        logger.warning("수요 예측 실패: %s — 기본값 사용", exc)
        baseline_enrollment = 0

    optimistic_enrollment = max(1, int(baseline_enrollment * 1.2))
    pessimistic_enrollment = max(0, int(baseline_enrollment * 0.8))

    def make_scenario(scenario_name: str, enrollment: int) -> dict:
        return {
            "scenario": scenario_name,
            "predicted_enrollment": enrollment,
            "demand_tier": classify_demand(enrollment),
            "estimated_revenue": float(enrollment * price_per_student),
        }

    baseline = make_scenario("baseline", baseline_enrollment)
    optimistic = make_scenario("optimistic", optimistic_enrollment)
    pessimistic = make_scenario("pessimistic", pessimistic_enrollment)

    # 시장 컨텍스트 구성
    market_context = None
    try:
        import pandas as pd

        comp_df = load_csv_cached(COMPETITOR_PATH)
        search_df = load_csv_cached(SEARCH_TRENDS_PATH)

        comp_openings = 0
        comp_avg_price = 0.0
        if comp_df is not None and "date" in comp_df.columns:
            cdf = comp_df.copy()
            cdf["date"] = pd.to_datetime(cdf["date"])
            prior = cdf[(cdf["field"] == field) & (cdf["date"] <= pd.Timestamp(date_str))]
            if len(prior) > 0:
                last = prior.sort_values("date").iloc[-1]
                comp_openings = int(last.get("competitor_openings", 0))
                comp_avg_price = float(last.get("competitor_avg_price", 0.0))

        search_trend: list[float] = []
        if search_df is not None and "date" in search_df.columns:
            sdf = search_df.copy()
            sdf["date"] = pd.to_datetime(sdf["date"])
            field_search = sdf[sdf["field"] == field].sort_values("date")
            # 최근 8주 검색량 추세
            prior_search = field_search[field_search["date"] <= pd.Timestamp(date_str)]
            if len(prior_search) > 0:
                search_trend = prior_search.tail(8)["search_volume"].tolist()

        market_context = {
            "competitor_openings": comp_openings,
            "competitor_avg_price": comp_avg_price,
            "search_volume_trend": search_trend,
        }
    except Exception as exc:
        logger.warning("시장 컨텍스트 수집 실패: %s", exc)

    return {
        "baseline": baseline,
        "optimistic": optimistic,
        "pessimistic": pessimistic,
        "market_context": market_context,
    }


def get_demographics_breakdown(field: str) -> dict:
    """분야별 수강생 인구통계 분석.

    student_profiles.csv에서 연령대 및 수강 목적 분포를 집계한다.

    Args:
        field: 분야 ('coding', 'security', 'game', 'art')

    Returns:
        DemographicsResponse 형식의 dict
    """
    import pandas as pd

    profile_df = load_csv_cached(STUDENT_PROFILES_PATH)

    # 기본값 — 데이터 없을 때
    age_distribution = [
        {"group": "20대", "ratio": 0.0},
        {"group": "30대", "ratio": 0.0},
        {"group": "40대 이상", "ratio": 0.0},
    ]
    purpose_distribution: list[dict] = []
    trend = "데이터 없음"

    if profile_df is None or len(profile_df) == 0:
        return {
            "field": field,
            "age_distribution": age_distribution,
            "purpose_distribution": purpose_distribution,
            "trend": trend,
        }

    field_df = profile_df[profile_df["field"] == field].copy()
    if len(field_df) == 0:
        return {
            "field": field,
            "age_distribution": age_distribution,
            "purpose_distribution": purpose_distribution,
            "trend": trend,
        }

    # 연령대 분포 집계
    age_cols = {
        "20대": "age_20s_ratio",
        "30대": "age_30s_ratio",
        "40대 이상": "age_40plus_ratio",
    }
    age_distribution = []
    for label, col in age_cols.items():
        if col in field_df.columns:
            ratio = float(field_df[col].mean())
        else:
            ratio = 0.0
        age_distribution.append({"group": label, "ratio": round(ratio, 4)})

    # 수강 목적 분포 집계
    if "purpose" in field_df.columns:
        purpose_counts = field_df["purpose"].value_counts(normalize=True)
        purpose_distribution = [
            {"purpose": p, "ratio": round(float(r), 4)}
            for p, r in purpose_counts.items()
        ]
    else:
        purpose_distribution = []

    # 트렌드: 최근 절반 vs 이전 절반 수강생 수 비교
    if "date" in field_df.columns:
        try:
            field_df["date"] = pd.to_datetime(field_df["date"])
            field_df = field_df.sort_values("date")
            mid = len(field_df) // 2
            if mid > 0:
                recent_count = len(field_df.iloc[mid:])
                older_count = len(field_df.iloc[:mid])
                if recent_count > older_count * 1.05:
                    trend = "증가"
                elif recent_count < older_count * 0.95:
                    trend = "감소"
                else:
                    trend = "안정"
        except Exception as exc:
            logger.debug("트렌드 계산 실패: %s", exc)
            trend = "알 수 없음"

    return {
        "field": field,
        "age_distribution": age_distribution,
        "purpose_distribution": purpose_distribution,
        "trend": trend,
    }


def get_competitor_analysis(field: str) -> dict:
    """분야별 경쟁사 현황 분석.

    competitor_data.csv에서 경쟁사 개강 수와 평균 수강료 트렌드를 집계하고
    시장 포화도 지수를 계산한다.

    Args:
        field: 분야 ('coding', 'security', 'game', 'art')

    Returns:
        CompetitorResponse 형식의 dict
    """
    import pandas as pd

    comp_df = load_csv_cached(COMPETITOR_PATH)

    # 기본값
    default = {
        "field": field,
        "competitor_openings": 0,
        "competitor_avg_price": 0.0,
        "saturation_index": 0.0,
        "recommendation": "데이터 부족으로 분석 불가. 추후 데이터 수집 후 재분석 권장.",
    }

    if comp_df is None or len(comp_df) == 0:
        return default

    field_df = comp_df[comp_df["field"] == field].copy()
    if len(field_df) == 0:
        return default

    if "date" in field_df.columns:
        field_df["date"] = pd.to_datetime(field_df["date"])
        field_df = field_df.sort_values("date")

    # 현재값 (가장 최근 레코드)
    last_row = field_df.iloc[-1]
    current_openings = int(last_row.get("competitor_openings", 0)) if "competitor_openings" in field_df.columns else 0
    current_avg_price = float(last_row.get("competitor_avg_price", 0.0)) if "competitor_avg_price" in field_df.columns else 0.0

    # 평균값 (전체 기간)
    avg_openings = float(field_df["competitor_openings"].mean()) if "competitor_openings" in field_df.columns else 1.0
    avg_openings = max(avg_openings, 1.0)

    # 포화도 지수 = 현재 개강 수 / 평균 개강 수 (최대 2.0으로 상한)
    saturation_index = round(min(current_openings / avg_openings, 2.0), 4)

    # 추천 전략 생성
    if saturation_index >= 1.5:
        recommendation = "시장 포화 상태입니다. 차별화된 커리큘럼 또는 틈새 분야 집중을 권장합니다."
    elif saturation_index >= 1.0:
        recommendation = "경쟁이 활발합니다. 가격 경쟁력 또는 강사 전문성 강화를 권장합니다."
    elif saturation_index >= 0.5:
        recommendation = "적정 경쟁 수준입니다. 마케팅 강화로 시장 점유율 확대를 노려볼 수 있습니다."
    else:
        recommendation = "경쟁이 낮은 블루오션입니다. 선점 전략으로 적극적인 개강을 권장합니다."

    return {
        "field": field,
        "competitor_openings": current_openings,
        "competitor_avg_price": current_avg_price,
        "saturation_index": saturation_index,
        "recommendation": recommendation,
    }
