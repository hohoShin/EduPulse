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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 모델 로딩."""
    load_models()
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
