"""공통 API 스키마. DemandTier는 constants.py에서 import (단일 소스)."""
from pydantic import BaseModel

from edupulse.constants import DemandTier  # 재정의 금지!

__all__ = ["DemandTier", "ErrorResponse"]


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
