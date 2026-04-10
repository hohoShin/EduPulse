# EduPulse 전체 기능 정리

**최종 업데이트:** 2026-04-10
**버전:** Phase A (Mock 데이터 기반 프론트엔드 + 백엔드 API 구현 완료)

---

## 1. 서비스 개요

EduPulse는 코딩·보안·게임·아트 분야 학원을 위한 **AI 기반 수강 수요 예측 솔루션**이다.
내부 데이터(수강 이력, 상담 로그)와 외부 데이터(검색 트렌드, 채용 공고)를 통합 분석하여
수요 예측 → 운영 계획 → 마케팅 전략 → 시장 분석까지 의사결정 전 과정을 지원한다.

### 핵심 가치

| 영역 | 해결하는 문제 | 핵심 산출물 |
|------|-------------|------------|
| **수요 예측** | "다음 분기에 몇 명이 올까?" | 수강생 수 + 수요 등급 (High/Mid/Low) |
| **운영 관리** | "강좌를 열어도 될까? 어떻게 운영하지?" | 폐강 위험도 + 강사/강의실 배정 |
| **마케팅** | "언제, 어떻게 홍보할까?" | 광고 타이밍 + 전환 예측 + 할인율 |
| **시장 분석** | "시장 상황은? 언제 열어야 유리한가?" | 경쟁사 동향 + 인구통계 + 최적 개강일 |

---

## 2. 전체 기능 목록

### 2.1 프론트엔드 (5페이지)

#### 대시보드 (`/`)
- **목적:** 학원 운영 현황을 한눈에 파악
- **구성 요소:**
  - 수요 지표 요약 카드 4장 (수강생 수, 전환율, 상담 건수, 수요 등급)
  - 30일 수요 추세 차트 (Recharts ComposedChart — 영역 + 라인)
  - 시스템 알림 패널 (폐강 위험, 마케팅 타이밍 등)
- **데이터:** Mock (Phase A)

#### 시뮬레이터 (`/simulator`)
- **목적:** 신규 강좌 개설 전 수요와 운영 지표를 종합적으로 시뮬레이션
- **입력:** 강좌명, 분야 (coding/security/game/art), 개강 예정일
- **출력:**
  - 예상 수강생 수 + 수요 등급 (TierBadge)
  - 신뢰 구간 (lower ~ upper)
  - 운영 가이드: 필요 강사 수, 권장 강의실 수
  - 마케팅 제안: 광고 시작 시점, 얼리버드 기간, 할인율
  - Low 등급 시 폐강 위험 경고 배너
- **데이터:** Mock (Phase A)

#### 마케팅 분석 (`/marketing`)
- **목적:** 분야별 잠재 수강생 전환 현황 분석 + 등급별 광고 전략 수립
- **입력:** 분야 선택 (FieldSelector)
- **섹션 A — 잠재 수강생 전환 예측:**
  - 예상 전환 수 (큰 숫자 카드)
  - 전환율 추세 차트 (8주, LineChart)
  - 상담 건수 추세 차트 (8주, BarChart)
  - 분야별 추천 액션 리스트
- **섹션 B — 광고 타이밍 추천:**
  - High / Mid / Low 등급별 3장 카드
  - 각 카드: 광고 시작 시기 (N주 전), 얼리버드 기간 (N일), 할인율 (N%)
- **데이터:** Mock (Phase A)

#### 운영 관리 (`/operations`)
- **목적:** 개설 확정된 강좌의 폐강 위험 평가 + 구체적 운영 계획 수립
- **입력:** 강좌명, 분야, 개강일 (폼 입력 후 "분석 실행")
- **섹션 A — 폐강 위험도 평가:**
  - 위험도 게이지 (RiskGauge, 0~1 점수)
  - 위험 등급 배지 (high=빨강, medium=노랑, low=초록)
  - 위험 요인 리스트
  - 권장 조치 텍스트
- **섹션 B — 강사/강의실 배정 계획:**
  - 필요 강사 수, 필요 강의실 수 (아이콘 카드)
  - 반별 배정 테이블 (반명, 강사, 시간대, 강의실)
  - 배정 요약 텍스트
- **데이터:** Mock (Phase A)

#### 시장 분석 (`/market`)
- **목적:** 시장 환경 분석을 통한 전략적 의사결정 지원
- **입력:** 분야 선택 (FieldSelector)
- **섹션 A — 수강생 인구통계:**
  - 연령대 분포 (PieChart — 20대/30대/40대+)
  - 수강 목적 분포 (가로 BarChart — 취업/취미/자격증)
  - 트렌드 배지 (증가/안정/감소)
- **섹션 B — 경쟁 학원 동향:**
  - 경쟁사 개강 수 (큰 숫자 카드)
  - 평균 수강료 (만원 단위)
  - 포화도 지수 게이지 (0~2)
  - 전략 추천 텍스트
- **섹션 C — 최적 개강일 추천:**
  - 상위 5개 후보 카드 (날짜, 예상 수강생, 수요 등급, 종합 점수)
  - 1위 카드에 "추천" 배지 강조
- **데이터:** Mock (Phase A)

---

### 2.2 백엔드 API (10개 엔드포인트)

#### 상태 확인

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/health` | GET | 서버 상태, 모델 로딩, DB 연결 확인 |

#### 수요 예측

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/demand/predict` | POST | 수강 수요 예측 (수강생 수 + 등급 + 신뢰 구간) |
| `/api/v1/demand/closure-risk` | POST | 폐강 위험도 평가 (위험 점수 + 등급 + 요인 + 권장 조치) |

**입력 스키마 (공통):**
```json
{
  "course_name": "Python 웹개발",
  "start_date": "2026-07-01",
  "field": "coding",
  "model_name": "ensemble"
}
```

**수요 예측 응답:**
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

**폐강 위험 응답:**
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

#### 운영 관리

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/schedule/suggest` | POST | 강사/강의실 배정 계획 생성 |

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

#### 마케팅

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/marketing/timing` | POST | 수요 등급별 광고 타이밍 + 얼리버드 + 할인율 |
| `/api/v1/marketing/lead-conversion` | POST | 잠재 수강생 전환 예측 (추세 + 추천 액션) |

**광고 타이밍 규칙:**

| 수요 등급 | 광고 시작 | 얼리버드 기간 | 할인율 |
|----------|----------|-------------|--------|
| High | 2주 전 | 7일 | 5% |
| Mid | 3주 전 | 14일 | 10% |
| Low | 4주 전 | 21일 | 15% |

**전환 예측 응답:**
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

#### 시뮬레이션 / 시장 분석

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/simulation/simulate` | POST | 신규 강좌 시나리오 분석 (baseline/optimistic/pessimistic) |
| `/api/v1/simulation/optimal-start` | POST | 최적 개강일 추천 (상위 5개, 복합 점수) |
| `/api/v1/simulation/demographics` | POST | 분야별 수강생 인구통계 (연령/목적/트렌드) |
| `/api/v1/simulation/competitors` | POST | 경쟁 학원 동향 (개강 수, 수강료, 포화도) |

**최적 개강일 점수 산정:** `composite_score = enrollment × 0.5 + job_score × 0.3 + low_competition × 0.2`

**시나리오 분석 응답:**
```json
{
  "baseline": { "predicted_enrollment": 25, "demand_tier": "HIGH", "estimated_revenue": 2500000 },
  "optimistic": { "predicted_enrollment": 30, "demand_tier": "HIGH", "estimated_revenue": 3000000 },
  "pessimistic": { "predicted_enrollment": 20, "demand_tier": "MID", "estimated_revenue": 2000000 },
  "market_context": { "competitor_openings": 8, "competitor_avg_price": 1200000 }
}
```

---

### 2.3 AI 모델

#### 모델 구성

| 모델 | 유형 | 피처 수 | MAPE | 학습 환경 |
|------|------|---------|------|----------|
| **XGBoost** | 그래디언트 부스팅 | 19개 | 16.20% | M4 MacBook / Droplet |
| **Prophet** | 시계열 분해 | ds + y | - | M4 MacBook / Droplet |
| **LSTM** | 딥러닝 (RNN) | 19개 | - | M4 MacBook 전용 (MPS) |
| **Ensemble** | 가중 평균 결합 | - | - | 런타임 |

#### 피처 목록 (19개)

| 카테고리 | 피처 | 설명 |
|----------|------|------|
| 시계열 (5) | `lag_1w`, `lag_2w`, `lag_4w`, `lag_8w`, `rolling_mean_4w` | 과거 수강생 수 지연값 + 이동 평균 |
| 날짜/분야 (3) | `month_sin`, `month_cos`, `field_encoded` | 월 순환 인코딩 + 분야 인코딩 |
| 외부 지표 (2) | `search_volume`, `job_count` | 검색량 + 채용 공고 수 |
| 내부 선행 (2) | `consultation_count`, `page_views` | 상담 건수 + 웹 조회수 |
| 자격증 (2) | `has_cert_exam`, `weeks_to_exam` | 자격증 시험 유무 + 시험까지 주수 |
| 경쟁사 (2) | `competitor_openings`, `competitor_avg_price` | 경쟁사 개강 수 + 평균 수강료 |
| 계절 이벤트 (3) | `is_vacation`, `is_exam_season`, `is_semester_start` | 방학/시험/학기 시작 여부 |

#### 제거된 피처

| 피처 | 제거 사유 |
|------|----------|
| `cart_abandon_rate` | 학원에 장바구니 개념 없음 (온라인 쇼핑몰 지표) |
| `conversion_rate` | 타겟(enrollment)과 순환 의존 → 데이터 누수 |
| `age_group_diversity` | 등록 후에만 계산 가능한 사후 지표 |

---

### 2.4 데이터 파이프라인

#### 데이터 소스 (9개 합성 CSV)

| 파일 | 내용 | 생성 모듈 |
|------|------|----------|
| `enrollment_logs.csv` | 주간 분야별 수강 이력 | `enrollment_generator.py` |
| `search_trends.csv` | 분야별 검색량 (Naver 기반) | `external_generator.py` |
| `job_postings.csv` | 분야별 채용 공고 수 | `external_generator.py` |
| `consultation_logs.csv` | 상담 건수 + 등록 전환 | `external_generator.py` |
| `web_logs.csv` | 웹사이트 페이지 조회수 | `external_generator.py` |
| `cert_schedule.csv` | 자격증 시험 일정 | `external_generator.py` |
| `competitor_data.csv` | 경쟁 학원 개강/수강료 | `external_generator.py` |
| `seasonal_events.csv` | 방학/시험/학기 이벤트 | `external_generator.py` |
| `student_profiles.csv` | 수강생 연령/목적 프로필 | `external_generator.py` |

#### 처리 흐름

```
수집 (Collection)
  ├── Naver DataLab API → search_trends.csv
  ├── 합성 생성기 → 나머지 8개 CSV
  └── (미래: 크롤링, DB 연동)
        ↓
전처리 (Preprocessing)
  ├── cleaner.py    → 결측치 보간 + 이상치 처리
  ├── transformer.py → 지연 피처 + 시계열 인코딩
  └── merger.py     → 9개 CSV 통합 병합
        ↓
모델링 (Modeling)
  ├── build_features() → 19개 피처 벡터 생성
  ├── 3종 모델 학습 (XGBoost, Prophet, LSTM)
  └── 앙상블 결합 → 최종 예측
        ↓
서비스 (API)
  └── FastAPI 10개 엔드포인트 → 프론트엔드 (React)
```

---

## 3. 페이지 간 기능 관계

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

### 시뮬레이터 vs 하위 3페이지

| 관점 | 시뮬레이터 | 마케팅/운영/시장 분석 |
|------|----------|-------------------|
| **깊이** | 종합 요약 (넓고 얕게) | 영역별 상세 (좁고 깊게) |
| **사용 시점** | 강좌 개설 검토 단계 | 개설 확정 후 실행 단계 |
| **데이터 범위** | 단일 강좌 예측 결과 | 분야 전체 추세/분포 |

---

## 4. 기술 스택

| 영역 | 기술 |
|------|------|
| **프론트엔드** | React 18.3, React Router 7, Recharts 3.8, Vite 8 |
| **스타일링** | CSS 변수 (커스텀 프로퍼티), 인라인 스타일 |
| **백엔드** | FastAPI, Pydantic v2 |
| **AI 모델** | XGBoost, Prophet, PyTorch (LSTM) |
| **데이터** | Pandas, NumPy, scikit-learn |
| **수집** | Naver DataLab API, BeautifulSoup, Selenium |
| **DB** | PostgreSQL, SQLAlchemy |
| **배포** | Docker, DigitalOcean Droplet (1vCPU/2GB) |
| **학습** | M4 MacBook (MPS — LSTM 전용) |

---

## 5. 개발 현황

### Phase A (현재) — Mock 데이터 기반

| 항목 | 상태 |
|------|------|
| 백엔드 API 10개 엔드포인트 | 구현 완료 |
| AI 모델 3종 + 앙상블 | 구현 완료 |
| 합성 데이터 9개 CSV | 구현 완료 |
| 프론트엔드 5페이지 | 구현 완료 (Mock 어댑터) |
| 프론트↔백엔드 연동 | 미착수 |

### Phase B (예정) — 실제 API 연동

| 항목 | 설명 |
|------|------|
| `realAdapter.js` 구현 | Mock → Real 어댑터 전환 |
| API 호출 연동 | 각 페이지에서 실제 FastAPI 엔드포인트 호출 |
| 에러 핸들링 | 네트워크 오류, 타임아웃, 서버 에러 처리 |
| 인증/권한 | (필요 시) JWT 기반 인증 추가 |
| DB 연동 | PostgreSQL 실데이터 기반 예측 |

---

## 6. 파일 구조 요약

### 프론트엔드 (`frontend/src/`)

```
pages/
  ├── Dashboard.jsx       대시보드
  ├── Simulator.jsx       시뮬레이터
  ├── Marketing.jsx       마케팅 분석
  ├── Operations.jsx      운영 관리
  └── Market.jsx          시장 분석

components/
  ├── Layout.jsx          사이드바 + 헤더 레이아웃
  ├── DemandChart.jsx     수요 추세 차트
  ├── AlertPanel.jsx      알림 패널
  ├── StatusPanel.jsx     상태 표시 (로딩/빈값/에러)
  ├── TierBadge.jsx       수요 등급 배지
  ├── FieldSelector.jsx   분야 선택 드롭다운
  ├── RiskGauge.jsx       위험도 게이지
  └── ScoreBar.jsx        점수 바

fixtures/
  ├── dashboardStates.js      대시보드 Mock
  ├── simulatorStates.js      시뮬레이터 Mock
  ├── systemStatusStates.js   시스템 상태 Mock
  ├── marketingStates.js      마케팅 Mock (분야별)
  ├── operationsStates.js     운영 Mock
  └── marketStates.js         시장 분석 Mock (분야별)

api/adapters/
  ├── mockAdapter.js      Mock 어댑터 (Phase A)
  ├── realAdapter.js      Real 어댑터 (Phase B)
  └── index.js            어댑터 라우터
```

### 백엔드 (`edupulse/`)

```
api/
  ├── main.py             FastAPI 앱 진입점
  ├── routers/
  │   ├── health.py       GET  /health
  │   ├── demand.py       POST /demand/predict, /demand/closure-risk
  │   ├── schedule.py     POST /schedule/suggest
  │   ├── marketing.py    POST /marketing/timing, /marketing/lead-conversion
  │   └── simulation.py   POST /simulation/simulate, optimal-start, demographics, competitors
  ├── schemas/            Pydantic 요청/응답 스키마
  └── services/           비즈니스 로직 (marketing, simulation, demand, schedule)

model/
  ├── predict.py          수요 예측 메인 (build_features + 모델 호출)
  ├── ensemble.py         앙상블 결합
  ├── xgboost_model.py    XGBoost (19 피처, MAPE 16.20%)
  ├── prophet_model.py    Prophet (시계열 분해)
  ├── lstm_model.py       LSTM (PyTorch, MPS 지원)
  └── saved/              저장된 모델 파일
```
