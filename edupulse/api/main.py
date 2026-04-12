"""FastAPI 앱 진입점.

실행:
    uvicorn edupulse.api.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from edupulse.api.dependencies import load_models
from edupulse.api.middleware import setup_middleware
from edupulse.api.routers import health, demand, schedule, marketing, simulation

logger = logging.getLogger(__name__)


def _auto_generate_csv():
    """CSV 데이터가 없으면 합성 데이터를 자동 생성한다."""
    import os
    from edupulse.constants import ENROLLMENT_PATH

    if os.path.exists(ENROLLMENT_PATH):
        logger.info("CSV 데이터 존재, 합성 생성 건너뜀")
        return

    try:
        logger.info("CSV 데이터 없음 — 합성 데이터 자동 생성 시작")
        from datetime import date
        from edupulse.data.generators.run_all import run
        n_years = date.today().year - 2018 + 1  # 2018~현재 연도 커버
        run(n_years=n_years, start_year=2018)
        logger.info("합성 데이터 자동 생성 완료 (2018~%d)", 2018 + n_years - 1)
    except Exception as e:
        logger.warning("합성 데이터 자동 생성 실패 (무시): %s", e)


def _auto_seed_instructors():
    """강사 테이블이 비어있으면 시드 데이터를 자동 투입한다."""
    try:
        from edupulse.database import SessionLocal, engine, Base
        from edupulse.db_models.instructor import Instructor

        Base.metadata.create_all(engine)
        session = SessionLocal()
        try:
            count = session.query(Instructor).count()
            if count == 0:
                from scripts.seed_instructors import seed_instructors
                seed_instructors()
                logger.info("강사 시드 데이터 자동 투입 완료")
            else:
                logger.info("강사 데이터 존재 (%d명), 시딩 건너뜀", count)
        finally:
            session.close()
    except Exception as e:
        logger.warning("강사 자동 시딩 실패 (무시): %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 모델 로딩 및 강사 시드 데이터 투입."""
    _auto_generate_csv()
    load_models()
    _auto_seed_instructors()
    yield


app = FastAPI(
    title="EduPulse API",
    description="AI-based course enrollment demand forecasting",
    version="0.1.0",
    lifespan=lifespan,
)

setup_middleware(app)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(demand.router, prefix="/api/v1", tags=["demand"])
app.include_router(schedule.router, prefix="/api/v1", tags=["schedule"])
app.include_router(marketing.router, prefix="/api/v1", tags=["marketing"])
app.include_router(simulation.router, prefix="/api/v1", tags=["simulation"])
