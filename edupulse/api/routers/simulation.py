"""시뮬레이션 API 라우터 — 개강일 최적화, 신규 과정 시뮬레이션, 인구통계, 경쟁사 분석."""
from fastapi import APIRouter

from edupulse.api.schemas.simulation import (
    CompetitorRequest,
    CompetitorResponse,
    DemographicsRequest,
    DemographicsResponse,
    OptimalStartRequest,
    OptimalStartResponse,
    SimulateRequest,
    SimulateResponse,
    StartDateCandidate,
)
from edupulse.api.services import simulation_service

router = APIRouter()


@router.post("/simulation/optimal-start", response_model=OptimalStartResponse)
def find_optimal_start(request: OptimalStartRequest) -> OptimalStartResponse:
    """검색 윈도우 내 최적 개강일 후보 반환 (최대 5개).

    각 월요일 후보에 대해 수요 예측 및 채용/경쟁 데이터를 종합하여
    복합 점수 기준 상위 5개 날짜를 추천한다.
    """
    candidates_raw = simulation_service.find_optimal_start_dates(
        course_name=request.course_name,
        field=request.field,
        window_start=request.search_window_start,
        window_end=request.search_window_end,
    )
    candidates = [StartDateCandidate(**c) for c in candidates_raw]
    return OptimalStartResponse(top_candidates=candidates)


@router.post("/simulation/simulate", response_model=SimulateResponse)
def simulate_new_course(request: SimulateRequest) -> SimulateResponse:
    """신규 과정 개설 시나리오 시뮬레이션.

    기준/낙관/비관 세 시나리오의 예상 수강생 수와 매출을 반환한다.
    시장 컨텍스트(경쟁사 개강 수, 검색량 추세)를 함께 제공한다.
    """
    result = simulation_service.simulate_new_course(
        course_name=request.course_name,
        field=request.field,
        start_date=request.start_date,
        price_per_student=request.price_per_student,
    )
    return SimulateResponse(**result)


@router.post("/simulation/demographics", response_model=DemographicsResponse)
def get_demographics(request: DemographicsRequest) -> DemographicsResponse:
    """분야별 수강생 인구통계 분석.

    연령대 분포, 수강 목적 분포, 최근 수강생 수 추세를 반환한다.
    """
    result = simulation_service.get_demographics_breakdown(field=request.field)
    return DemographicsResponse(**result)


@router.post("/simulation/competitors", response_model=CompetitorResponse)
def get_competitor_analysis(request: CompetitorRequest) -> CompetitorResponse:
    """분야별 경쟁사 현황 분석.

    경쟁사 개강 수, 평균 수강료, 시장 포화도 지수와
    전략적 권고안을 반환한다.
    """
    result = simulation_service.get_competitor_analysis(field=request.field)
    return CompetitorResponse(**result)
