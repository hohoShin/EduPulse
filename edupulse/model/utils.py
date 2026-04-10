"""모델 유틸리티. classify_demand()는 edupulse.constants에서 import하여 사용."""
import re
from pathlib import Path

from edupulse.constants import classify_demand  # noqa: F401 — re-export


def find_latest_version(model_dir: str) -> int:
    """모델 저장 디렉토리에서 최신 버전 번호를 반환.

    vN/ 형태의 하위 디렉토리를 스캔하여 가장 큰 N을 반환한다.
    버전 디렉토리가 없으면 0을 반환한다.

    Args:
        model_dir: 모델 저장 루트 경로 (예: edupulse/model/saved/xgboost)

    Returns:
        최신 버전 번호 (0 = 버전 없음)
    """
    path = Path(model_dir)
    if not path.exists():
        return 0
    versions = []
    for child in path.iterdir():
        if child.is_dir():
            match = re.match(r"^v(\d+)$", child.name)
            if match:
                versions.append(int(match.group(1)))
    return max(versions) if versions else 0


def get_device() -> "torch.device | str":
    """디바이스 감지. torch 미설치 시 문자열 'cpu' 반환 (XGBoost/Prophet 전용 환경)."""
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
