"""BaseForecaster ABC + PredictionResult / ModelMetadata dataclass."""
import json
import logging
import sys
import threading
import warnings
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from edupulse.constants import DemandTier


@dataclass
class PredictionResult:
    """모델 예측 결과."""

    predicted_enrollment: int
    demand_tier: DemandTier
    confidence_lower: float
    confidence_upper: float
    model_used: str
    mape: float | None


@dataclass
class ModelMetadata:
    """모델 학습 메타데이터. 학습 조건과 성능을 기록한다."""

    model_name: str
    version: int
    trained_at: str
    data_rows: int
    data_date_range: dict = field(default_factory=dict)
    feature_columns: list[str] = field(default_factory=list)
    hyperparameters: dict = field(default_factory=dict)
    mape: float | None = None
    fields: list[str] = field(default_factory=list)
    python_version: str = field(default_factory=lambda: sys.version.split()[0])
    package_versions: dict = field(default_factory=dict)


def save_metadata(path: str, version: int, metadata: ModelMetadata) -> Path:
    """ModelMetadata를 JSON 파일로 저장.

    Args:
        path: 모델 저장 루트 경로 (예: edupulse/model/saved/xgboost)
        version: 버전 번호
        metadata: 저장할 메타데이터

    Returns:
        저장된 metadata.json 파일 경로
    """
    save_dir = Path(path) / f"v{version}"
    save_dir.mkdir(parents=True, exist_ok=True)
    meta_path = save_dir / "metadata.json"
    meta_path.write_text(
        json.dumps(asdict(metadata), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return meta_path


def load_metadata(path: str, version: int) -> ModelMetadata:
    """JSON 파일에서 ModelMetadata를 로딩.

    Args:
        path: 모델 저장 루트 경로
        version: 버전 번호

    Returns:
        ModelMetadata 인스턴스

    Raises:
        FileNotFoundError: metadata.json이 존재하지 않을 때
    """
    meta_path = Path(path) / f"v{version}" / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"메타데이터 파일을 찾을 수 없습니다: {meta_path}")
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    return ModelMetadata(**data)


def _extract_data_info(df: pd.DataFrame) -> dict:
    """학습 DataFrame에서 메타데이터에 필요한 정보를 추출.

    Args:
        df: 학습 DataFrame

    Returns:
        {"data_rows", "data_date_range", "fields"} 딕셔너리
    """
    info: dict = {"data_rows": len(df), "data_date_range": {}, "fields": []}
    if "date" in df.columns:
        dates = pd.to_datetime(df["date"])
        info["data_date_range"] = {
            "start": str(dates.min().date()),
            "end": str(dates.max().date()),
        }
    if "field" in df.columns:
        info["fields"] = sorted(df["field"].unique().tolist())
    return info


def _get_package_version(package_name: str) -> str | None:
    """패키지 버전을 안전하게 반환. 미설치 시 None."""
    try:
        from importlib.metadata import version
        return version(package_name)
    except Exception:
        return None


def validate_feature_columns(
    expected: list[str], df: pd.DataFrame, caller: str = "",
) -> list[str]:
    """DataFrame에서 사용 가능한 피처 컬럼을 반환하고, 누락 시 경고 로그를 남긴다.

    Args:
        expected: 기대하는 피처 컬럼 목록
        df: 실제 DataFrame
        caller: 호출자 식별 문자열 (로그용)

    Returns:
        df에 존재하는 컬럼만 필터링한 목록
    """
    available = [c for c in expected if c in df.columns]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        msg = f"[{caller}] 피처 컬럼 누락: {missing}"
        logging.getLogger(__name__).warning(msg)
        warnings.warn(msg, UserWarning, stacklevel=2)
    return available


def ensure_feature_columns(
    df: pd.DataFrame, expected: list[str], caller: str = "",
) -> pd.DataFrame:
    """누락 피처를 0으로 채운 DataFrame 복사본 반환. 원본은 변경하지 않는다.

    Args:
        df: 실제 DataFrame
        expected: 기대하는 피처 컬럼 목록
        caller: 호출자 식별 문자열 (로그용)

    Returns:
        expected 컬럼이 모두 존재하는 DataFrame (누락 시 0.0으로 채움)
    """
    available = validate_feature_columns(expected, df, caller)
    if len(available) == len(expected):
        return df  # 모든 컬럼 존재 → 복사 불필요
    result = df.copy()
    for col in expected:
        if col not in result.columns:
            result[col] = 0.0
    return result


def warn_feature_mismatch(path: str, version: int, current_features: list[str]) -> None:
    """metadata.json이 있으면 학습 시 피처와 현재 피처를 비교하여 경고.

    Args:
        path: 모델 저장 루트 경로
        version: 버전 번호
        current_features: 현재 코드에서 사용하는 피처 목록
    """
    try:
        meta = load_metadata(path, version)
        saved = meta.feature_columns
        if saved and set(saved) != set(current_features):
            added = set(current_features) - set(saved)
            removed = set(saved) - set(current_features)
            parts = []
            if added:
                parts.append(f"추가됨={added}")
            if removed:
                parts.append(f"제거됨={removed}")
            msg = (
                f"[load] 피처 불일치 — 학습: {len(saved)}개, "
                f"현재: {len(current_features)}개. {', '.join(parts)}"
            )
            logging.getLogger(__name__).warning(msg)
            warnings.warn(msg, UserWarning, stacklevel=2)
    except FileNotFoundError:
        pass  # metadata 없으면 검증 불가 — 무시


class BaseForecaster(ABC):
    """모든 예측 모델의 추상 기반 클래스."""

    def __init__(self):
        self._lock = threading.Lock()

    @abstractmethod
    def train(self, df: pd.DataFrame) -> None:
        """모델 학습."""
        ...

    @abstractmethod
    def _predict(self, features: pd.DataFrame) -> PredictionResult:
        """내부 예측 로직 (Lock 없이 호출)."""
        ...

    def predict(self, features: pd.DataFrame) -> PredictionResult:
        """스레드 안전 예측. 동시 요청에서 내부 상태 충돌 방지."""
        with self._lock:
            return self._predict(features)

    @abstractmethod
    def evaluate(self, df: pd.DataFrame, n_splits: int = 5) -> dict:
        """시계열 K-Fold 교차검증. MAPE 반환."""
        ...

    def save(self, path: str, version: int, df: pd.DataFrame | None = None) -> None:
        """모델 저장. 하위 클래스에서 오버라이드.

        Args:
            path: 저장 루트 경로
            version: 버전 번호
            df: 학습 DataFrame (메타데이터 생성용, None이면 생략)
        """
        ...

    def load(self, path: str, version: int) -> None:
        """모델 로딩. 하위 클래스에서 오버라이드."""
        ...
