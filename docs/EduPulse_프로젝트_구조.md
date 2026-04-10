# EduPulse 프로젝트 구조

> **최종 업데이트:** 2026-04-10
> **현재 상태:** Phase D 완료 (프론트엔드-백엔드 실시간 연동)

---

## 1. 프로젝트 개요

EduPulse는 코딩/보안/게임/아트 분야 학원을 위한 **AI 기반 수강 수요 예측 솔루션**이다.
수강 이력, 검색 트렌드, 채용 시장 등의 데이터를 통합 분석하여 수요 예측 → 운영 계획 → 마케팅 전략 → 시장 분석까지 의사결정 전 과정을 지원한다.

### 기술 스택 요약

| 영역 | 기술 |
|---|---|
| 프론트엔드 | React 18.3, React Router 7, Recharts 3.8, Vite 8 |
| 백엔드 | FastAPI, Pydantic v2, Python 3.12 |
| AI 모델 | XGBoost, Prophet, PyTorch LSTM, Ensemble |
| 데이터 | Pandas, NumPy, scikit-learn |
| 수집 | Naver DataLab API, BeautifulSoup |
| DB | PostgreSQL, SQLAlchemy, Alembic |
| 배포 | Docker, DigitalOcean Droplet |
| LSTM 학습 | M4 MacBook (Apple MPS) |

---

## 2. 디렉토리 구조

```
edupulse/                               # 프로젝트 루트
│
├── edupulse/                           # 백엔드 Python 패키지
│   ├── config.py                       # 환경 설정 (DB URL, API 키)
│   ├── constants.py                    # 전역 상수 (분야, 임계값, CSV 경로)
│   ├── database.py                     # DB 연결/세션 관리
│   │
│   ├── api/                            # FastAPI 서버
│   │   ├── main.py                     # 앱 진입점 (라우터 등록, 모델 로딩)
│   │   ├── dependencies.py             # 의존성 주입 (모델 캐시)
│   │   ├── middleware.py               # CORS 등 미들웨어
│   │   ├── routers/
│   │   │   ├── health.py               # GET  /api/v1/health
│   │   │   ├── demand.py               # POST /api/v1/demand/predict, closure-risk
│   │   │   ├── schedule.py             # POST /api/v1/schedule/suggest
│   │   │   ├── marketing.py            # POST /api/v1/marketing/timing, lead-conversion
│   │   │   └── simulation.py           # POST /api/v1/simulation/simulate, optimal-start, demographics, competitors
│   │   ├── schemas/                    # Pydantic 요청/응답 스키마
│   │   │   ├── common.py               # 공통 (FieldEnum, DemandTierEnum)
│   │   │   ├── demand.py               # 수요 예측 스키마
│   │   │   ├── marketing.py            # 마케팅 스키마
│   │   │   ├── schedule.py             # 스케줄 스키마
│   │   │   └── simulation.py           # 시뮬레이션 스키마
│   │   └── services/                   # 비즈니스 로직
│   │       ├── marketing_service.py    # 전환 예측, 광고 타이밍 계산
│   │       └── simulation_service.py   # 시나리오 분석, 인구통계, 경쟁사
│   │
│   ├── model/                          # AI 모델링
│   │   ├── base.py                     # BaseForecaster ABC, PredictionResult, ModelMetadata
│   │   ├── predict.py                  # 수요 예측 진입점 (build_features + 모델 호출)
│   │   ├── train.py                    # 모델 학습 CLI (--model, --version)
│   │   ├── evaluate.py                 # MAPE 평가, 시계열 K-Fold
│   │   ├── ensemble.py                 # 앙상블 (가중 평균, 단일 모델 폴백)
│   │   ├── xgboost_model.py            # XGBoost (FEATURE_COLUMNS 19개 정의)
│   │   ├── prophet_model.py            # Prophet (ds/y 형식)
│   │   ├── lstm_model.py               # LSTM (PyTorch, MPS 지원)
│   │   ├── retrain.py                  # 자동 재학습 스케줄러
│   │   ├── utils.py                    # get_device() 등 유틸리티
│   │   └── saved/                      # 저장된 모델 (git에서 제외)
│   │       ├── xgboost/v1/             # model.json + metadata.json
│   │       ├── lstm/v1/                # model.pt + scaler.pkl + metadata.json
│   │       └── prophet/v1/             # model.pkl + metadata.json
│   │
│   ├── preprocessing/                  # 데이터 전처리
│   │   ├── cleaner.py                  # 결측치 보간, 이상치 처리 (IQR)
│   │   ├── transformer.py              # 지연 피처, 월 인코딩, 분야 인코딩
│   │   └── merger.py                   # 9개 CSV → 단일 학습 데이터셋 병합
│   │
│   ├── collection/                     # 데이터 수집
│   │   └── api/
│   │       ├── collect_search_trends.py  # 수집 CLI 진입점
│   │       ├── naver_datalab.py        # Naver DataLab (주 데이터 소스)
│   │       ├── google_trends.py        # Google Trends (캐시 전용)
│   │       ├── keywords.py             # 분야→키워드 매핑
│   │       └── quota.py                # Naver API 일일 할당량 (KST 리셋)
│   │
│   ├── data/                           # 데이터 저장소
│   │   ├── generators/                 # 합성 데이터 생성기
│   │   │   ├── enrollment_generator.py # 주간 수강 이력 생성
│   │   │   ├── external_generator.py   # 외부 데이터 8종 생성
│   │   │   ├── internal_generator.py   # 내부 데이터 생성
│   │   │   ├── events_generator.py     # 계절 이벤트 생성
│   │   │   └── run_all.py              # 전체 합성 데이터 실행
│   │   ├── raw/                        # 원시 데이터 (git 제외)
│   │   │   ├── internal/               # enrollment_history, consultation_logs 등
│   │   │   └── external/               # search_trends, job_postings 등
│   │   ├── processed/                  # 전처리 결과 (git 제외)
│   │   └── warehouse/                  # 최종 학습 데이터 (git 제외)
│   │
│   └── db_models/                      # SQLAlchemy ORM 모델
│       ├── course.py
│       ├── enrollment.py
│       └── prediction.py
│
├── frontend/                           # 프론트엔드 (React + Vite)
│   ├── vite.config.js                  # Vite 설정 (dev proxy 포함)
│   ├── package.json                    # 의존성 (react, recharts, react-router-dom)
│   ├── .env.development                # VITE_ADAPTER=mock
│   ├── .env.production                 # VITE_ADAPTER=real
│   │
│   └── src/
│       ├── main.jsx                    # React 진입점
│       ├── App.jsx                     # 라우터 설정
│       ├── index.css                   # 글로벌 스타일 (CSS 변수)
│       │
│       ├── pages/                      # 5개 페이지
│       │   ├── Dashboard.jsx           # 대시보드 (요약 카드 + 차트 + 알림)
│       │   ├── Simulator.jsx           # 시뮬레이터 (수요 + 운영 + 마케팅 통합)
│       │   ├── Marketing.jsx           # 마케팅 분석 (전환 + 광고 타이밍)
│       │   ├── Operations.jsx          # 운영 관리 (폐강 위험 + 배정)
│       │   └── Market.jsx              # 시장 분석 (인구통계 + 경쟁 + 최적 개강일)
│       │
│       ├── components/                 # 공용 컴포넌트
│       │   ├── Layout.jsx              # 사이드바 + 헤더 레이아웃
│       │   ├── DemandChart.jsx         # 수요 추세 차트
│       │   ├── AlertPanel.jsx          # 알림 패널
│       │   ├── StatusPanel.jsx         # 로딩/빈값/에러 상태 표시
│       │   ├── TierBadge.jsx           # 수요 등급 배지 (High/Mid/Low)
│       │   ├── FieldSelector.jsx       # 분야 선택 드롭다운
│       │   ├── RiskGauge.jsx           # 위험도/포화도 게이지
│       │   └── ScoreBar.jsx            # 점수 바
│       │
│       ├── api/                        # API 통신 계층
│       │   ├── viewModels.js           # UI 데이터 팩토리 (createUIState 등)
│       │   ├── types.js                # JSDoc 타입 정의
│       │   ├── client.js               # fetch 래퍼 (apiGet, apiPost)
│       │   ├── transformers.js         # 백엔드 응답 → UI 형태 변환
│       │   ├── errors.js               # HTTP 에러 → 한글 UIState
│       │   └── adapters/
│       │       ├── index.js            # 어댑터 선택기 (VITE_ADAPTER 기반)
│       │       ├── mockAdapter.js      # Mock 어댑터 (fixture 기반)
│       │       ├── realAdapter.js      # Real 어댑터 (FastAPI 호출)
│       │       └── hybridAdapter.js    # Hybrid (Dashboard=mock, 나머지=real)
│       │
│       └── fixtures/                   # Mock 데이터
│           ├── dashboardStates.js
│           ├── simulatorStates.js
│           ├── systemStatusStates.js
│           ├── marketingStates.js
│           ├── operationsStates.js
│           └── marketStates.js
│
├── tests/                              # 테스트
│   ├── conftest.py                     # 공통 fixture
│   ├── test_model.py                   # 모델 학습/예측 테스트
│   ├── test_demand.py                  # 수요 예측 API 테스트
│   ├── test_health.py                  # 헬스체크 테스트
│   ├── test_simulation.py              # 시뮬레이션 API 테스트
│   ├── test_generators.py              # 합성 데이터 생성 테스트
│   ├── test_collection.py              # 데이터 수집 테스트
│   └── test_preprocessing.py           # 전처리 테스트
│
├── alembic/                            # DB 마이그레이션
│   ├── env.py
│   └── versions/
│       └── 001_initial.py
│
├── scripts/                            # 실행 스크립트
│   ├── run_pipeline.py                 # 전체 파이프라인 실행
│   ├── deploy.sh                       # 배포 스크립트
│   └── transfer_lstm.sh               # LSTM 모델 MacBook → Droplet 전송
│
├── docs/                               # 문서
│   ├── EduPulse_전체_기능_정리.md       # 전체 기능 목록 + API 스키마
│   ├── EduPulse_프로젝트_구조.md        # 본 문서
│   ├── 프론트엔드_백엔드_연동_가이드.md   # Phase B→C→D 연동 상세
│   ├── model_layer_refactoring.md      # 모델 계층 리팩토링 기록
│   ├── 합성_데이터_생성_가이드.md        # 합성 데이터 생성 상세 가이드
│   ├── ai_chat_report/                 # AI 대화 기반 활용 리포트
│   ├── ai_plans/                       # AI 기반 설계 문서
│   └── ai_tool_report/                 # AI 도구 활용 리포트
│
├── pyproject.toml                      # Python 프로젝트 메타데이터
├── requirements.txt                    # 공통 패키지
├── requirements-dev.txt                # 로컬 개발 전용 (jupyter 등)
├── requirements-server.txt             # 서버 전용 (경량)
├── Dockerfile                          # Docker 이미지
├── docker-compose.yml                  # 서비스 컨테이너
├── docker-compose.dev.yml              # 개발용 Docker
├── CLAUDE.md                           # AI 코딩 에이전트 가이드
└── README.md                           # 프로젝트 소개
```

---

## 3. 시스템 아키텍처

### 3.1 전체 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                        데이터 계층                                │
│                                                                 │
│  [Naver API] ──┐                                                │
│  [합성 생성기] ──┼──▸ raw CSV (9종) ──▸ 전처리 ──▸ 학습 데이터     │
│  [크롤링]     ──┘    (enrollment,     (cleaner,   (19개 피처      │
│                       search_trends,  transformer, 벡터)          │
│                       job_postings    merger)                     │
│                       ...)                                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        모델 계층                                 │
│                                                                 │
│  [XGBoost] ──┐                                                  │
│  [Prophet] ──┼──▸ EnsembleForecaster ──▸ PredictionResult       │
│  [LSTM]    ──┘    (가중 평균 결합)        { predicted_enrollment, │
│                                           demand_tier,           │
│                                           confidence_interval }  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      백엔드 API 계층                              │
│                                                                 │
│  FastAPI (10개 엔드포인트)                                        │
│  ├── /health              서버 상태                               │
│  ├── /demand/predict      수요 예측                               │
│  ├── /demand/closure-risk 폐강 위험                               │
│  ├── /schedule/suggest    강사/강의실 배정                         │
│  ├── /marketing/timing    광고 타이밍                              │
│  ├── /marketing/lead-conversion 전환 예측                         │
│  ├── /simulation/simulate 시나리오 분석                            │
│  ├── /simulation/optimal-start  최적 개강일                        │
│  ├── /simulation/demographics   인구통계                           │
│  └── /simulation/competitors    경쟁사 동향                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP (Vite proxy in dev)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     프론트엔드 계층                                │
│                                                                 │
│  Adapter 선택기 (VITE_ADAPTER)                                   │
│  ├── mock    → mockAdapter   (fixture 데이터)                     │
│  ├── hybrid  → hybridAdapter (Dashboard=mock, 나머지=real)        │
│  └── real    → realAdapter   (전체 API 호출)                      │
│       │                                                          │
│       ├── client.js      (apiGet/apiPost)                        │
│       ├── transformers.js (응답 변환)                              │
│       └── errors.js      (에러 한글화)                             │
│                   │                                              │
│                   ▼                                              │
│  5개 페이지 (Dashboard, Simulator, Marketing, Operations, Market) │
│  8개 공용 컴포넌트 (Layout, DemandChart, TierBadge, ...)          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 프론트엔드 어댑터 패턴

```
Page (예: Marketing.jsx)
  │
  │  import { getLeadConversion, getMarketingTiming } from '../api/adapters'
  │
  ▼
adapters/index.js ──── VITE_ADAPTER 환경변수로 분기
  │
  ├── 'mock'   → mockAdapter.js   → fixtures/*.js에서 즉시 반환
  ├── 'hybrid' → hybridAdapter.js → Dashboard 3개는 mock, 9개는 real
  └── 'real'   → realAdapter.js   → client.js로 HTTP 호출
                     │
                     ├── transformers.js  (응답 형태 통일)
                     └── errors.js       (에러 형태 통일)
                            │
                            ▼
                  createUIState({ state, data, isDemo })
                  → Page는 UIState 하나만 소비
```

**핵심 규약:** 페이지는 어댑터가 무엇인지 모른다. UIState 인터페이스만 소비하므로 mock ↔ real 전환 시 페이지 코드 변경 불필요.

---

## 4. 데이터 파이프라인

### 4.1 데이터 소스 (9종 CSV)

| 구분 | 파일 | 내용 | 생성 모듈 |
|---|---|---|---|
| 내부 | `enrollment_history.csv` | 주간 분야별 수강 이력 | `enrollment_generator.py` |
| 내부 | `consultation_logs.csv` | 상담 건수 + 등록 전환 | `internal_generator.py` |
| 내부 | `web_logs.csv` | 페이지 조회수 | `internal_generator.py` |
| 내부 | `student_profiles.csv` | 수강생 연령/목적 | `internal_generator.py` |
| 외부 | `search_trends.csv` | 분야별 검색량 | `external_generator.py` / Naver API |
| 외부 | `job_postings.csv` | 분야별 채용 공고 수 | `external_generator.py` |
| 외부 | `cert_exam_schedule.csv` | 자격증 시험 일정 | `external_generator.py` |
| 외부 | `competitor_data.csv` | 경쟁 학원 개강/수강료 | `external_generator.py` |
| 외부 | `seasonal_events.csv` | 방학/시험/학기 이벤트 | `events_generator.py` |

### 4.2 전처리 흐름

```
raw CSV (9종)
    │
    ▼
cleaner.py
    ├── 결측치: linear interpolation
    ├── 이상치: IQR 방식 (계절성 강한 경우 Z-score 보완)
    └── 날짜 표준화: YYYY-MM-DD
    │
    ▼
merger.py
    ├── 병합 키: [field, date]
    └── 9개 CSV → 단일 DataFrame
    │
    ▼
transformer.py
    ├── 지연 피처: lag_1w, lag_2w, lag_4w, lag_8w
    ├── 이동 평균: rolling_mean_4w
    ├── 월 인코딩: month_sin, month_cos (순환)
    └── 분야 인코딩: field_encoded (art=0, coding=1, game=2, security=3)
    │
    ▼
predict.py::build_features()
    └── 최종 19개 피처 벡터 생성 → 모델 입력
```

### 4.3 피처 목록 (19개)

| 카테고리 | 피처명 | 설명 |
|---|---|---|
| 시계열 (5) | `lag_1w`, `lag_2w`, `lag_4w`, `lag_8w`, `rolling_mean_4w` | 과거 수강생 수 + 이동 평균 |
| 날짜/분야 (3) | `month_sin`, `month_cos`, `field_encoded` | 월 순환 인코딩 + 분야 |
| 외부 지표 (2) | `search_volume`, `job_count` | 검색량 + 채용 공고 |
| 내부 선행 (2) | `consultation_count`, `page_views` | 상담 건수 + 웹 조회수 |
| 자격증 (2) | `has_cert_exam`, `weeks_to_exam` | 시험 유무 + 시험까지 주수 |
| 경쟁사 (2) | `competitor_openings`, `competitor_avg_price` | 개강 수 + 평균 수강료 |
| 계절 이벤트 (3) | `is_vacation`, `is_exam_season`, `is_semester_start` | 방학/시험/학기 플래그 |

---

## 5. AI 모델

### 5.1 모델 구성

| 모델 | 유형 | MAPE | 학습 환경 | 저장 형식 |
|---|---|---|---|---|
| **XGBoost** | 그래디언트 부스팅 | 16.20% | M4 MacBook / Droplet | `model.json` |
| **LSTM** | 딥러닝 (RNN) | 40.32% | M4 MacBook 전용 (MPS) | `model.pt` + `scaler.pkl` |
| **Prophet** | 시계열 분해 | - | M4 MacBook / Droplet | `model.pkl` |
| **Ensemble** | 가중 평균 결합 | - | 런타임 | (로딩된 모델 조합) |

### 5.2 모델 클래스 계층

```
BaseForecaster (ABC)           # base.py
  ├── train(df) → metadata
  ├── predict(df) → PredictionResult
  └── load(path, version)
      │
      ├── XGBoostForecaster    # xgboost_model.py
      ├── LSTMForecaster       # lstm_model.py
      ├── ProphetForecaster    # prophet_model.py
      └── EnsembleForecaster   # ensemble.py (여러 모델 조합)
```

### 5.3 수요 등급 분류

```python
# constants.py
DEMAND_THRESHOLDS = {"high": 6, "mid": 3}  # 주간 기준

HIGH: >= 6명/주
MID:  >= 3명/주
LOW:  < 3명/주
```

### 5.4 LSTM 하이퍼파라미터 (현재)

| 파라미터 | 값 | 비고 |
|---|---|---|
| `SEQUENCE_LENGTH` | 8 | 8주(2개월) 시퀀스 |
| `HIDDEN_SIZE` | 32 | 소규모 데이터 최적화 |
| `NUM_LAYERS` | 2 | 2층 LSTM |
| `DROPOUT` | 0.2 | |
| `INPUT_SIZE` | 19 | `len(FEATURE_COLUMNS)` — 동적 |
| `PATIENCE` | 15 | Early stopping |
| `learning_rate` | 5e-4 | |
| `epochs` | 200 | |

### 5.5 모델 버전 관리

```
model/saved/
  ├── xgboost/v1/
  │   ├── model.json          # 학습된 모델
  │   └── metadata.json       # 하이퍼파라미터, MAPE, 피처 목록
  ├── lstm/v1/
  │   ├── model.pt
  │   ├── scaler.pkl
  │   └── metadata.json
  └── prophet/v1/
      ├── model.pkl
      └── metadata.json
```

`MODEL_VERSION` 환경변수로 사용할 버전 선택 (기본값: 1).

---

## 6. 백엔드 API

### 6.1 엔드포인트 전체 목록

| 엔드포인트 | 메서드 | 설명 | 주요 입력 |
|---|---|---|---|
| `/api/v1/health` | GET | 서버/모델/DB 상태 | - |
| `/api/v1/demand/predict` | POST | 수요 예측 | course_name, start_date, field |
| `/api/v1/demand/closure-risk` | POST | 폐강 위험 평가 | course_name, start_date, field |
| `/api/v1/schedule/suggest` | POST | 강사/강의실 배정 | course_name, start_date, predicted_enrollment |
| `/api/v1/marketing/timing` | POST | 광고 타이밍 제안 | course_name, start_date, demand_tier |
| `/api/v1/marketing/lead-conversion` | POST | 전환 예측 | field |
| `/api/v1/simulation/simulate` | POST | 3시나리오 분석 | course_name, field, start_date, price_per_student |
| `/api/v1/simulation/optimal-start` | POST | 최적 개강일 | course_name, field, search_window_start/end |
| `/api/v1/simulation/demographics` | POST | 인구통계 | field |
| `/api/v1/simulation/competitors` | POST | 경쟁사 동향 | field |

### 6.2 서버 구동

```bash
# 개발 모드
.venv/bin/python -m uvicorn edupulse.api.main:app --reload

# 서버 시작 시 자동 실행:
# 1. load_models() → XGBoost/LSTM/Prophet 로딩 → Ensemble 구성
# 2. CORS 미들웨어 설정
# 3. 5개 라우터 등록 (/api/v1 prefix)
```

### 6.3 모델 로딩 흐름

```
서버 시작 (lifespan)
  └── load_models()  (dependencies.py)
        ├── XGBoostForecaster.load("saved/xgboost", v1)   ✅
        ├── ProphetForecaster.load("saved/prophet", v1)    ⚠️ (pandas 호환 이슈)
        ├── LSTMForecaster.load("saved/lstm", v1)          ✅
        └── EnsembleForecaster(models={성공한 모델들})
              → Prophet 실패 시 XGBoost+LSTM 또는 XGBoost 단독 폴백
```

---

## 7. 프론트엔드

### 7.1 페이지 구성

| 경로 | 페이지 | 역할 | 사용 API |
|---|---|---|---|
| `/` | Dashboard | 운영 현황 요약 | getDashboardSummary, getDemandChart, getDashboardAlerts |
| `/simulator` | Simulator | 신규 강좌 시뮬레이션 | simulateDemand |
| `/marketing` | Marketing | 전환 + 광고 전략 | getLeadConversion, getMarketingTiming |
| `/operations` | Operations | 폐강 위험 + 배정 | getClosureRisk, getScheduleSuggest |
| `/market` | Market | 시장 환경 분석 | getDemographics, getCompetitors, getOptimalStart |

### 7.2 컴포넌트 의존 관계

```
Layout.jsx (모든 페이지 감싸는 쉘)
  ├── 사이드바 내비게이션
  └── 헤더 + 콘텐츠 영역
        │
        └── Page
              ├── StatusPanel    → UIState.state에 따라 로딩/에러/빈값 표시
              ├── FieldSelector  → 분야 선택 (coding/security/game/art)
              ├── TierBadge      → 수요 등급 (High=초록, Mid=노랑, Low=빨강)
              ├── RiskGauge      → 반원 게이지 (0~1 점수, labels 커스텀 가능)
              ├── ScoreBar       → 수평 점수 바 (0~2 또는 0~100)
              ├── DemandChart    → Recharts ComposedChart
              └── AlertPanel     → 알림 목록 (critical/warning/info)
```

### 7.3 스타일링

CSS custom properties 기반 (Tailwind 미사용):

```css
--color-primary, --color-success, --color-warning, --color-danger
--space-xs ~ --space-xl
--radius-sm, --radius-md, --radius-lg
```

---

## 8. 환경 구성

### 8.1 개발 환경

| 항목 | 설정 |
|---|---|
| Python | 3.12 (`.venv/bin/python` 사용 필수) |
| Node.js | 18+ |
| 패키지 관리 | pip (Python), npm (Node) |
| 백엔드 실행 | `.venv/bin/python -m uvicorn edupulse.api.main:app --reload` |
| 프론트엔드 실행 | `cd frontend && npm run dev` |
| 테스트 | `.venv/bin/python -m pytest tests/ -v` |
| 프론트엔드 빌드 | `cd frontend && npx vite build` |

### 8.2 환경변수

**백엔드 (`.env`)**

| 변수 | 용도 |
|---|---|
| `DATABASE_URL` | PostgreSQL 연결 문자열 |
| `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` | Naver DataLab API 키 |
| `API_HOST` / `API_PORT` | 서버 바인드 (기본 0.0.0.0:8000) |
| `MODEL_VERSION` | 사용할 모델 버전 (기본 1) |

**프론트엔드 (`.env.development` / `.env.production`)**

| 변수 | 용도 | 기본값 |
|---|---|---|
| `VITE_ADAPTER` | 어댑터 선택 (mock/hybrid/real) | mock |
| `VITE_API_BASE_URL` | API 기본 URL | (빈 문자열, proxy 사용) |

### 8.3 로컬 vs 서버

| | M4 MacBook (로컬) | DigitalOcean Droplet |
|---|---|---|
| 역할 | 개발, LSTM 학습 | API 서빙, XGBoost/Prophet 재학습 |
| GPU | Apple MPS | CPU만 |
| 스펙 | M4 칩 | 1 vCPU / 2GB RAM |

LSTM은 MacBook에서 학습 후 `scp`로 서버 전송:
```bash
scp model/saved/lstm/v1/model.pt user@droplet:/app/model/saved/lstm/v1/
```

---

## 9. Git 관리

### 9.1 브랜치 전략

```
main ← PR 머지만 허용 (squash merge)
  └── dev ← 개발 통합 브랜치
        ├── feat/frontend-mockup-pages     (머지 완료)
        ├── feat/api-endpoints             (머지 완료)
        └── feat/frontend-enhancement-v2   (현재 작업 중)
```

| 접두사 | 용도 | 예시 |
|---|---|---|
| `feat/` | 새 기능 | `feat/demand-api` |
| `fix/` | 버그 수정 | `fix/prophet-date-format` |
| `data/` | 데이터 수집/전처리 | `data/job-crawler` |
| `model/` | 모델 학습/튜닝 | `model/lstm-tuning` |

### 9.2 커밋 메시지

```
<prefix>: <요약 (72자 이내)>

<선택: 왜 이 변경이 필요한지>
```

접두사: `feat:`, `fix:`, `data:`, `model:`, `docs:`, `refactor:`, `test:`, `chore:`

### 9.3 .gitignore 핵심 항목

```
.env
__pycache__/
model/saved/**/*.pt
model/saved/**/*.pkl
data/raw/
data/processed/
data/warehouse/
*.csv
node_modules/
```

---

## 10. 문서 목록

| 파일 | 내용 |
|---|---|
| `README.md` | 프로젝트 소개, 기능 목록, 실행 방법 |
| `CLAUDE.md` | AI 코딩 에이전트 가이드 (코딩 규칙, 환경, 주의사항) |
| `docs/EduPulse_프로젝트_구조.md` | **본 문서** — 전체 구조 |
| `docs/EduPulse_전체_기능_정리.md` | 기능 상세 + API 스키마 + 응답 예시 |
| `docs/프론트엔드_백엔드_연동_가이드.md` | Phase B→C→D 연동 구현 상세 |
| `docs/합성_데이터_생성_가이드.md` | 합성 데이터 9종 생성 로직 상세 |
| `docs/model_layer_refactoring.md` | 모델 계층 리팩토링 기록 |
| `docs/ai_plans/edupulse-frontend-phases.md` | 프론트엔드 Phase A→D 계획 |
| `docs/ai_plans/edupulse-backend.md` | 백엔드 설계 문서 |
| `docs/ai_plans/edupulse-frontend.md` | 프론트엔드 설계 문서 |
| `docs/ai_plans/edupulse-full-build.md` | 전체 빌드 계획 |
| `docs/ai_tool_report/EduPulse_모델_전체_해설.md` | 3종 모델 + 앙상블 해설 |
