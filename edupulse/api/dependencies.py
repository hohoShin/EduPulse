"""DB 세션 및 모델 레지스트리 의존성 주입.

모델 로딩은 predict.load_model()에 위임하여 이중 캐시 문제를 방지한다.
"""
from fastapi import HTTPException

from edupulse.database import SessionLocal
from edupulse.model.predict import MODEL_VERSION, _model_cache, load_model as _load_model


def get_loaded_model_names() -> list[str]:
    """현재 캐시에 로딩된 모델 이름 목록 반환 (버전 접미사 제거)."""
    return [key.rsplit("_v", 1)[0] for key in _model_cache]


def load_models() -> None:
    """서버 시작 시 모델 프리로딩. predict.load_model() 캐시에 등록."""
    for name in ("xgboost", "prophet", "lstm", "ensemble"):
        try:
            _load_model(name, version=MODEL_VERSION)
        except Exception:
            pass  # 미설치/미학습 모델은 건너뜀


def get_model(name: str = "ensemble"):
    """모델 반환. 미로딩 시 503.

    'ensemble' 요청 시 실패하면 xgboost로 fallback.

    Args:
        name: 모델 이름

    Returns:
        BaseForecaster 인스턴스
    """
    try:
        return _load_model(name, version=MODEL_VERSION)
    except Exception:
        pass
    # ensemble fallback → xgboost
    if name == "ensemble":
        try:
            return _load_model("xgboost", version=MODEL_VERSION)
        except Exception:
            pass
    raise HTTPException(status_code=503, detail=f"Model '{name}' not loaded")


def get_db():
    """DB 세션 의존성 주입. Sync SessionLocal."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
