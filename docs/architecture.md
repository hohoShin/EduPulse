# EduPulse 프로젝트 아키텍처

> **최종 업데이트:** 2026-04-10
> **현재 상태:** Phase D 완료 (프론트엔드-백엔드 실시간 연동)

---

## 1. 프로젝트 개요

EduPulse는 코딩/보안/게임/아트 분야 학원을 위한 **AI 기반 수강 수요 예측 솔루션**이다.
수강 이력, 검색 트렌드, 채용 시장 등의 데이터를 통합 분석하여 수요 예측 → 운영 계획 → 마케팅 전략 → 시장 분석까지 의사결정 전 과정을 지원한다.

### 기술 스택

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

## 2. 핵심 가치

| 영역 | 해결하는 문제 | 핵심 산출물 |
|------|-------------|------------|
| **수요 예측** | "다음 분기에 몇 명이 올까?" | 수강생 수 + 수요 등급 (High/Mid/Low) |
| **운영 관리** | "강좌를 열어도 될까? 어떻게 운영하지?" | 폐강 위험도 + 강사/강의실 배정 |
| **마케팅** | "언제, 어떻게 홍보할까?" | 광고 타이밍 + 전환 예측 + 할인율 |
| **시장 분석** | "시장 상황은? 언제 열어야 유리한가?" | 경쟁사 동향 + 인구통계 + 최적 개강일 |

---

## 3. 디렉토리 구조

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
│   │   ├── xgboost_model.py            # XGBoost (FEATURE_COLUMNS 정의)
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
│   ├── architecture.md                # 본 문서 — 프로젝트 구조 + 기능 + API 스펙
│   ├── data-and-model.md              # 데이터 파이프라인 + 모델 가이드
│   ├── frontend-integration.md        # 프론트엔드 연동 가이드
│   ├── ai_reports/                    # AI 활용 리포트 (#1~#7 + 모델 해설)
│   ├── ai_plans/                      # AI 기반 설계 문서
│   └── ai_collaboration_index.md      # AI 협업 문서 인덱스
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

## 4. 시스템 아키텍처

### 4.1 전체 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                        데이터 계층                                │
│                                                                 │
│  [Naver API] ──┐                                                │
│  [합성 생성기] ──┼──▸ raw CSV (9종) ──▸ 전처리 ──▸ 학습 데이터     │
│  [크롤링]     ──┘    (enrollment,     (cleaner,   (피처 벡터      │
│                       search_trends,  transformer, → data-and-   │
│                       job_postings    merger)       model.md     │
│                       ...)                          참조)        │
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

### 4.2 프론트엔드 어댑터 패턴

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

## 5. 프론트엔드

### 5.1 페이지 구성

| 경로 | 페이지 | 역할 | 사용 API |
|---|---|---|---|
| `/` | Dashboard | 운영 현황 요약 | getDashboardSummary, getDemandChart, getDashboardAlerts |
| `/simulator` | Simulator | 신규 강좌 시뮬레이션 | simulateDemand |
| `/marketing` | Marketing | 전환 + 광고 전략 | getLeadConversion, getMarketingTiming |
| `/operations` | Operations | 폐강 위험 + 배정 | getClosureRisk, getScheduleSuggest |
| `/market` | Market | 시장 환경 분석 | getDemographics, getCompetitors, getOptimalStart |

#### 대시보드 (`/`)

- **목적:** 학원 운영 현황을 한눈에 파악
- **구성 요소:**
  - 수요 지표 요약 카드 4장 (수강생 수, 전환율, 상담 건수, 수요 등급)
  - 30일 수요 추세 차트 (Recharts ComposedChart -- 영역 + 라인)
  - 시스템 알림 패널 (폐강 위험, 마케팅 타이밍 등)
- **데이터:** 실시간 API 연동 (Phase D)

#### 시뮬레이터 (`/simulator`)

- **목적:** 신규 강좌 개설 전 수요와 운영 지표를 종합적으로 시뮬레이션
- **입력:** 강좌명, 분야 (coding/security/game/art), 개강 예정일
- **출력:**
  - 예상 수강생 수 + 수요 등급 (TierBadge)
  - 신뢰 구간 (lower ~ upper)
  - 운영 가이드: 필요 강사 수, 권장 강의실 수
  - 마케팅 제안: 광고 시작 시점, 얼리버드 기간, 할인율
  - Low 등급 시 폐강 위험 경고 배너
- **데이터:** 실시간 API 연동 (Phase D)

#### 마케팅 분석 (`/marketing`)

- **목적:** 분야별 잠재 수강생 전환 현황 분석 + 등급별 광고 전략 수립
- **입력:** 분야 선택 (FieldSelector)
- **섹션 A -- 잠재 수강생 전환 예측:**
  - 예상 전환 수 (큰 숫자 카드)
  - 전환율 추세 차트 (8주, LineChart)
  - 상담 건수 추세 차트 (8주, BarChart)
  - 분야별 추천 액션 리스트
- **섹션 B -- 광고 타이밍 추천:**
  - High / Mid / Low 등급별 3장 카드
  - 각 카드: 광고 시작 시기 (N주 전), 얼리버드 기간 (N일), 할인율 (N%)
- **데이터:** 실시간 API 연동 (Phase D)

#### 운영 관리 (`/operations`)

- **목적:** 개설 확정된 강좌의 폐강 위험 평가 + 구체적 운영 계획 수립
- **입력:** 강좌명, 분야, 개강일 (폼 입력 후 "분석 실행")
- **섹션 A -- 폐강 위험도 평가:**
  - 위험도 게이지 (RiskGauge, 0~1 점수)
  - 위험 등급 배지 (high=빨강, medium=노랑, low=초록)
  - 위험 요인 리스트
  - 권장 조치 텍스트
- **섹션 B -- 강사/강의실 배정 계획:**
  - 필요 강사 수, 필요 강의실 수 (아이콘 카드)
  - 반별 배정 테이블 (반명, 강사, 시간대, 강의실)
  - 배정 요약 텍스트
- **데이터:** 실시간 API 연동 (Phase D)

#### 시장 분석 (`/market`)

- **목적:** 시장 환경 분석을 통한 전략적 의사결정 지원
- **입력:** 분야 선택 (FieldSelector)
- **섹션 A -- 수강생 인구통계:**
  - 연령대 분포 (PieChart -- 20대/30대/40대+)
  - 수강 목적 분포 (가로 BarChart -- 취업/취미/자격증)
  - 트렌드 배지 (증가/안정/감소)
- **섹션 B -- 경쟁 학원 동향:**
  - 경쟁사 개강 수 (큰 숫자 카드)
  - 평균 수강료 (만원 단위)
  - 포화도 지수 게이지 (0~2)
  - 전략 추천 텍스트
- **섹션 C -- 최적 개강일 추천:**
  - 상위 5개 후보 카드 (날짜, 예상 수강생, 수요 등급, 종합 점수)
  - 1위 카드에 "추천" 배지 강조
- **데이터:** 실시간 API 연동 (Phase D)

### 5.2 컴포넌트 의존 관계

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

### 5.3 페이지 간 기능 관계

```
┌──────────────────────────────────────────────────────┐
│                    대시보드 (/)                        │
│              전체 현황 요약 + 알림                      │
└──────────────┬───────────────────────────────────────┘
               │
    ┌──────────▼──────────┐
    │  시뮬레이터           │  ← "이 강좌 열면 어떨까?" (의사결정 개요)
    │  /simulator          │
    │  수요 + 운영 + 마케팅  │
    └───┬─────┬────────┬──┘
        │     │        │
   ┌────▼──┐ ┌▼─────┐ ┌▼──────────┐
   │마케팅  │ │운영   │ │시장 분석   │
   │분석   │ │관리   │ │/market    │
   │/mktg  │ │/ops   │ │           │
   └───────┘ └──────┘ └───────────┘
    전환 예측   폐강 위험   인구통계
    광고 전략   배정 상세   경쟁사 동향
                          최적 개강일
```

#### 시뮬레이터 vs 하위 3페이지

| 관점 | 시뮬레이터 | 마케팅/운영/시장 분석 |
|------|----------|-------------------|
| **깊이** | 종합 요약 (넓고 얕게) | 영역별 상세 (좁고 깊게) |
| **사용 시점** | 강좌 개설 검토 단계 | 개설 확정 후 실행 단계 |
| **데이터 범위** | 단일 강좌 예측 결과 | 분야 전체 추세/분포 |

### 5.4 스타일링

CSS custom properties 기반 (Tailwind 미사용):

```css
--color-primary, --color-success, --color-warning, --color-danger
--space-xs ~ --space-xl
--radius-sm, --radius-md, --radius-lg
```

---

## 6. 백엔드 API

### 6.1 엔드포인트 전체 목록

> 이 테이블이 API 엔드포인트의 **단일 진실 공급원(Single Source of Truth)**이다.
> 다른 문서에서 엔드포인트를 참조할 때는 이 섹션을 기준으로 한다.

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

### 6.2 주요 API 스키마

#### 수요 예측 (`/api/v1/demand/predict`)

**요청:**
```json
{
  "course_name": "Python 웹개발",
  "start_date": "2026-07-01",
  "field": "coding",
  "model_name": "ensemble"
}
```

**응답:**
```json
{
  "course_name": "Python 웹개발",
  "predicted_enrollment": 25,
  "demand_tier": "HIGH",
  "confidence_interval": { "lower": 20.0, "upper": 30.0 },
  "model_used": "ensemble",
  "prediction_date": "2026-04-10T12:00:00Z"
}
```

#### 폐강 위험 (`/api/v1/demand/closure-risk`)

**응답:**
```json
{
  "risk_score": 0.72,
  "risk_level": "high",
  "contributing_factors": [
    "예측 수강생 수 부족: 3명 (LOW 등급)",
    "신뢰 구간 하한(1.5명)이 최소 개강 인원(5명) 미만"
  ],
  "recommendation": "마케팅 강화 및 조기 등록 할인 적용을 권장합니다."
}
```

#### 강사/강의실 배정 (`/api/v1/schedule/suggest`)

**배정 규칙:** 반 편성 = ceil(수강생/15), 강사 = 반 수, 강의실 = ceil(반/2) (오전/오후 분할)

**응답:**
```json
{
  "course_name": "Python 웹개발",
  "required_instructors": 2,
  "required_classrooms": 1,
  "assignment_plan": {
    "classes": [
      { "class_name": "A반", "instructor_slot": "강사 1", "time_slot": "오전 (09:00-12:00)", "classroom": "강의실 1" },
      { "class_name": "B반", "instructor_slot": "강사 2", "time_slot": "오후 (13:00-16:00)", "classroom": "강의실 1" }
    ],
    "summary": "30명 기준: 2개 반 편성 (반당 15명), 강사 2명, 강의실 1개 (오전/오후 분할)"
  }
}
```

#### 광고 타이밍 (`/api/v1/marketing/timing`)

**등급별 규칙:**

| 수요 등급 | 광고 시작 | 얼리버드 기간 | 할인율 |
|----------|----------|-------------|--------|
| High | 2주 전 | 7일 | 5% |
| Mid | 3주 전 | 14일 | 10% |
| Low | 4주 전 | 21일 | 15% |

#### 전환 예측 (`/api/v1/marketing/lead-conversion`)

**응답:**
```json
{
  "field": "coding",
  "estimated_conversions": 42,
  "conversion_rate_trend": [0.32, 0.35, 0.33, 0.38, 0.36, 0.40, 0.39, 0.42],
  "consultation_count_trend": [120, 115, 130, 125, 140, 135, 150, 145],
  "recommendations": [
    "전환율이 상승 추세입니다. 현재 마케팅 전략을 유지하세요.",
    "상담 후 미등록 고객에 대한 후속 연락을 강화하세요."
  ]
}
```

#### 시나리오 분석 (`/api/v1/simulation/simulate`)

**응답:**
```json
{
  "baseline": { "predicted_enrollment": 25, "demand_tier": "HIGH", "estimated_revenue": 2500000 },
  "optimistic": { "predicted_enrollment": 30, "demand_tier": "HIGH", "estimated_revenue": 3000000 },
  "pessimistic": { "predicted_enrollment": 20, "demand_tier": "MID", "estimated_revenue": 2000000 },
  "market_context": { "competitor_openings": 8, "competitor_avg_price": 1200000 }
}
```

#### 최적 개강일 (`/api/v1/simulation/optimal-start`)

**점수 산정 공식:**

```
composite_score = enrollment * 0.5 + job_score * 0.3 + low_competition * 0.2
```

### 6.3 서버 구동

```bash
# 개발 모드
.venv/bin/python -m uvicorn edupulse.api.main:app --reload

# 서버 시작 시 자동 실행:
# 1. load_models() → XGBoost/LSTM/Prophet 로딩 → Ensemble 구성
# 2. CORS 미들웨어 설정
# 3. 5개 라우터 등록 (/api/v1 prefix)
```

### 6.4 모델 로딩 흐름

```
서버 시작 (lifespan)
  └── load_models()  (dependencies.py)
        ├── XGBoostForecaster.load("saved/xgboost", v1)
        ├── ProphetForecaster.load("saved/prophet", v1)
        ├── LSTMForecaster.load("saved/lstm", v1)
        └── EnsembleForecaster(models={성공한 모델들})
              → Prophet 실패 시 XGBoost+LSTM 또는 XGBoost 단독 폴백
```

---

## 7. AI 모델 개요

### 7.1 모델 구성

| 모델 | 유형 | MAPE | 학습 환경 |
|---|---|---|---|
| **XGBoost** | 그래디언트 부스팅 | 16.20% | M4 MacBook / Droplet |
| **LSTM** | 딥러닝 (RNN) | 40.32% | M4 MacBook 전용 (MPS) |
| **Prophet** | 시계열 분해 | 45.44% | M4 MacBook / Droplet |
| **Ensemble** | 가중 평균 결합 | - | 런타임 |

### 7.2 수요 등급 분류

```python
DEMAND_THRESHOLDS = {"high": 6, "mid": 3}  # 주간 기준

HIGH: >= 6명/주
MID:  >= 3명/주
LOW:  < 3명/주
```

모델 상세 (하이퍼파라미터, 피처, 학습 방식)는 → [data-and-model.md](data-and-model.md) 참조

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
        └── feat/frontend-enhancement-v2   (머지 완료)
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
| `CLAUDE.md` | AI 코딩 에이전트 가이드 |
| `docs/architecture.md` | **본 문서** -- 프로젝트 구조 + 기능 + API 스펙 |
| `docs/data-and-model.md` | 데이터 파이프라인 + 모델 가이드 |
| `docs/frontend-integration.md` | 프론트엔드-백엔드 연동 가이드 |
| `docs/ai_plans/` | AI 기반 설계 문서 (4개) |
| `docs/ai_reports/` | AI 활용 리포트 (#1~#7 + 모델 해설, 총 8개) |
| `docs/ai_collaboration_index.md` | AI 협업 문서 인덱스 (리포트 + 계획서 + 이관 문서) |
