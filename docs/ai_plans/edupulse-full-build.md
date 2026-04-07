# EduPulse MVP 구현 계획서 (v2 - Revised)

> **Plan ID:** edupulse-full-build
> **생성일:** 2026-04-07
> **수정일:** 2026-04-07 (Iteration 2 - Architect/Critic 피드백 반영)
> **상태:** DRAFT - 사용자 확인 대기중
> **복잡도:** MEDIUM (MVP 스코프 축소)
> **예상 범위:** 4 Phase, 2주, 2인 팀
> **전략:** MVP-First (Option C)

---

## RALPLAN-DR 요약

### Guiding Principles (핵심 원칙)

1. **MVP-First Delivery** -- 2주 데드라인 내 시연 가능한 end-to-end 파이프라인 완성이 최우선. 완벽보다 동작하는 시스템.
2. **Data-First Development** -- 합성 데이터를 Day 1에 생성하여 모든 후속 작업의 블로커를 제거.
3. **Single-Model Primary** -- XGBoost를 primary 모델로 확정. Prophet은 secondary, LSTM은 stretch goal. Droplet 2GB 제약에서 단일 모델 서빙.
4. **Time-Series Integrity** -- 모든 데이터 처리에서 시간 순서 보장. 랜덤 셔플 금지, 시계열 K-Fold 필수.
5. **Environment-Aware Design** -- M4 MacBook(MPS)과 Droplet(CPU) 이중 환경. requirements 3-파일 분리, 디바이스 감지 동적.

### Decision Drivers (핵심 결정 요인)

1. **2주 데드라인** -- 핵심 기능(수요 예측 + 대시보드)이 가장 빨리 시연 가능해야 함. 과도한 모델 비교보다 동작하는 1개 모델이 중요.
2. **Droplet 메모리 제약 (2GB)** -- PostgreSQL(~300MB) + FastAPI(~100MB) + 모델 서빙(~200MB) = ~600MB. 3개 모델 동시 로딩 불가. 단일 모델(XGBoost ~50MB) 서빙 전략 필수.
3. **2인 팀 병렬화** -- Person A(Backend/Data/Model)와 Person B(Frontend + API 통합)가 Phase 1 스키마 계약 후 독립 작업 가능해야 함.

### Viable Options (구현 접근법)

#### Option A: Bottom-Up Sequential (데이터부터 순차 구축)

```
Data Layer -> Collection -> Preprocessing -> Modeling -> API -> Frontend
```

| 장점 | 단점 |
|---|---|
| 데이터 흐름이 자연스럽게 검증됨 | Frontend 결과물이 가장 마지막에 나옴 |
| 통합 버그가 적음 | 2주 내 완성 불가능 (순차 진행으로 3-4주 소요) |

**미선택 사유:** 2인 병렬 작업 불가. 2주 데드라인 초과 확실.

#### Option B: Contract-First Parallel (계약 선정의 후 병렬 구축, 이전 v1 선택안)

```
6 Phase: Foundation -> Data -> Modeling -> API -> Frontend -> DevOps
```

| 장점 | 단점 |
|---|---|
| 체계적이고 확장 가능 | 6 Phase는 2주에 과도한 범위 |
| 3개 모델 비교 가능 | 3개 모델 동시 학습/비교는 시간 낭비 |
| 완전한 아키텍처 | Droplet에서 3모델 동시 서빙 불가 |

**미선택 사유 (v1에서 변경):** Architect 피드백 -- Droplet 2GB에서 3개 모델 동시 로딩 불가능. 2주 데드라인에서 6 Phase는 Phase 당 평균 2.3일로 버퍼 없음. 3개 모델 "성능 비교"는 합성 데이터에서 의미 제한적.

#### Option C: MVP-First (최소 기능 우선 빠른 전달) -- SELECTED

```
4 Phase: Foundation(2일) -> Data+Model(4일) -> API+Frontend(4일) -> Polish(2일)
```

| 장점 | 단점 |
|---|---|
| 2주 데드라인에 2일 버퍼 확보 | Prophet/LSTM은 stretch goal |
| XGBoost 단일 모델로 Droplet 메모리 안전 | 모델 다양성이 시연에서 부족할 수 있음 |
| Phase 2부터 2인 완전 병렬 | 크롤러/수집 모듈은 MVP 이후로 연기 |
| Day 7에 이미 시연 가능한 시스템 존재 | -- |

**선택 사유:** 2주 + 2인 제약에서 유일하게 버퍼를 확보할 수 있는 전략. XGBoost는 합성 데이터에서도 빠르게 학습 가능(30초-2분)하며, Droplet에서도 안정적으로 서빙. Prophet은 Phase 4에서 시간이 남으면 추가.

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
- Prophet은 요청 시 lazy loading, 사용 후 메모리 해제 (secondary, stretch)
- LSTM은 Droplet에서 서빙하지 않음 (MacBook 로컬 시연 전용)
- `api/dependencies.py`에서 `MODEL_REGISTRY` dict로 관리, 로딩된 모델만 서빙

---

## 2주 일정표 (2인 팀)

```
Person A: Backend / Data / Model (서버 쪽 전체)
Person B: Frontend / API 통합 / DevOps

Week 1
-----------------------------------------------------------------------
Day  | Person A                      | Person B
-----------------------------------------------------------------------
1    | Phase 1: 프로젝트 구조 셋업      | Phase 1: 프로젝트 구조 셋업 (공동)
     | pyproject.toml, DB, config     | .gitignore, requirements 분리
2    | Phase 1: 스키마 계약, ORM 모델   | Phase 1: Vite+React 프로젝트 초기화
     | conftest.py, health check      | API client stub, Layout 컴포넌트
-----------------------------------------------------------------------
3    | Phase 2: 합성 데이터 생성기      | Phase 2: Dashboard 페이지 (mock data)
     | enrollment, external 데이터     | DemandChart, TierBadge 컴포넌트
4    | Phase 2: 전처리 모듈            | Phase 2: Simulator 페이지 (mock data)
     | cleaner, transformer, merger   | 폼 입력 -> mock 예측 결과 표시
5    | Phase 2: XGBoost 학습/평가      | Phase 2: API client 실제 연결 준비
     | train.py, evaluate.py          | 에러 핸들링 UI, 로딩 상태
-----------------------------------------------------------------------

Week 2
-----------------------------------------------------------------------
Day  | Person A                      | Person B
-----------------------------------------------------------------------
6    | Phase 3: demand API 라우터      | Phase 3: Dashboard <-> API 연결
     | predict 엔드포인트 구현          | 실제 예측 데이터로 차트 렌더링
7    | Phase 3: schedule, marketing   | Phase 3: Simulator <-> API 연결
     | API 라우터 구현                  | AlertPanel 구현
     | *** Day 7: 중간 시연 가능 ***   |
-----------------------------------------------------------------------
8    | Phase 3: API 테스트, 버그 수정   | Phase 3: 반응형 레이아웃, UI 다듬기
9    | Phase 4: Docker 구성            | Phase 4: Frontend Dockerfile
     | docker-compose.yml             | nginx 설정
10   | Phase 4: Prophet 추가 (stretch) | Phase 4: 통합 테스트, 문서화
     | 또는 버그 수정 + 배포 테스트      | README 업데이트
-----------------------------------------------------------------------

Day 11-12: 버퍼 (배포 테스트, 발표 준비, 비상 수정)
```

---

## 기존 main.py 마이그레이션 계획

현재 프로젝트 루트에 `main.py`가 존재 (기본 FastAPI hello world).

```
현재: /main.py (FastAPI app, root에 위치)
목표: /api/main.py (라우터 구조의 FastAPI app)
```

**마이그레이션 절차:**
1. `api/main.py`를 새로 생성 (라우터 마운트 구조)
2. 기존 `main.py`의 `app` 인스턴스 로직을 `api/main.py`로 이전
3. 기존 `main.py`를 삭제하거나, `api/main.py`를 import하는 진입점으로 변환
4. `test_main.http`의 엔드포인트를 새 구조에 맞게 업데이트
5. 실행 커맨드 변경: `uvicorn main:app` -> `uvicorn api.main:app`

**수락 기준:** `uvicorn api.main:app --reload` 실행 시 정상 기동, `/docs`에서 모든 라우터 확인 가능

---

## 디렉토리 구조 (CLAUDE.md 기준 유지 + 명명 규칙 정리)

```
edupulse/                          # 프로젝트 루트 (= git repo root)
├── pyproject.toml                 # edupulse 패키지 설정
├── requirements.txt               # 공통 의존성 (수정)
├── requirements-dev.txt           # 로컬 개발 전용
├── requirements-server.txt        # Droplet 서버 전용
├── .env.example
├── .gitignore                     # Python + Node.js + 프로젝트별 패턴
│
├── edupulse/                      # Python 패키지 (ORM, config, 공통)
│   ├── __init__.py
│   ├── config.py                  # pydantic-settings 기반 환경 설정
│   ├── database.py                # SQLAlchemy engine, session, Base
│   └── db_models/                 # SQLAlchemy ORM 모델 (** model/과 혼동 방지 **)
│       ├── __init__.py
│       ├── course.py              # Course, Cohort 테이블
│       ├── enrollment.py          # Enrollment, Consultation 테이블
│       ├── prediction.py          # PredictionResult 테이블
│       └── instructor.py          # Instructor, Availability 테이블
│
├── data/
│   ├── generators/                # 합성 데이터 생성기
│   │   ├── __init__.py
│   │   ├── enrollment_generator.py
│   │   ├── external_generator.py
│   │   └── run_all.py             # python -m data.generators.run_all
│   ├── raw/internal/.gitkeep
│   ├── raw/external/.gitkeep
│   ├── processed/.gitkeep
│   └── warehouse/.gitkeep
│
├── collection/                    # 데이터 수집 (MVP 이후 우선순위)
│   ├── crawlers/
│   │   ├── base_crawler.py
│   │   ├── job_posting.py
│   │   └── competitor.py
│   └── api/
│       ├── naver_datalab.py
│       └── google_trends.py
│
├── preprocessing/
│   ├── __init__.py
│   ├── cleaner.py
│   ├── transformer.py
│   └── merger.py
│
├── model/                         # ML 모델 (** edupulse/db_models/와 명확히 분리 **)
│   ├── __init__.py
│   ├── base.py                    # BaseForecaster ABC
│   ├── xgboost_model.py           # Primary 모델
│   ├── prophet_model.py           # Secondary 모델 (stretch)
│   ├── lstm_model.py              # Stretch goal (MacBook 전용)
│   ├── train.py
│   ├── predict.py
│   ├── evaluate.py
│   ├── retrain.py
│   ├── utils.py                   # get_device(), 모델 저장/로딩
│   └── saved/
│       ├── xgboost/.gitkeep
│       ├── prophet/.gitkeep
│       └── lstm/.gitkeep
│
├── api/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 앱 (기존 root main.py 대체)
│   ├── dependencies.py            # DB session, MODEL_REGISTRY 주입
│   ├── middleware.py               # CORS, 에러 핸들링
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── demand.py
│   │   ├── schedule.py
│   │   └── marketing.py
│   └── schemas/
│       ├── __init__.py
│       ├── common.py              # DemandTier enum, ErrorResponse
│       ├── demand.py
│       ├── schedule.py
│       └── marketing.py
│
├── frontend/                      # Vite + React + Recharts
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── api/
│   │   │   └── client.js          # fetch 기반 API 클라이언트
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx      # MVP 핵심 페이지
│   │   │   └── Simulator.jsx      # 수요 시뮬레이션
│   │   └── components/
│   │       ├── Layout.jsx
│   │       ├── DemandChart.jsx
│   │       ├── TierBadge.jsx
│   │       └── AlertPanel.jsx
│   └── public/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_demand.py
│   └── test_preprocessing.py
│
├── scripts/
│   ├── deploy.sh
│   └── transfer_lstm.sh
│
├── docker-compose.yml
├── docker-compose.dev.yml
├── Dockerfile
└── frontend/Dockerfile
```

### 명명 규칙 정리 (Critic 피드백 반영)

| 디렉토리 | 역할 | 혼동 방지 |
|---|---|---|
| `edupulse/db_models/` | SQLAlchemy ORM 모델 (DB 테이블 정의) | `models/` 대신 `db_models/` 사용 |
| `model/` | ML 모델 (Prophet, XGBoost, LSTM) | CLAUDE.md 원본 구조 유지 |
| `api/schemas/` | Pydantic request/response 스키마 | API 계층 전용 |

---

## Phase 1: Foundation (기반 구축) -- Day 1-2

**목표:** 프로젝트 구조, DB 스키마, 환경 설정, 스키마 계약 확립. Person B가 Frontend 착수 가능한 상태.
**담당:** Person A + Person B (공동 작업 후 분리)
**예상 소요:** 2일

### Task 1.1: 프로젝트 인프라 (Day 1, 공동)

| 파일 | 담당 | 설명 |
|---|---|---|
| `pyproject.toml` | A | edupulse 패키지 설정 (name, version, dependencies ref) |
| `.gitignore` (수정) | B | Python + Node.js + 프로젝트별 패턴 추가 |
| `requirements.txt` (수정) | A | 공통 의존성만 (boto3, mlflow, jupyter 제거) |
| `requirements-dev.txt` (신규) | A | jupyter, plotly, matplotlib, black, flake8 |
| `requirements-server.txt` (신규) | A | torch CPU-only, prophet 제외, 경량 패키지만 |
| `.env.example` | A | DATABASE_URL, NAVER keys, API_HOST/PORT |
| `edupulse/__init__.py` | A | 패키지 초기화 |
| `edupulse/config.py` | A | pydantic-settings 기반 Settings 클래스 |
| `edupulse/database.py` | A | SQLAlchemy async engine, session factory |
| `docker-compose.dev.yml` | A | PostgreSQL 로컬 개발용 (port 5432) |

### Task 1.2: DB ORM 모델 + API 스키마 계약 (Day 2)

| 파일 | 담당 | 설명 |
|---|---|---|
| `edupulse/db_models/__init__.py` | A | ORM 모델 export |
| `edupulse/db_models/course.py` | A | Course, Cohort 테이블 |
| `edupulse/db_models/enrollment.py` | A | Enrollment 테이블 |
| `edupulse/db_models/prediction.py` | A | PredictionResult 테이블 |
| `api/__init__.py` | A | API 패키지 |
| `api/main.py` | A | FastAPI 앱 (기존 main.py 대체) |
| `api/schemas/common.py` | A | DemandTier enum, ErrorResponse |
| `api/schemas/demand.py` | A | DemandRequest, DemandResponse |
| `api/schemas/schedule.py` | A | ScheduleRequest, ScheduleResponse |
| `api/schemas/marketing.py` | A | MarketingRequest, MarketingResponse |
| `api/routers/health.py` | A | GET /api/v1/health |
| `tests/conftest.py` | A | pytest fixtures, TestClient |
| `tests/test_health.py` | A | health check 테스트 |

### Task 1.3: Frontend 프로젝트 초기화 (Day 2, Person B)

| 파일 | 담당 | 설명 |
|---|---|---|
| `frontend/` (Vite 초기화) | B | `npm create vite@latest frontend -- --template react` |
| `frontend/vite.config.js` | B | proxy 설정 (localhost:8000) |
| `frontend/src/App.jsx` | B | React Router 라우팅 |
| `frontend/src/api/client.js` | B | fetch 기반 API 클라이언트 (스키마 계약 기반) |
| `frontend/src/components/Layout.jsx` | B | 공통 레이아웃 (사이드바, 헤더) |

### 핵심 스키마 계약 (Contract)

```python
# api/schemas/common.py
from enum import Enum

class DemandTier(str, Enum):
    HIGH = "High"    # >= 25명
    MID = "Mid"      # >= 12명
    LOW = "Low"      # < 12명

# 통합 임계값 (모든 분야 동일)
DEMAND_THRESHOLDS = {"high": 25, "mid": 12}
```

```python
# api/schemas/demand.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import Literal

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

### requirements.txt 수정 계획

**현재 문제점 (Architect 피드백):**
- `boto3` 포함됨 -- 프로젝트에서 S3 사용하지 않음 (scp 전송). 제거.
- `mlflow` 포함됨 -- 2주 데드라인에서 제외 결정. 제거.
- `jupyter`, `matplotlib`, `seaborn`, `plotly` -- dev 전용. 분리.
- `torch`, `torchvision` -- 서버에서는 CPU-only 또는 제외. 분리.
- `pydantic-settings` 누락 -- 추가 필수.

**수정 후 requirements.txt (공통):**
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
# 스케줄러: cron 사용 결정 -- apscheduler 제거 (852행 참조)

# 테스트
pytest>=8.2.0
pytest-asyncio>=0.23.0
```

**requirements-dev.txt (로컬 전용):**
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

**requirements-server.txt (Droplet 전용):**
```
-r requirements.txt
# prophet은 Droplet에서 stretch goal로만 설치
# torch 미포함 (LSTM은 MacBook에서 학습 후 scp 전송, Droplet에서 서빙 안함)
# jupyter, 시각화 미포함
```

### .gitignore 수정 계획

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
data/raw/
data/processed/
data/warehouse/
*.csv
*.parquet

# Model artifacts
model/saved/**/*.pkl
model/saved/**/*.joblib
model/saved/**/*.pt
model/saved/**/*.json
!model/saved/**/.gitkeep

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

### 수락 기준

```bash
# 1. FastAPI 서버 기동 확인
uvicorn api.main:app --reload
# 기대: INFO: Application startup complete

# 2. Swagger UI 스키마 확인
curl -s http://localhost:8000/docs | grep -q "swagger"
# 또는 브라우저에서 http://localhost:8000/docs 접속

# 3. Health check API 응답
curl -s http://localhost:8000/api/v1/health | python -m json.tool
# 기대: {"status": "ok", ...}

# 4. 테스트 통과
pytest tests/test_health.py -v
# 기대: PASSED

# 5. PostgreSQL 로컬 기동 (Docker)
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml ps
# 기대: postgres ... Up

# 6. DB 테이블 생성 확인
python -c "from edupulse.database import engine, Base; from edupulse.db_models import *; Base.metadata.create_all(engine); print('OK')"
# 기대: OK

# 7. Frontend 개발 서버 기동
cd frontend && npm install && npm run dev
# 기대: VITE v5.x.x ready in xxx ms -- Local: http://localhost:5173/

# 8. pydantic-settings 동작 확인
python -c "from edupulse.config import settings; print(settings.database_url)"
# 기대: postgresql://... (또는 .env 미설정 시 default 값)
```

---

## Phase 2: Data + Model (데이터 + 모델링) -- Day 3-6

**목표:** 합성 데이터 생성, 전처리 파이프라인, XGBoost 학습/평가 완료
**담당:** Person A (데이터/모델), Person B (Frontend 병렬 진행)
**예상 소요:** 4일
**선행 조건:** Phase 1 완료

### Task 2.1: 합성 데이터 생성 (Day 3, Person A)

| 파일 | 설명 |
|---|---|
| `data/generators/__init__.py` | 생성기 패키지 |
| `data/generators/enrollment_generator.py` | 수강 이력 합성 (계절성, 트렌드) |
| `data/generators/external_generator.py` | 검색 트렌드, 채용 공고 합성 |
| `data/generators/run_all.py` | 전체 합성 데이터 일괄 생성 |

**합성 데이터 요구사항:**
- 4개 분야(coding, security, game, art) x 최소 8기수 x 2년치
- 계절성: 방학 시즌(1월, 7-8월) 수요 증가, 학기 중(3-5월, 9-11월) 감소
- 외부 지표 상관관계: 검색량 증가 -> 2-4주 후 등록 증가
- Prophet 호환 형식(`ds`, `y`) + 범용 형식(`date`, `enrollment_count`) 동시 출력
- 수요 등급 분포: 약 20% High(>=25), 50% Mid(12-24), 30% Low(<12)

### Task 2.2: 전처리 모듈 (Day 4, Person A)

| 파일 | 설명 |
|---|---|
| `preprocessing/__init__.py` | 전처리 패키지 |
| `preprocessing/cleaner.py` | 결측치 linear interpolation, IQR 이상치 처리 |
| `preprocessing/transformer.py` | lag feature(1/2/4/8주), sliding window |
| `preprocessing/merger.py` | 내부+외부 데이터 병합, 날짜 YYYY-MM-DD 표준화 |

### Task 2.3: XGBoost 모델 학습 (Day 5-6, Person A)

| 파일 | 설명 |
|---|---|
| `model/__init__.py` | 모델 패키지 |
| `model/base.py` | BaseForecaster ABC |
| `model/xgboost_model.py` | XGBoost 래퍼 (primary) |
| `model/train.py` | 통합 학습 스크립트 |
| `model/predict.py` | 예측 실행 (등록 인원 + 수요 등급) |
| `model/evaluate.py` | MAPE 평가, 시계열 K-Fold |
| `model/utils.py` | get_device(), 모델 저장/로딩, 버전 관리 |
| `model/saved/xgboost/.gitkeep` | XGBoost 모델 저장 디렉토리 |

### Task 2.4: Frontend 병렬 작업 (Day 3-6, Person B)

| 파일 | 설명 |
|---|---|
| `frontend/src/pages/Dashboard.jsx` | 메인 대시보드 (mock data로 먼저 구현) |
| `frontend/src/components/DemandChart.jsx` | Recharts 시계열 차트 |
| `frontend/src/components/TierBadge.jsx` | High/Mid/Low 뱃지 |
| `frontend/src/pages/Simulator.jsx` | 수요 시뮬레이터 (폼 -> mock 결과) |
| `frontend/src/components/AlertPanel.jsx` | 폐강 리스크 알림 |

**Person B mock 전략:** Phase 1에서 확정된 스키마 계약(DemandResponse)에 맞는 mock JSON을 `/frontend/src/api/mockData.js`에 작성. API 연결은 Phase 3에서 수행.

### 모델 핵심 인터페이스

```python
# model/base.py
from abc import ABC, abstractmethod
import pandas as pd
from dataclasses import dataclass
from typing import Literal

@dataclass
class PredictionResult:
    predicted_enrollment: int
    demand_tier: Literal["High", "Mid", "Low"]
    confidence_lower: float
    confidence_upper: float
    model_used: str
    mape: float | None

class BaseForecaster(ABC):
    @abstractmethod
    def train(self, df: pd.DataFrame) -> None: ...

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> PredictionResult: ...

    @abstractmethod
    def evaluate(self, df: pd.DataFrame, n_splits: int = 5) -> dict: ...

    def save(self, path: str, version: int) -> None: ...
    def load(self, path: str, version: int) -> None: ...
```

**수요 등급 임계값 (통합, 모든 분야 동일):**
```python
# model/utils.py
DEMAND_THRESHOLDS = {"high": 25, "mid": 12}

def classify_demand(predicted_count: int) -> str:
    if predicted_count >= DEMAND_THRESHOLDS["high"]:
        return "High"
    elif predicted_count >= DEMAND_THRESHOLDS["mid"]:
        return "Mid"
    else:
        return "Low"
```

### 수락 기준

```bash
# 1. 합성 데이터 생성
python -m data.generators.run_all
ls data/raw/internal/ data/raw/external/
# 기대: enrollment_*.csv, search_trends_*.csv, job_postings_*.csv 등

# 2. 합성 데이터 검증
python -c "
import pandas as pd
df = pd.read_csv('data/raw/internal/enrollment_history.csv')
assert len(df) >= 64, f'최소 64행(4분야x8기수x2) 필요, 현재 {len(df)}'
assert set(df['field'].unique()) == {'coding','security','game','art'}
print('합성 데이터 OK')
"

# 3. 전처리 파이프라인
python -c "
from preprocessing.cleaner import clean_data
from preprocessing.transformer import add_lag_features
from preprocessing.merger import merge_datasets
print('전처리 모듈 import OK')
"

# 4. XGBoost 학습 및 예측
python -m model.train --model xgboost
# 기대: 모델 학습 완료, model/saved/xgboost/v1/ 에 저장

# 5. 모델 평가 (MAPE)
python -m model.evaluate --model xgboost
# 기대: MAPE 값 출력 (합성 데이터 기준 < 30% 목표)

# 6. 예측 테스트
python -c "
from model.predict import predict_demand
result = predict_demand('Python 웹개발', '2026-05-01', 'coding')
assert result.demand_tier in ['High', 'Mid', 'Low']
assert result.predicted_enrollment > 0
print(f'예측: {result.predicted_enrollment}명 ({result.demand_tier})')
"

# 7. 전처리 테스트
pytest tests/test_preprocessing.py -v
# 기대: PASSED
```

**MAPE 수락 기준 (Critic 피드백 반영):**
- 합성 데이터 기준 XGBoost MAPE < 30% (합성 데이터는 패턴이 명확하므로 달성 가능)
- 실데이터 전환 시 MAPE < 25% 목표 (추후 재튜닝)
- MAPE 30% 초과 시: feature engineering 재검토 (lag feature 조합 변경) -> hyperparameter 튜닝 -> 데이터 증강 순서로 대응

---

## Phase 3: API + Frontend 통합 -- Day 6-8

**목표:** FastAPI 라우터 구현, 모델 서빙, Frontend-API 연결 완료. Day 7에 중간 시연 가능.
**담당:** Person A (API 라우터), Person B (Frontend 연결)
**예상 소요:** 3일
**선행 조건:** Phase 1 (스키마), Phase 2 (XGBoost 모델)

### Task 3.1: API 라우터 구현 (Day 6-7, Person A)

| 파일 | 설명 |
|---|---|
| `api/dependencies.py` | DB session, MODEL_REGISTRY(단일 모델 로딩) |
| `api/middleware.py` | CORS (localhost:5173 허용), 에러 핸들링, 로깅 |
| `api/routers/__init__.py` | 라우터 패키지 |
| `api/routers/demand.py` | `POST /api/v1/demand/predict` |
| `api/routers/schedule.py` | `POST /api/v1/schedule/suggest` |
| `api/routers/marketing.py` | `POST /api/v1/marketing/timing` |
| `tests/test_demand.py` | 수요 예측 API 테스트 |

### Task 3.2: Frontend-API 연결 (Day 6-8, Person B)

| 파일 | 수정 내용 |
|---|---|
| `frontend/src/api/client.js` | mock -> 실제 API 호출로 전환 |
| `frontend/src/pages/Dashboard.jsx` | 실제 예측 데이터로 차트 렌더링 |
| `frontend/src/pages/Simulator.jsx` | 폼 submit -> API 호출 -> 결과 표시 |
| `frontend/src/components/AlertPanel.jsx` | 폐강 리스크 강좌 표시 (Low 등급) |

### API 엔드포인트 상세

```
POST /api/v1/demand/predict
  Input:  DemandRequest (course_name, start_date, field)
  Output: DemandResponse (predicted_enrollment, demand_tier, confidence_interval, model_used)
  모델:   XGBoost (primary), 미로딩 시 503

POST /api/v1/schedule/suggest
  Input:  ScheduleRequest (course_name, start_date, predicted_enrollment)
  Output: ScheduleResponse (required_instructors, required_classrooms, assignment_plan)
  로직:   predicted_enrollment / 15 = 강사 수 (올림), / 30 = 강의실 수 (올림)

POST /api/v1/marketing/timing
  Input:  MarketingRequest (course_name, start_date, demand_tier)
  Output: MarketingResponse (ad_launch_weeks_before, earlybird_duration_days, discount_rate)
  로직:   High -> 광고 2주전/얼리버드 7일/5%, Mid -> 3주전/14일/10%, Low -> 4주전/21일/15%

GET  /api/v1/health
  Output: { status, models_loaded, db_connected, memory_usage_mb }
```

### MODEL_REGISTRY 단일 모델 서빙

```python
# api/dependencies.py
from model.xgboost_model import XGBoostForecaster

MODEL_REGISTRY: dict[str, BaseForecaster] = {}

def load_models():
    """서버 시작 시 XGBoost만 로딩. Droplet 메모리 절약."""
    try:
        xgb = XGBoostForecaster()
        xgb.load("model/saved/xgboost", version=1)
        MODEL_REGISTRY["xgboost"] = xgb
    except FileNotFoundError:
        pass  # 모델 미학습 상태 -- health check에서 표시

def get_model(name: str = "xgboost") -> BaseForecaster:
    if name not in MODEL_REGISTRY:
        raise HTTPException(503, f"Model '{name}' not loaded")
    return MODEL_REGISTRY[name]
```

### 수락 기준

```bash
# 1. 수요 예측 API 테스트
curl -X POST http://localhost:8000/api/v1/demand/predict \
  -H "Content-Type: application/json" \
  -d '{"course_name":"Python 웹개발","start_date":"2026-05-01","field":"coding"}'
# 기대: {"predicted_enrollment": N, "demand_tier": "High|Mid|Low", ...}

# 2. 스케줄링 API 테스트
curl -X POST http://localhost:8000/api/v1/schedule/suggest \
  -H "Content-Type: application/json" \
  -d '{"course_name":"Python 웹개발","start_date":"2026-05-01","predicted_enrollment":25}'
# 기대: {"required_instructors": 2, "required_classrooms": 1, ...}

# 3. 마케팅 API 테스트
curl -X POST http://localhost:8000/api/v1/marketing/timing \
  -H "Content-Type: application/json" \
  -d '{"course_name":"Python 웹개발","start_date":"2026-05-01","demand_tier":"High"}'
# 기대: {"ad_launch_weeks_before": 2, "earlybird_duration_days": 7, "discount_rate": 0.05}

# 4. 모델 미로딩 시 503 반환
# (model/saved/xgboost/ 비어있을 때)
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/demand/predict \
  -H "Content-Type: application/json" \
  -d '{"course_name":"test","start_date":"2026-05-01","field":"coding"}'
# 기대: 503

# 5. CORS 헤더 확인
curl -s -I -X OPTIONS http://localhost:8000/api/v1/demand/predict \
  -H "Origin: http://localhost:5173"
# 기대: Access-Control-Allow-Origin: http://localhost:5173

# 6. pytest API 테스트
pytest tests/test_demand.py -v
# 기대: PASSED

# 7. Frontend에서 대시보드 확인
# 브라우저에서 http://localhost:5173 접속
# 기대: DemandChart에 실제 예측 데이터 렌더링, TierBadge 표시

# 8. Frontend 에러 핸들링
# API 서버 중지 후 Frontend 접속
# 기대: "서버에 연결할 수 없습니다" 에러 메시지 (빈 화면 아님)
```

---

## Phase 4: Polish + Deploy -- Day 9-10 (+2일 버퍼)

**목표:** Docker 컨테이너화, 재학습 스케줄러, 문서화. Prophet 추가는 stretch goal.
**담당:** Person A (Docker, retrain), Person B (Frontend Dockerfile, 문서)
**예상 소요:** 2일 + 2일 버퍼
**선행 조건:** Phase 3 완료

### Task 4.1: Docker 구성 (Day 9)

| 파일 | 담당 | 설명 |
|---|---|---|
| `Dockerfile` | A | API 서버 (Python 3.11-slim, requirements-server.txt) |
| `frontend/Dockerfile` | B | Frontend 빌드 (node:20-alpine -> nginx) |
| `docker-compose.yml` | A | PostgreSQL + API + Frontend 통합 |
| `docker-compose.dev.yml` (수정) | A | 로컬 개발용 (hot reload 추가) |
| `.dockerignore` | A | .venv, node_modules, .git, data/raw/ |

### Task 4.2: 재학습 스케줄러 (Day 9, Person A)

| 파일 | 설명 |
|---|---|
| `model/retrain.py` | cron 호출 대상 스크립트 (APScheduler 대신 cron 사용) |
| `scripts/deploy.sh` | Droplet 배포 스크립트 |
| `scripts/transfer_lstm.sh` | LSTM 모델 scp 전송 (stretch goal) |

**cron vs APScheduler 결정 (Architect 피드백 반영):**
- APScheduler를 FastAPI 내부에서 돌리면 API 응답을 블로킹할 수 있음
- Droplet에서는 시스템 cron으로 `retrain.py`를 직접 실행하는 것이 안전
- `retrain.py`는 standalone 스크립트로 구현 (`python -m model.retrain`)
- cron 설정 예시: `0 2 * * 0 cd /app && python -m model.retrain --model xgboost`

### Task 4.3: 문서화 + 마무리 (Day 10)

| 파일 | 담당 | 설명 |
|---|---|---|
| `README.md` (수정) | B | S3 참조 제거, scp 전송으로 통일, 실행 방법 업데이트 |
| API 문서 | A | Swagger UI 자동 생성 확인 |

### Stretch Goals (시간 여유 시, Day 10-12)

우선순위 순서:

1. **Prophet 모델 추가** -- `model/prophet_model.py` 구현, API에서 model 파라미터로 선택 가능
2. **데이터 수집 모듈** -- `collection/` 크롤러 및 API 수집기 구현
3. **LSTM 모델** -- MacBook 전용 학습, Droplet 서빙은 제외
4. **노트북** -- `notebooks/` EDA, 모델 비교 노트북

### 수락 기준

```bash
# 1. Docker 전체 서비스 기동
docker-compose up --build -d
docker-compose ps
# 기대: db(Up), api(Up), frontend(Up)

# 2. Docker 내 API 응답 확인
curl http://localhost:8000/api/v1/health
# 기대: {"status":"ok","models_loaded":["xgboost"],"db_connected":true}

# 3. Docker 내 Frontend 접근
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# 기대: 200

# 4. Docker 내 PostgreSQL 서비스명 접근
docker-compose exec api python -c "
from edupulse.database import engine
with engine.connect() as conn:
    print(conn.execute('SELECT 1').scalar())
"
# 기대: 1 (db 서비스명으로 접근 성공)

# 5. 재학습 스크립트 실행
python -m model.retrain --model xgboost --dry-run
# 기대: "Dry run: would retrain xgboost with latest data"

# 6. README S3 참조 없음 확인
grep -i "s3" README.md
# 기대: 결과 없음 (scp로 통일)
```

---

## Phase 의존성 다이어그램 (4 Phase)

```
Phase 1 (Foundation) -- Day 1-2
  |
  |--- Person A ---> Phase 2 (Data + Model) -- Day 3-6
  |                    |
  |                    +---> Phase 3A (API 라우터) -- Day 6-8
  |                           |
  |--- Person B ---> Phase 2B (Frontend mock) -- Day 3-6
  |                    |
  |                    +---> Phase 3B (Frontend 연결) -- Day 6-8
  |                           |
  |                           v
  +-----------------------> Phase 4 (Polish + Deploy) -- Day 9-10
                             |
                             +---> Buffer (Day 11-12)
```

**핵심 병렬화:**
- Day 3부터 Person A(데이터/모델)와 Person B(Frontend mock)가 완전 독립 작업
- Day 6에 합류: Person A가 API 라우터를, Person B가 Frontend-API 연결을 동시 작업
- Phase 1의 스키마 계약이 이 병렬화를 가능하게 하는 핵심

---

## ADR (Architecture Decision Record)

### Decision
MVP-First 전략으로 전환한다. XGBoost 단일 모델을 primary로 확정하고, 4 Phase 구조로 2주 내 end-to-end 시연 가능한 시스템을 완성한다.

### Drivers
1. **2주 데드라인** -- 6 Phase 계획은 Phase 당 평균 2.3일로 버퍼가 없음. 4 Phase로 축소하여 2일 버퍼 확보.
2. **Droplet 2GB 메모리** -- 3개 모델 동시 서빙 불가. XGBoost 단일 모델(~50MB)로 메모리 예산 내 안정 운영.
3. **2인 팀 구성 확정** -- Person A(Backend), Person B(Frontend)로 Phase 1 이후 완전 병렬 가능.
4. **합성 데이터 기반 개발** -- 합성 데이터에서 3개 모델 "성능 비교"는 의미 제한적. 1개 모델의 안정적 동작이 더 중요.

### Alternatives Considered

- **Option A: Bottom-Up Sequential** -- 순차 진행으로 2주 초과 확실. 2인 병렬 활용 불가.
- **Option B: Contract-First 6-Phase** -- 체계적이나 2주에 과도한 범위. 3개 모델 동시 서빙은 Droplet 메모리 초과. Architect가 "pipeline extensibility"로 reframe 제안했으나, MVP에서는 실제 동작하는 1개 모델이 우선.

### Why Chosen
2주 + 2인 + 2GB 제약 조건에서 유일하게 시연 가능한 end-to-end 시스템을 완성할 수 있는 전략. XGBoost는 학습 속도(30초-2분)와 메모리 효율 모두 최적. Prophet/LSTM은 stretch goal로 남겨 "확장 가능한 아키텍처"를 BaseForecaster ABC로 시연.

### Consequences
- Prophet/LSTM이 MVP에서 빠짐 -- 시연 시 "확장 포인트" 설명 필요
- 모델 비교 노트북이 stretch goal -- 공모전 리포트에서 다양성 어필 약화
- 크롤러/수집 모듈이 MVP 이후 -- 실제 데이터 수집 시연 불가

### Follow-ups
- MVP 완성 후 Prophet 추가 (Day 10-12 버퍼 활용)
- 공모전 이후 LSTM 통합 및 모델 비교 노트북 작성
- 실제 학원 데이터 확보 시 데이터 수집 모듈 구현 및 모델 재학습
- MLflow 통합은 공모전 이후 장기 과제

---

## 테스트 전략

### Unit Tests (Phase 2)

| 대상 | 파일 | 검증 항목 |
|---|---|---|
| 전처리 | `tests/test_preprocessing.py` | cleaner: 결측치 보간 동작, 이상치 제거. transformer: lag feature 정확성 |
| 모델 utils | `tests/test_model_utils.py` | classify_demand() 임계값 동작, get_device() 반환값 |

### Integration Tests (Phase 3)

| 대상 | 파일 | 검증 항목 |
|---|---|---|
| Demand API | `tests/test_demand.py` | 정상 요청 200, 잘못된 field 422, 모델 미로딩 503 |
| Schedule API | `tests/test_schedule.py` | 강사 수 계산 정확성 |
| Marketing API | `tests/test_marketing.py` | 등급별 타이밍/할인율 매핑 |

### E2E Smoke Test (Phase 4)

```bash
# docker-compose 기동 후 전체 흐름 검증
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

## 리스크 및 완화 전략

| 리스크 | 영향도 | 완화 전략 |
|---|---|---|
| 합성 데이터가 실제 분포와 괴리 | 중간 | 계절성/트렌드/상관관계를 현실적으로 설계. BaseForecaster ABC로 모델 교체 용이 |
| Prophet pip 설치 실패 (ARM64) | 낮음 | MVP에서 Prophet은 stretch goal. conda fallback 문서화 |
| Droplet 메모리 부족 | 중간 | XGBoost 단일 모델 전략. health API에 memory_usage_mb 포함 |
| Frontend-Backend 스키마 불일치 | 낮음 | Phase 1 스키마 계약 + OpenAPI spec 자동 생성 |
| 2주 데드라인 초과 | 중간 | 2일 버퍼 확보. Day 7 중간 시연으로 조기 경보. Stretch goal 과감히 포기 |
| XGBoost MAPE가 높음 (>30%) | 낮음 | 합성 데이터 패턴이 명확하므로 가능성 낮음. feature engineering으로 대응 |

---

## Frontend 기술 선택 (Critic 피드백 반영)

| 항목 | 선택 | 사유 |
|---|---|---|
| 빌드 도구 | **Vite** | CRA 대비 10배 빠른 HMR, 2024+ 표준 |
| 프레임워크 | React 18 | CLAUDE.md 명시 |
| 차트 | Recharts | CLAUDE.md 명시, React 친화적 |
| HTTP 클라이언트 | fetch API | 추가 의존성 없음, Vite proxy로 CORS 우회 |
| 패키지 매니저 | npm | 기본 도구, 추가 설정 불필요 |
| CSS | CSS Modules 또는 Tailwind CSS | MVP 수준 스타일링에 충분 |

**Vite proxy 설정:**
```js
// frontend/vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

---

## pyproject.toml 구조 (Architect 피드백 반영)

```toml
[project]
name = "edupulse"
version = "0.1.0"
description = "AI-based course enrollment demand forecasting"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.black]
line-length = 88
target-version = ["py311"]
```

`pythonpath = ["."]` 설정으로 `from edupulse.config import settings`, `from model.train import ...` 등의 import가 프로젝트 루트 기준으로 동작.
