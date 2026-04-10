"""Health check 라우터."""
import resource

from fastapi import APIRouter

from edupulse.api.dependencies import get_loaded_model_names

router = APIRouter()


@router.get("/health")
def health_check():
    """서버 상태 및 모델 로딩 여부 반환."""
    models_loaded = get_loaded_model_names()

    # DB 연결 확인 (연결 실패 시 False 반환)
    db_connected = False
    try:
        from edupulse.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    # 메모리 사용량 (rusage 기반, MB 단위)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss: macOS는 bytes, Linux는 kilobytes
    import platform
    if platform.system() == "Darwin":
        memory_usage_mb = round(usage.ru_maxrss / 1024 / 1024, 1)
    else:
        memory_usage_mb = round(usage.ru_maxrss / 1024, 1)

    return {
        "status": "ok",
        "models_loaded": models_loaded,
        "db_connected": db_connected,
        "memory_usage_mb": memory_usage_mb,
    }
