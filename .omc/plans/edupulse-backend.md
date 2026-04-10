# EduPulse Backend 구현 계획서 (v2 — Revised)

> **Plan ID:** edupulse-backend
> **원본:** edupulse-full-build.md (Person A 파트 분리)
> **생성일:** 2026-04-08
> **수정일:** 2026-04-08 (Critic/Architect 피드백 13건 반영)
> **상태:** DRAFT
> **담당:** Person A (Backend / Data / Model)
> **전략:** MVP-First — XGBoost 단일 모델 primary, Sync DB, 통합 패키지 구조

---

## 핵심 아키텍처 결정 (v2 변경사항)

| 결정 | 선택 | 사유 |
|---|---|---|
| 패키지 구조 | **통합 (edupulse/)** | CWD 비의존, pip install -e . 가능, Docker 안전 |
| DB 접근 | **Sync (psycopg2 + def 엔드포인트)** | 1 worker MVP에 충분, async 복잡도 제거 |
| 마이그레이션 | **Alembic** | 스키마 변경 불가피, create_all() 한계 |
| 상수 관리 | **edupulse/constants.py 단일 소스** | 이중 정의 방지 |
| 모델 서빙 | **threading.Lock** | XGBoost predict() 스레드 안전성 |

---

## Droplet 메모리 예산 (2GB RAM)

```
Component               | 메모리 (MB) | 비고
------------------------|------------|-----
OS + 시스템              |     ~200   | Ubuntu minimal
PostgreSQL              |     ~300   | shared_buffers=128MB 설정
FastAPI (uvicorn)       |     ~100   | worker 1개
XGBoost 모델 (로딩)      |      ~50   | joblib 직렬화 기준
Python 런타임            |     ~150   | pandas, numpy 등
                        |------------|
합계                     |     ~800   |
여유                     |   ~1200   | OOM 방지 버퍼
```

**단일 모델 서빙 전략:**
- API 서버 시작 시 XGBoost만 메모리에 로딩 (primary)
- Prophet은 요청 시 lazy loading + threading.Lock, 사용 후 메모리 해제 (secondary, stretch)
- LSTM은 Droplet에서 서빙하지 않음 (MacBook 로컬 시연 전용)
- `edupulse/api/dependencies.py`에서 `MODEL_REGISTRY` dict로 관리

---

## 디렉토리 구조 (v2 — 통합 패키지)

```
edupulse/                          # 프로젝트 루트 (= git repo root)
├── pyproject.toml
├── requirements.txt               # 공통 의존성 (전체 교체)
├── requirements-dev.txt           # 로컬 개발 전용
├── requirements-server.txt        # Droplet 서버 전용
├── .env.example
├── .gitignore
├── alembic.ini                    # Alembic 설정
├── alembic/                       # DB 마이그레이션
│   ├── env.py
│   └── versions/
│
├── edupulse/                      # 통합 Python 패키지
│   ├── __init__.py
│   ├── constants.py               # DEMAND_THRESHOLDS 등 (단일 소스)
│   ├── config.py                  # pydantic-settings 기반
│   ├── database.py                # SQLAlchemy sync engine, session
│   │
│   ├── db_models/                 # SQLAlchemy ORM 모델
│   │   ├── __init__.py
│   │   ├── course.py
│   │   ├── enrollment.py
│   │   └── prediction.py
│   │
│   ├── data/
│   │   ├── generators/
│   │   │   ├── __init__.py
│   │   │   ├── enrollment_generator.py
│   │   │   ├── external_generator.py
│   │   │   └── run_all.py         # python -m edupulse.data.generators.run_all
│   │   ├── raw/internal/.gitkeep
│   │   ├── raw/external/.gitkeep
│   │   ├── processed/.gitkeep
│   │   └── warehouse/.gitkeep     # 최종 학습용 데이터셋
│   │
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── cleaner.py
│   │   ├── transformer.py
│   │   └── merger.py
│   │
│   ├── model/
│   │   ├── __init__.py
│   │   ├── base.py                # BaseForecaster ABC + threading.Lock
│   │   ├── xgboost_model.py
│   │   ├── prophet_model.py       # stretch
│   │   ├── lstm_model.py          # stretch (MacBook 전용)
│   │   ├── train.py
│   │   ├── predict.py
│   │   ├── evaluate.py
│   │   ├── retrain.py
│   │   ├── utils.py               # get_device() (조건부 torch import)
│   │   └── saved/
│   │       ├── xgboost/.gitkeep
│   │       ├── prophet/.gitkeep
│   │       └── lstm/.gitkeep
│   │
│   └── api/
│       ├── __init__.py
│       ├── main.py                # FastAPI 앱 진입점
│       ├── dependencies.py        # DB session, MODEL_REGISTRY
│       ├── middleware.py           # CORS, 에러 핸들링
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── health.py
│       │   ├── demand.py
│       │   ├── schedule.py
│       │   └── marketing.py
│       └── schemas/
│           ├── __init__.py
│           ├── common.py          # DemandTier enum (임계값은 constants.py에서 import)
│           ├── demand.py
│           ├── schedule.py
│           └── marketing.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # FakeForecaster mock fixture 포함
│   ├── test_health.py
│   ├── test_demand.py
│   ├── test_preprocessing.py
│   └── test_model_utils.py
│
├── scripts/
│   ├── run_pipeline.py            # generate → preprocess → train 오케스트레이션
│   ├── deploy.sh
│   └── transfer_lstm.sh
│
├── docker-compose.yml
├── docker-compose.dev.yml
└── Dockerfile
```

**Import 예시 (통합 구조):**
```python
from edupulse.config import settings
from edupulse.constants import DEMAND_THRESHOLDS, DemandTier
from edupulse.database import engine, SessionLocal, Base
from edupulse.db_models.course import Course
from edupulse.model.xgboost_model import XGBoostForecaster
from edupulse.model.utils import classify_demand
from edupulse.preprocessing.cleaner import clean_data
from edupulse.api.main import app
```

**실행 커맨드:**
```bash
uvicorn edupulse.api.main:app --reload
python -m edupulse.data.generators.run_all
python -m edupulse.model.train --model xgboost
python -m edupulse.model.retrain --model xgboost
python -m scripts.run_pipeline
```

---

## 일정 (Person A)

```
Week 1
-----------------------------------------------------------------------
Day  | 작업
-----------------------------------------------------------------------
1    | Phase 1: 프로젝트 구조 셋업 (공동)
     | pyproject.toml, DB, config, Alembic 초기화
2    | Phase 1: 스키마 계약, ORM 모델
     | conftest.py, health check, 초기 migration
-----------------------------------------------------------------------
3    | Phase 2: 합성 데이터 생성기
     | enrollment, external 데이터
4    | Phase 2: 전처리 모듈
     | cleaner, transformer, merger
5    | Phase 2: XGBoost 학습/평가
     | train.py, evaluate.py, run_pipeline.py
-----------------------------------------------------------------------

Week 2
-----------------------------------------------------------------------
Day  | 작업
-----------------------------------------------------------------------
6    | Phase 3: demand API 라우터
     | predict 엔드포인트 구현
7    | Phase 3: schedule, marketing API 라우터
     | *** Day 7: 중간 시연 가능 ***
-----------------------------------------------------------------------
8    | Phase 3: API 테스트, 버그 수정
9    | Phase 4: Docker 구성
     | docker-compose.yml (DATABASE_URL=db:5432 명시)
10   | Phase 4: Prophet 추가 (stretch)
     | 또는 버그 수정 + 배포 테스트
-----------------------------------------------------------------------

Day 11-12: 버퍼
```

---

## Phase 1: Foundation (기반 구축) — Day 1-2

**목표:** 프로젝트 구조, DB 스키마, 환경 설정, 스키마 계약, Alembic 초기화

### Task 1.1: 프로젝트 인프라 (Day 1)

| 파일 | 설명 |
|---|---|
| `pyproject.toml` | edupulse 통합 패키지 설정 (setuptools packages.find 포함) |
| `requirements.txt` (전체 교체) | 공통 의존성만. 아래 상세 참조 |
| `requirements-dev.txt` (신규) | jupyter, plotly, matplotlib, black, flake8 |
| `requirements-server.txt` (신규) | 서버 전용 경량 패키지. 아래 상세 참조 |
| `.env.example` | 환경변수 템플릿. 아래 상세 참조 |
| `.gitignore` (수정) | Python + Node.js + 프로젝트별 패턴 |
| `edupulse/__init__.py` | 패키지 초기화 |
| `edupulse/constants.py` | DEMAND_THRESHOLDS, DemandTier (단일 소스) |
| `edupulse/config.py` | pydantic-settings 기반 Settings 클래스 |
| `edupulse/database.py` | SQLAlchemy **sync** engine, SessionLocal, Base |
| `alembic.ini` + `alembic/env.py` | DB 마이그레이션 초기화 |
| `docker-compose.dev.yml` | PostgreSQL 로컬 개발용 (port 5432) |

### Task 1.2: DB ORM 모델 + API 스키마 계약 (Day 2)

| 파일 | 설명 |
|---|---|
| `edupulse/db_models/__init__.py` | ORM 모델 export |
| `edupulse/db_models/course.py` | Course, Cohort 테이블 |
| `edupulse/db_models/enrollment.py` | Enrollment 테이블 |
| `edupulse/db_models/prediction.py` | PredictionResult 테이블 |
| `edupulse/api/__init__.py` | API 패키지 |
| `edupulse/api/main.py` | FastAPI 앱 (기존 root main.py 대체) |
| `edupulse/api/schemas/common.py` | DemandTier import from constants, ErrorResponse |
| `edupulse/api/schemas/demand.py` | DemandRequest, DemandResponse |
| `edupulse/api/schemas/schedule.py` | ScheduleRequest, ScheduleResponse |
| `edupulse/api/schemas/marketing.py` | MarketingRequest, MarketingResponse |
| `edupulse/api/routers/health.py` | GET /api/v1/health |
| `alembic/versions/001_initial.py` | 초기 마이그레이션 (Course, Enrollment, PredictionResult) |
| `tests/conftest.py` | pytest fixtures, TestClient, FakeForecaster |
| `tests/test_health.py` | health check 테스트 |

---

### 핵심 코드 스니펫

#### edupulse/constants.py (단일 소스 — CRITICAL)

```python
"""프로젝트 전역 상수. 모든 모듈이 여기서 import."""
from enum import Enum

class DemandTier(str, Enum):
    HIGH = "High"    # >= 25명
    MID = "Mid"      # >= 12명
    LOW = "Low"      # < 12명

DEMAND_THRESHOLDS = {"high": 25, "mid": 12}

def classify_demand(predicted_count: int) -> DemandTier:
    """예측 인원 → 수요 등급 변환. DemandTier enum 반환."""
    if predicted_count >= DEMAND_THRESHOLDS["high"]:
        return DemandTier.HIGH
    elif predicted_count >= DEMAND_THRESHOLDS["mid"]:
        return DemandTier.MID
    else:
        return DemandTier.LOW
```

#### edupulse/config.py (v2 추가)

```python
"""pydantic-settings 기반 환경 설정."""
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql://edupulse:edupulse@localhost:5432/edupulse"

    # External API
    naver_client_id: str = ""
    naver_client_secret: str = ""

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Model
    model_dir: str = "edupulse/model/saved"

settings = Settings()
```

#### edupulse/database.py (Sync 명시)

```python
"""SQLAlchemy sync engine + session.

동기 DB 접근 전략:
- FastAPI 엔드포인트는 def (not async def)로 정의
- FastAPI가 자동으로 threadpool에서 실행하여 이벤트 루프 블로킹 방지
- 1 worker MVP에 충분. Async 전환은 추후 stretch goal.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from edupulse.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass
```

#### edupulse/api/schemas/common.py (constants에서 import)

```python
"""공통 API 스키마. DemandTier는 constants.py에서 import (단일 소스)."""
from pydantic import BaseModel
from edupulse.constants import DemandTier  # 재정의 금지!

class ErrorResponse(BaseModel):
    detail: str
    status_code: int
```

#### edupulse/api/schemas/demand.py

```python
from pydantic import BaseModel
from datetime import date, datetime
from typing import Literal
from edupulse.constants import DemandTier

class DemandRequest(BaseModel):
    course_name: str
    start_date: date
    field: Literal["coding", "security", "game", "art"]

class ConfidenceInterval(BaseModel):
    lower: float
    upper: float

class DemandResponse(BaseModel):
    course_name: str
    field: str
    predicted_enrollment: int
    demand_tier: DemandTier
    confidence_interval: ConfidenceInterval
    model_used: str
    prediction_date: datetime
```

#### .env.example (v2 추가)

```env
# Database
DATABASE_URL=postgresql://edupulse:edupulse@localhost:5432/edupulse
# Docker 환경에서는: postgresql://edupulse:edupulse@db:5432/edupulse

# External API
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=

# Server
API_HOST=0.0.0.0
API_PORT=8000
```

---

### requirements.txt (전체 교체)

**기존 파일의 모든 내용을 아래로 교체한다.**

제거되는 패키지 (이동 또는 삭제):
- `selenium` → 제거 (MVP에서 미사용)
- `statsmodels` → 제거 (MVP에서 미사용)
- `prophet` → requirements-dev.txt로 이동
- `torch`, `torchvision` → requirements-dev.txt로 이동
- `mlflow` → 제거 (2주 데드라인 제외)
- `boto3` → 제거 (S3 미사용, scp 전송)
- `apscheduler` → 제거 (cron 사용 결정)
- `matplotlib`, `seaborn`, `plotly` → requirements-dev.txt로 이동
- `jupyter`, `ipykernel` → requirements-dev.txt로 이동
- `black`, `flake8` → requirements-dev.txt로 이동

버전 전략: `==` 고정 → `>=` 최소 버전으로 변경 (호환성 유연성 확보)

```
# 데이터 수집
requests>=2.32.0
beautifulsoup4>=4.12.0
pytrends>=4.9.0
python-dotenv>=1.0.0

# 데이터 처리
pandas>=2.2.0
numpy>=1.26.0
scipy>=1.13.0
scikit-learn>=1.5.0

# 모델링 (공통)
xgboost>=2.0.0
joblib>=1.4.0

# 백엔드
fastapi>=0.111.0
uvicorn>=0.30.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
httpx>=0.27.0

# 데이터베이스
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
alembic>=1.13.0

# 테스트
pytest>=8.2.0
```

### requirements-dev.txt (로컬 전용)

```
-r requirements.txt
prophet>=1.1.0
torch>=2.3.0
torchvision>=0.18.0
jupyter>=1.0.0
ipykernel>=6.29.0
matplotlib>=3.9.0
seaborn>=0.13.0
plotly>=5.22.0
black>=24.4.0
flake8>=7.0.0
```

### requirements-server.txt (Droplet 전용)

```
-r requirements.txt
# prophet: stretch goal로만 설치 (pip install prophet)
# torch 미포함: LSTM은 MacBook에서 학습 후 scp 전송
# jupyter, 시각화 미포함: 서버에서 불필요
# 이 파일은 requirements.txt와 동일하지만 명시적 분리를 위해 유지
```

### pyproject.toml (통합 패키지 + setuptools)

```toml
[project]
name = "edupulse"
version = "0.1.0"
description = "AI-based course enrollment demand forecasting"
requires-python = ">=3.11,<3.13"

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["edupulse*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.black]
line-length = 88
target-version = ["py311"]
```

### .gitignore (Backend에서도 관리)

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
*.egg-info/
dist/
build/
*.egg

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env
.env.local

# Data (raw 데이터는 git에 올리지 않음)
edupulse/data/raw/
edupulse/data/processed/
edupulse/data/warehouse/
*.csv
*.parquet

# Model artifacts
edupulse/model/saved/**/*.pkl
edupulse/model/saved/**/*.joblib
edupulse/model/saved/**/*.pt
edupulse/model/saved/**/*.json
!edupulse/model/saved/**/.gitkeep

# Alembic
alembic/versions/__pycache__/

# Node.js / Frontend
frontend/node_modules/
frontend/dist/
frontend/.env.local

# Docker
*.log

# Jupyter
.ipynb_checkpoints/

# OS
.DS_Store
Thumbs.db

# omc
.omc/
```

### 기존 main.py 마이그레이션

```
현재: /main.py (FastAPI app, root에 위치)
목표: /edupulse/api/main.py (라우터 구조의 FastAPI app)
```

1. `edupulse/api/main.py`를 새로 생성 (라우터 마운트 구조)
2. 기존 `main.py`의 로직을 `edupulse/api/main.py`로 이전
3. 기존 `main.py`를 삭제
4. `test_main.http`를 새 엔드포인트에 맞게 업데이트 또는 삭제
5. 실행 커맨드 변경: `uvicorn main:app` → `uvicorn edupulse.api.main:app`

### Phase 1 수락 기준

```bash
# 1. pip install -e . 동작 확인 (통합 패키지 핵심 검증)
pip install -e .
python -c "from edupulse.config import settings; print(settings.database_url)"
# 기대: postgresql://edupulse:edupulse@localhost:5432/edupulse

# 2. FastAPI 서버 기동
uvicorn edupulse.api.main:app --reload
# 기대: INFO: Application startup complete

# 3. Health check
curl -s http://localhost:8000/api/v1/health | python -m json.tool
# 기대: {"status": "ok", ...}

# 4. 테스트
pytest tests/test_health.py -v
# 기대: PASSED

# 5. PostgreSQL (Docker)
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml ps
# 기대: postgres ... Up

# 6. Alembic 마이그레이션
alembic upgrade head
# 기대: Running upgrade -> 001_initial, OK

# 7. DB 테이블 확인
python -c "
from edupulse.database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
assert 'courses' in tables or 'course' in tables, f'테이블 없음: {tables}'
print(f'테이블: {tables}')
"
```

---

## Phase 2: Data + Model (데이터 + 모델링) — Day 3-5

**목표:** 합성 데이터 생성, 전처리 파이프라인, XGBoost 학습/평가 완료
**선행 조건:** Phase 1 완료
**소요:** 3일 (Day 5에 완료, Day 6부터 Phase 3 시작 가능)

### Task 2.1: 합성 데이터 생성 (Day 3)

| 파일 | 설명 |
|---|---|
| `edupulse/data/generators/__init__.py` | 생성기 패키지 |
| `edupulse/data/generators/enrollment_generator.py` | 수강 이력 합성 (계절성, 트렌드) |
| `edupulse/data/generators/external_generator.py` | 검색 트렌드, 채용 공고 합성 |
| `edupulse/data/generators/run_all.py` | 전체 합성 데이터 일괄 생성 |

**합성 데이터 요구사항:**
- 4개 분야(coding, security, game, art) x 최소 8기수 x 2년치
- 계절성: 방학 시즌(1월, 7-8월) 수요 증가, 학기 중(3-5월, 9-11월) 감소
- 외부 지표 상관관계: 검색량 증가 → 2-4주 후 등록 증가
- Prophet 호환 형식(`ds`, `y`) + 범용 형식(`date`, `enrollment_count`) 동시 출력
- 수요 등급 분포: 약 20% High(>=25), 50% Mid(12-24), 30% Low(<12)
- 출력 경로: `edupulse/data/raw/internal/`, `edupulse/data/raw/external/`

### Task 2.2: 전처리 모듈 (Day 4)

| 파일 | 설명 |
|---|---|
| `edupulse/preprocessing/__init__.py` | 전처리 패키지 |
| `edupulse/preprocessing/cleaner.py` | 결측치 linear interpolation, IQR 이상치 처리 |
| `edupulse/preprocessing/transformer.py` | lag feature(1/2/4/8주), sliding window |
| `edupulse/preprocessing/merger.py` | 내부+외부 데이터 병합, 날짜 YYYY-MM-DD 표준화 |

**전처리 출력:** `edupulse/data/warehouse/` (최종 학습용 데이터셋)

### Task 2.3: XGBoost 모델 학습 (Day 5)

| 파일 | 설명 |
|---|---|
| `edupulse/model/__init__.py` | 모델 패키지 |
| `edupulse/model/base.py` | BaseForecaster ABC + threading.Lock |
| `edupulse/model/xgboost_model.py` | XGBoost 래퍼 (primary) |
| `edupulse/model/train.py` | 통합 학습 스크립트 |
| `edupulse/model/predict.py` | 예측 실행 (등록 인원 + 수요 등급) |
| `edupulse/model/evaluate.py` | MAPE 평가, 시계열 K-Fold |
| `edupulse/model/utils.py` | get_device() (조건부 torch import), 모델 저장/로딩 |
| `scripts/run_pipeline.py` | generate → preprocess → train 오케스트레이션 |

### 모델 핵심 인터페이스

```python
# edupulse/model/base.py
import threading
from abc import ABC, abstractmethod
import pandas as pd
from dataclasses import dataclass
from edupulse.constants import DemandTier

@dataclass
class PredictionResult:
    predicted_enrollment: int
    demand_tier: DemandTier
    confidence_lower: float
    confidence_upper: float
    model_used: str
    mape: float | None

class BaseForecaster(ABC):
    def __init__(self):
        self._lock = threading.Lock()

    @abstractmethod
    def train(self, df: pd.DataFrame) -> None: ...

    @abstractmethod
    def _predict(self, features: pd.DataFrame) -> PredictionResult: ...

    def predict(self, features: pd.DataFrame) -> PredictionResult:
        """스레드 안전 예측. 동시 요청에서 내부 상태 충돌 방지."""
        with self._lock:
            return self._predict(features)

    @abstractmethod
    def evaluate(self, df: pd.DataFrame, n_splits: int = 5) -> dict: ...

    def save(self, path: str, version: int) -> None: ...
    def load(self, path: str, version: int) -> None: ...
```

```python
# edupulse/model/utils.py
"""모델 유틸리티. classify_demand()는 edupulse.constants에서 import하여 사용."""
from edupulse.constants import classify_demand  # 재정의 금지!

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
```

```python
# edupulse/model/predict.py (글루 함수 — API 입력 → BaseForecaster 입력 변환)
"""API의 raw 입력을 BaseForecaster가 요구하는 pd.DataFrame으로 변환."""
import pandas as pd
from edupulse.model.base import PredictionResult

def predict_demand(
    course_name: str,
    start_date: str,
    field: str,
    model_name: str = "xgboost"
) -> PredictionResult:
    """
    API에서 호출하는 진입점.
    1. raw 입력 → feature DataFrame 구성 (전처리 모듈 활용)
    2. 모델 로딩 (MODEL_REGISTRY에서)
    3. model.predict(features) 호출
    4. PredictionResult 반환
    """
    # 구현은 Phase 3에서 API dependencies와 함께 완성
    ...
```

### scripts/run_pipeline.py (v2 추가 — 파이프라인 오케스트레이션)

```python
"""데이터 생성 → 전처리 → 학습 전체 파이프라인.

Usage:
    python -m scripts.run_pipeline
    python -m scripts.run_pipeline --skip-generate  # 기존 데이터 사용
"""
# 1. edupulse.data.generators.run_all → raw/
# 2. edupulse.preprocessing.cleaner + transformer + merger → warehouse/
# 3. edupulse.model.train → model/saved/
```

### Phase 2 수락 기준

```bash
# 1. 합성 데이터 생성
python -m edupulse.data.generators.run_all
ls edupulse/data/raw/internal/ edupulse/data/raw/external/

# 2. 합성 데이터 검증
python -c "
import pandas as pd
df = pd.read_csv('edupulse/data/raw/internal/enrollment_history.csv')
assert len(df) >= 64, f'최소 64행 필요, 현재 {len(df)}'
assert set(df['field'].unique()) == {'coding','security','game','art'}
print('합성 데이터 OK')
"

# 3. 전처리 모듈
python -c "
from edupulse.preprocessing.cleaner import clean_data
from edupulse.preprocessing.transformer import add_lag_features
from edupulse.preprocessing.merger import merge_datasets
print('전처리 모듈 import OK')
"

# 4. 전체 파이프라인
python -m scripts.run_pipeline
# 기대: 데이터 생성 → 전처리 → 학습 완료

# 5. XGBoost 학습 확인
ls edupulse/model/saved/xgboost/
# 기대: v1/ 디렉토리에 모델 파일 존재

# 6. 모델 평가 (MAPE < 30%)
python -m edupulse.model.evaluate --model xgboost

# 7. 예측 테스트
python -c "
from edupulse.model.predict import predict_demand
result = predict_demand('Python 웹개발', '2026-05-01', 'coding')
assert result.demand_tier.value in ['High', 'Mid', 'Low']
assert result.predicted_enrollment > 0
print(f'예측: {result.predicted_enrollment}명 ({result.demand_tier.value})')
"

# 8. 전처리 테스트
pytest tests/test_preprocessing.py -v

# 9. 모델 utils 테스트
pytest tests/test_model_utils.py -v
```

**MAPE 수락 기준:**
- 합성 데이터 기준 XGBoost MAPE < 30%
- MAPE 30% 초과 시: feature engineering 재검토 → hyperparameter 튜닝 → 데이터 증강

---

## Phase 3: API 라우터 구현 — Day 6-8

**목표:** FastAPI 라우터 구현, 모델 서빙
**선행 조건:** Phase 1 (스키마), Phase 2 (XGBoost 모델)

### Task 3.1: API 라우터 구현 (Day 6-7)

| 파일 | 설명 |
|---|---|
| `edupulse/api/dependencies.py` | DB session, MODEL_REGISTRY(단일 모델 로딩 + Lock) |
| `edupulse/api/middleware.py` | CORS (localhost:5173 + Droplet 도메인), 에러 핸들링 |
| `edupulse/api/routers/__init__.py` | 라우터 패키지 |
| `edupulse/api/routers/demand.py` | `POST /api/v1/demand/predict` |
| `edupulse/api/routers/schedule.py` | `POST /api/v1/schedule/suggest` (rule-based MVP) |
| `edupulse/api/routers/marketing.py` | `POST /api/v1/marketing/timing` (rule-based MVP) |
| `tests/test_demand.py` | 수요 예측 API 테스트 (FakeForecaster 사용) |

**Sync 엔드포인트 규칙 (CRITICAL):**
```python
# DB 또는 모델을 사용하는 엔드포인트는 반드시 def (not async def)
# FastAPI가 자동으로 threadpool에서 실행

@router.post("/predict")
def predict_demand(request: DemandRequest):  # def, not async def
    model = get_model("xgboost")
    ...
```

### API 엔드포인트 상세

```
POST /api/v1/demand/predict
  Input:  DemandRequest (course_name, start_date, field)
  Output: DemandResponse (predicted_enrollment, demand_tier, confidence_interval, model_used)
  모델:   XGBoost (primary), 미로딩 시 503

POST /api/v1/schedule/suggest  [rule-based MVP]
  Input:  ScheduleRequest (course_name, start_date, predicted_enrollment)
  Output: ScheduleResponse (required_instructors, required_classrooms, assignment_plan)
  로직:   predicted_enrollment / 15 = 강사 수 (올림), / 30 = 강의실 수 (올림)
  NOTE:   CLAUDE.md는 DB 강사 가용성 조합을 명시하나, MVP에서는 순수 산술.
          TODO: 추후 Instructor 테이블 연동

POST /api/v1/marketing/timing  [rule-based MVP]
  Input:  MarketingRequest (course_name, start_date, demand_tier)
  Output: MarketingResponse (ad_launch_weeks_before, earlybird_duration_days, discount_rate)
  로직:   High → 2주전/7일/5%, Mid → 3주전/14일/10%, Low → 4주전/21일/15%

GET  /api/v1/health
  Output: { status, models_loaded, db_connected, memory_usage_mb }
```

### MODEL_REGISTRY 단일 모델 서빙 (threading.Lock 포함)

```python
# edupulse/api/dependencies.py
import threading
from edupulse.model.base import BaseForecaster
from edupulse.model.xgboost_model import XGBoostForecaster
from edupulse.database import SessionLocal
from fastapi import HTTPException

MODEL_REGISTRY: dict[str, BaseForecaster] = {}
_prophet_lock = threading.Lock()

def load_models():
    """서버 시작 시 XGBoost만 로딩. Droplet 메모리 절약."""
    try:
        xgb = XGBoostForecaster()
        xgb.load("edupulse/model/saved/xgboost", version=1)
        MODEL_REGISTRY["xgboost"] = xgb
    except FileNotFoundError:
        pass  # 모델 미학습 상태 — health check에서 표시

def get_model(name: str = "xgboost") -> BaseForecaster:
    if name not in MODEL_REGISTRY:
        raise HTTPException(503, f"Model '{name}' not loaded")
    return MODEL_REGISTRY[name]

def get_db():
    """DB 세션 의존성 주입. Sync SessionLocal."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### tests/conftest.py (FakeForecaster mock — v2 추가)

```python
import pytest
from fastapi.testclient import TestClient
from edupulse.api.main import app
from edupulse.api.dependencies import MODEL_REGISTRY
from edupulse.model.base import BaseForecaster, PredictionResult
from edupulse.constants import DemandTier

class FakeForecaster(BaseForecaster):
    """테스트용 가짜 모델. 모델 파일 불필요, 결정론적 결과."""
    def train(self, df): pass
    def _predict(self, features):
        return PredictionResult(
            predicted_enrollment=20,
            demand_tier=DemandTier.MID,
            confidence_lower=15.0,
            confidence_upper=25.0,
            model_used="fake",
            mape=None,
        )
    def evaluate(self, df, n_splits=5):
        return {"mape": 0.1}
    def save(self, path, version): pass
    def load(self, path, version): pass

@pytest.fixture
def client():
    """FakeForecaster가 로딩된 TestClient."""
    MODEL_REGISTRY["xgboost"] = FakeForecaster()
    with TestClient(app) as c:
        yield c
    MODEL_REGISTRY.clear()

@pytest.fixture
def client_no_model():
    """모델 미로딩 상태 TestClient (503 테스트용)."""
    MODEL_REGISTRY.clear()
    with TestClient(app) as c:
        yield c
```

### Phase 3 수락 기준

```bash
# 1. 수요 예측 API
curl -X POST http://localhost:8000/api/v1/demand/predict \
  -H "Content-Type: application/json" \
  -d '{"course_name":"Python 웹개발","start_date":"2026-05-01","field":"coding"}'
# 기대: {"predicted_enrollment": N, "demand_tier": "High|Mid|Low", ...}

# 2. 스케줄링 API
curl -X POST http://localhost:8000/api/v1/schedule/suggest \
  -H "Content-Type: application/json" \
  -d '{"course_name":"Python 웹개발","start_date":"2026-05-01","predicted_enrollment":25}'

# 3. 마케팅 API
curl -X POST http://localhost:8000/api/v1/marketing/timing \
  -H "Content-Type: application/json" \
  -d '{"course_name":"Python 웹개발","start_date":"2026-05-01","demand_tier":"High"}'

# 4. 모델 미로딩 시 503 반환
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/demand/predict \
  -H "Content-Type: application/json" \
  -d '{"course_name":"test","start_date":"2026-05-01","field":"coding"}'
# 기대: 503

# 5. CORS 헤더
curl -s -I -X OPTIONS http://localhost:8000/api/v1/demand/predict \
  -H "Origin: http://localhost:5173"
# 기대: Access-Control-Allow-Origin: http://localhost:5173

# 6. pytest (FakeForecaster 사용 — 모델 파일 불필요)
pytest tests/test_demand.py -v
# 기대: PASSED (200, 422, 503 모두 테스트)
```

---

## Phase 4: Docker + Deploy — Day 9-10

**목표:** Docker 컨테이너화, 재학습 스케줄러
**선행 조건:** Phase 3 완료

### Task 4.1: Docker 구성 (Day 9)

| 파일 | 설명 |
|---|---|
| `Dockerfile` | API 서버 (Python 3.11-slim, pip install -e .) |
| `docker-compose.yml` | PostgreSQL + API + Frontend 통합 |
| `docker-compose.dev.yml` (수정) | 로컬 개발용 (hot reload) |
| `.dockerignore` | .venv, node_modules, .git, edupulse/data/raw/ |

**Docker DATABASE_URL 전략 (v2 추가):**
```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: edupulse
      POSTGRES_USER: edupulse
      POSTGRES_PASSWORD: edupulse

  api:
    build: .
    environment:
      # Docker 내부: 서비스명 'db' 사용 (localhost 아님!)
      DATABASE_URL: postgresql://edupulse:edupulse@db:5432/edupulse
    depends_on:
      - db
```

**Dockerfile 구조:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt
COPY . .
RUN pip install -e .
EXPOSE 8000
CMD ["uvicorn", "edupulse.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Task 4.2: 재학습 스케줄러 (Day 9)

| 파일 | 설명 |
|---|---|
| `edupulse/model/retrain.py` | cron 호출 대상 스크립트 (standalone) |
| `scripts/deploy.sh` | Droplet 배포 스크립트 |
| `scripts/transfer_lstm.sh` | LSTM 모델 scp 전송 (stretch goal) |

**cron 전략:**
- `retrain.py`는 standalone: `python -m edupulse.model.retrain --model xgboost`
- 내부에서 전처리 파이프라인도 호출 (새 데이터 → 전처리 → 재학습)
- cron: `0 2 * * 0 cd /app && python -m edupulse.model.retrain --model xgboost`

### Phase 4 수락 기준

```bash
# 1. Docker 전체 서비스 기동
docker-compose up --build -d
docker-compose ps
# 기대: db(Up), api(Up), frontend(Up)

# 2. API 응답
curl http://localhost:8000/api/v1/health
# 기대: {"status":"ok","models_loaded":["xgboost"],"db_connected":true}

# 3. Docker 내 Frontend 접근
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# 기대: 200

# 4. Docker 내 DB 서비스명 접근
docker-compose exec api python -c "
from edupulse.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    print(conn.execute(text('SELECT 1')).scalar())
"
# 기대: 1

# 5. 재학습 스크립트
python -m edupulse.model.retrain --model xgboost --dry-run
# 기대: "Dry run: would retrain xgboost with latest data"
```

---

## Stretch Goals (시간 여유 시)

1. **Prophet 모델 추가** — `edupulse/model/prophet_model.py`, API에서 model 파라미터로 선택. lazy loading + `_prophet_lock` 사용.
2. **데이터 수집 모듈** — `collection/` 크롤러 및 API 수집기
3. **LSTM 모델** — MacBook 전용 학습, Droplet 서빙 제외

---

## 테스트 전략

### Unit Tests (Phase 2)

| 대상 | 파일 | 검증 항목 |
|---|---|---|
| 전처리 | `tests/test_preprocessing.py` | cleaner: 결측치 보간, 이상치 제거. transformer: lag feature |
| 모델 utils | `tests/test_model_utils.py` | classify_demand() 임계값 (DemandTier enum 반환), get_device() |
| 상수 | `tests/test_model_utils.py` | DEMAND_THRESHOLDS 값, DemandTier 열거형 |

### Integration Tests (Phase 3)

| 대상 | 파일 | 검증 항목 |
|---|---|---|
| Demand API | `tests/test_demand.py` | 정상 200 (FakeForecaster), 잘못된 field 422, 모델 미로딩 503 |
| Schedule API | `tests/test_schedule.py` | 강사 수 계산 정확성 |
| Marketing API | `tests/test_marketing.py` | 등급별 타이밍/할인율 매핑 |

### E2E Smoke Test (Phase 4)

```bash
docker-compose up -d
sleep 10
curl -f http://localhost:8000/api/v1/health
curl -f -X POST http://localhost:8000/api/v1/demand/predict \
  -H "Content-Type: application/json" \
  -d '{"course_name":"test","start_date":"2026-06-01","field":"coding"}'
curl -f http://localhost:3000
echo "E2E smoke test passed"
```

---

## 리스크 및 완화

| 리스크 | 완화 전략 |
|---|---|
| 합성 데이터 실제 분포 괴리 | 계절성/트렌드 현실적 설계, BaseForecaster ABC. 합성 MAPE는 파이프라인 검증용임을 명시 |
| Droplet 메모리 부족 | XGBoost 단일 모델, health API memory_usage_mb |
| XGBoost MAPE > 30% | feature engineering → hyperparameter 튜닝 → 데이터 증강 |
| Prophet pip 설치 실패 | stretch goal, conda fallback |
| 동시 요청 시 모델 상태 충돌 | BaseForecaster.predict()에 threading.Lock |
| Docker 내 DB 연결 실패 | DATABASE_URL을 docker-compose.yml에서 db:5432로 명시 |
| Alembic 마이그레이션 충돌 | 2인 팀이므로 마이그레이션 생성은 Person A만 담당 |
| torch 미설치 환경 (Droplet) | get_device()에서 try/except ImportError 처리 |

---

## v2 변경사항 요약 (13건)

| # | 이슈 | 변경 내용 |
|---|---|---|
| 1 | 패키지 구조 | 모든 모듈을 `edupulse/` 아래로 통합. setuptools packages.find 설정 |
| 2 | DEMAND_THRESHOLDS 이중 정의 | `edupulse/constants.py` 단일 소스. classify_demand()도 여기에 |
| 3 | Async/Sync 미결정 | Sync 명시. DB 엔드포인트는 `def`. `pytest-asyncio` 제거 |
| 4 | DB 마이그레이션 없음 | Alembic 추가. Phase 1에서 초기화 |
| 5 | config.py 미정의 | Settings 클래스 스니펫 추가 |
| 6 | .env.example 미정의 | 환경변수 + 기본값 + Docker 주석 추가 |
| 7 | requirements.txt 교체 절차 | "전체 교체" 명시, 제거 패키지 목록, 버전 전략 변경 기재 |
| 8 | 모델 스레드 안전성 | BaseForecaster에 threading.Lock, _predict() 패턴 |
| 9 | 파이프라인 오케스트레이션 없음 | scripts/run_pipeline.py 추가 |
| 10 | Docker DATABASE_URL | docker-compose.yml에서 db:5432 명시 |
| 11 | 테스트 모델 의존성 | conftest.py에 FakeForecaster mock fixture |
| 12 | 일정 겹침 (Day 5-6) | Task 2.3을 Day 5로 축소. Phase 3은 Day 6부터 |
| 13 | get_device() torch import | try/except ImportError로 조건부 import |
