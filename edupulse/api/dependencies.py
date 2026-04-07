"""DB 세션 및 모델 레지스트리 의존성 주입."""
import threading

from fastapi import HTTPException

from edupulse.database import SessionLocal

MODEL_REGISTRY: dict = {}
_registry_lock = threading.Lock()


def load_models() -> None:
    """서버 시작 시 모델 로딩. XGBoost는 항상 시도; Prophet/Ensemble은 선택적."""
    # XGBoost
    try:
        from edupulse.model.xgboost_model import XGBoostForecaster

        xgb = XGBoostForecaster()
        xgb.load("edupulse/model/saved/xgboost", version=1)
        with _registry_lock:
            MODEL_REGISTRY["xgboost"] = xgb
    except Exception:
        pass  # 모델 미학습 상태 — health check에서 표시

    # Prophet (선택적 — 미설치 환경 안전)
    try:
        from edupulse.model.prophet_model import ProphetForecaster

        prophet = ProphetForecaster()
        prophet.load("edupulse/model/saved/prophet", version=1)
        with _registry_lock:
            MODEL_REGISTRY["prophet"] = prophet
    except Exception:
        pass

    # Ensemble — 로딩된 모델로 구성
    try:
        from edupulse.model.ensemble import EnsembleForecaster

        ensemble = EnsembleForecaster()
        with _registry_lock:
            for name in ("xgboost", "prophet"):
                if name in MODEL_REGISTRY:
                    ensemble.add_model(name, MODEL_REGISTRY[name])

        # LSTM은 파일이 있을 때만 추가 (MacBook에서 학습 후 전송)
        try:
            from edupulse.model.lstm_model import LSTMForecaster

            lstm = LSTMForecaster()
            lstm.load("edupulse/model/saved/lstm", version=1)
            ensemble.add_model("lstm", lstm)
            with _registry_lock:
                MODEL_REGISTRY["lstm"] = lstm
        except Exception:
            pass

        if ensemble.model_count > 0:
            with _registry_lock:
                MODEL_REGISTRY["ensemble"] = ensemble
    except Exception:
        pass


def get_model(name: str = "ensemble"):
    """모델 레지스트리에서 모델 반환. 미로딩 시 503.

    'ensemble' 요청 시 ensemble이 없으면 xgboost로 fallback.

    Args:
        name: 모델 이름

    Returns:
        BaseForecaster 인스턴스
    """
    with _registry_lock:
        if name in MODEL_REGISTRY:
            return MODEL_REGISTRY[name]
        # ensemble fallback → xgboost
        if name == "ensemble" and "xgboost" in MODEL_REGISTRY:
            return MODEL_REGISTRY["xgboost"]
    raise HTTPException(status_code=503, detail=f"Model '{name}' not loaded")


def get_db():
    """DB 세션 의존성 주입. Sync SessionLocal."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
