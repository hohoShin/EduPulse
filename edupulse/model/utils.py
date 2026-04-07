"""모델 유틸리티. classify_demand()는 edupulse.constants에서 import하여 사용."""
from edupulse.constants import classify_demand  # noqa: F401 — re-export


def get_device():
    """디바이스 감지. torch 미설치 환경(Droplet)에서도 안전."""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")    # M4 MacBook
        else:
            return torch.device("cpu")
    except ImportError:
        return "cpu"  # torch 미설치 (Droplet, XGBoost 전용)
