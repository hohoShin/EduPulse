# 프론트엔드-백엔드 연동 가이드

> **최종 업데이트:** 2026-04-10
> **현재 상태:** Phase D 완료 (전체 5페이지 실시간 API 연동)
> **관련 문서:** [architecture.md](architecture.md), [data-and-model.md](data-and-model.md)

---

## 1. 개요

Phase A(Mock-First Scaffold)에서 구축한 5개 페이지 + 12개 adapter 메서드를 기반으로,
실제 FastAPI 백엔드와 연결하는 Phase B -> C -> D를 구현한 과정과 구조를 정리한다.

**핵심 원칙:** 페이지 코드는 변경하지 않는다. adapter 레이어만 교체하면 mock <-> real 전환이 완료되는 구조.

---

## 2. 아키텍처

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌───────────┐
│  Pages (5)  │ ──▸ │  index.js    │ ──▸ │  mockAdapter.js  │     │           │
│  Dashboard  │     │  (Selector)  │     │  realAdapter.js  │ ──▸ │  FastAPI   │
│  Simulator  │     │              │     │  hybridAdapter.js│     │  Backend   │
│  Marketing  │     │ VITE_ADAPTER │     │                  │     │           │
│  Operations │     │ 환경변수 기반  │     └──────────────────┘     └───────────┘
│  Market     │     │ 어댑터 선택   │            │
└─────────────┘     └──────────────┘      ┌─────┴──────┐
                                          │            │
                                    transformers.js  errors.js
                                    (응답 변환)      (에러 통일)
```

### 어댑터 전환 흐름

| VITE_ADAPTER 값 | 동작 | 용도 |
|---|---|---|
| `mock` (기본값) | 전체 mock fixture 사용 | 백엔드 없이 프론트 개발 |
| `hybrid` | Dashboard 3개 -> mock, 나머지 9개 -> real | 점진 전환 |
| `real` | 전체 실제 API 호출 | 운영 환경 |

---

## 3. Phase별 구현 상세

### 3.1 Phase B -- Contract Hardening

목표: adapter 인터페이스 고정, 에러 형식 통일, 변환 유틸리티 준비.

#### 생성된 파일

| 파일 | 역할 |
|---|---|
| `src/api/types.js` | JSDoc typedef (UIState, SummaryCard 등). 런타임 코드 없음 |
| `src/api/transformers.js` | 백엔드 응답 -> UI 기대 형태로 변환 (10개 함수) |
| `src/api/errors.js` | HTTP 에러 -> 한글 UIState 에러 객체 |

#### transformers.js -- 변환 함수 목록

| 함수 | 백엔드 엔드포인트 | 변환 내용 |
|---|---|---|
| `transformHealthResponse` | `GET /health` | flat 객체 -> StatusItem[] 배열 |
| `transformSimulateResponse` | `POST /simulation/simulate` | 3시나리오 -> SimulatorResult (baseline 기준) |
| `transformLeadConversionResponse` | `POST /marketing/lead-conversion` | `recommendations: str[]` -> `{text, link}[]` |
| `transformClosureRiskResponse` | `POST /demand/closure-risk` | `risk_trend: null` 등 누락 필드 보충 |
| `transformCompetitorResponse` | `POST /simulation/competitors` | `previous_openings: null` 등 보충 |
| `transformDemographicsResponse` | `POST /simulation/demographics` | pass-through + `total_students: null` |
| `transformScheduleResponse` | `POST /schedule/suggest` | snake_case 구조 유지 |
| `transformMarketingTimingResponse` | `POST /marketing/timing` | `demand_tier`, 할인율 등 추출 |
| `transformOptimalStartResponse` | `POST /simulation/optimal-start` | `top_candidates` 배열 추출 |
| `transformDemandResponse` | `POST /demand/predict` | raw pass-through |

#### errors.js -- 에러 분류 규칙

| 조건 | 한글 메시지 |
|---|---|
| `TypeError` (네트워크 불가) | "서버에 연결할 수 없습니다" |
| HTTP 422 | "잘못된 입력입니다" |
| HTTP 5xx | "서버 오류가 발생했습니다" |
| 기타 | "알 수 없는 오류가 발생했습니다" |

---

### 3.2 Phase C -- Real Integration

목표: realAdapter를 실제 HTTP 호출로 구현, 환경변수 기반 어댑터 전환.

#### 생성/수정된 파일

| 파일 | Action | 내용 |
|---|---|---|
| `src/api/client.js` | NEW | native fetch 래퍼 (`apiGet`, `apiPost`) |
| `.env.development` | NEW | `VITE_API_BASE_URL=`, `VITE_ADAPTER=mock` |
| `.env.production` | NEW | `VITE_ADAPTER=real` |
| `vite.config.js` | MODIFY | dev proxy: `/api` -> `http://localhost:8000` |
| `src/api/adapters/index.js` | MODIFY | 환경변수 기반 어댑터 선택 + hybrid 추가 |
| `src/api/adapters/hybridAdapter.js` | NEW | Dashboard->mock, 나머지->real 위임 |
| `src/api/adapters/realAdapter.js` | MODIFY | 12개 메서드 전체 구현 |

#### client.js -- API 클라이언트 설계

```javascript
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function apiGet(path)          // GET + JSON 파싱
export async function apiPost(path, body)   // POST + JSON 파싱
// 에러 시 err.status 속성 포함 -> toErrorUIState()에서 분류
```

- 외부 라이브러리(axios 등) 없이 native fetch만 사용
- 개발 모드에서는 Vite proxy가 `/api` 요청을 `localhost:8000`으로 전달

#### realAdapter.js -- 12개 메서드 구현 구조

**Group 1 -- 직접 매핑 (5개)**

엔드포인트 상세는 -> [architecture.md](architecture.md) SS6 참조

| 메서드 | 설명 |
|---|---|
| `getSystemStatus()` | 서버/모델/DB/메모리 상태 |
| `getLeadConversion({field})` | 잠재 수강생 전환 분석 |
| `getDemographics({field})` | 연령/성별 분포 |
| `getCompetitors({field})` | 경쟁 분석 |
| `getClosureRisk({courseName, field, startDate})` | 폐강 위험 평가 |

**Group 2 -- API 체이닝 (3개)**

엔드포인트 상세는 -> [architecture.md](architecture.md) SS6 참조

| 메서드 | 호출 흐름 | 설명 |
|---|---|---|
| `getScheduleSuggest` | `demand/predict` -> `schedule/suggest` | 수요 예측 결과로 강사/교실 배정 |
| `getMarketingTiming({field})` | `marketing/timing` x 3 (HIGH/MID/LOW 병렬) | 수요 등급별 마케팅 타이밍 |
| `getOptimalStart({field, startDate, endDate})` | `simulation/optimal-start` | 최적 개강일 후보 |

`getMarketingTiming` 상세 흐름:
```javascript
const [r1, r2, r3] = await Promise.all([
  apiPost('/api/v1/marketing/timing', { ..., demand_tier: 'HIGH' }),
  apiPost('/api/v1/marketing/timing', { ..., demand_tier: 'MID' }),
  apiPost('/api/v1/marketing/timing', { ..., demand_tier: 'LOW' }),
]);
// 배열로 반환 -- 페이지가 Array.isArray() 검사 후 .map()
return createUIState({ data: [transform(r1), transform(r2), transform(r3)] });
```

**Group 3 -- 복합 체이닝 (1개)**

`simulateDemand({courseName, field, startDate})`:
```
(1) POST /simulation/simulate -> baseline/optimistic/pessimistic
(2) 병렬:
   - POST /marketing/timing (baseline.demand_tier)
   - POST /schedule/suggest (baseline.predicted_enrollment)
(3) SimulatorResult 조립 (marketing + operations 필드 추가)
```

**Group 4 -- 대시보드 클라이언트 조합 (3개, Phase D)**

| 메서드 | 조합 방식 | 출력 |
|---|---|---|
| `getDashboardSummary` | demographics + competitors + demand/predict 병렬 | SummaryCard[] (3장) |
| `getDemandChart` | simulation/optimal-start (8주 윈도우) | ChartPoint[] (최대 5개) |
| `getDashboardAlerts` | demand/closure-risk | AlertItem[] 또는 empty |

---

### 3.3 Phase D -- Dashboard Expansion

목표: 대시보드를 기존 API 조합으로 실시간 데이터 표시.

#### getDashboardSummary -- 카드 3장 조립

```javascript
const [, compRaw, demandRaw] = await Promise.all([
  apiPost('/api/v1/simulation/demographics', { field }),
  apiPost('/api/v1/simulation/competitors', { field }),
  apiPost('/api/v1/demand/predict', { course_name: '기본과정', start_date: futureDate(4), field }),
]);

// SummaryCard 3장
cards = [
  { id: 'total-students',    title: '예상 수강생',  value: demandRaw.predicted_enrollment },
  { id: 'competitor-count',   title: '경쟁 강좌',   value: compRaw.competitor_openings },
  { id: 'demand-index',       title: '수요 지수',   value: demandRaw.demand_tier },
];
```

#### getDashboardAlerts -- 폐강 위험 기반 알림

| risk_level | 알림 유형 | 메시지 |
|---|---|---|
| `high` | critical | 폐강 위험 + recommendation |
| `medium` | warning | 폐강 주의 + recommendation |
| `low` | (표시 안 함) | empty 상태 반환 |

#### Dashboard.jsx 변경

```jsx
// 데모 스위처를 개발 모드에서만 표시
{import.meta.env.DEV && renderDemoSwitcher()}
```

---

## 4. snake_case 원칙과 데이터 형태 규약

### 4.1 문제 발견

최초 구현 시 transformer가 backend 응답을 camelCase로 변환했으나,
페이지들은 mock fixture의 **snake_case** 속성명을 직접 참조하고 있었다.

```
Backend (snake_case) -> transformer (camelCase 변환) -> Page (snake_case 기대) -> undefined
```

### 4.2 해결 원칙

```
Backend (snake_case) -> transformer (snake_case 유지) -> Page (snake_case 소비) -> OK
```

**예외 2가지** -- viewModels.js 팩토리 함수가 camelCase를 정의하는 경우:
1. `createStatusItem` -> `{ label, status, checkedAt, details }` (camelCase)
2. `createSimulatorResult` -> `{ courseName, predictedCount, demandTier, ... }` (camelCase)

이 두 경우는 팩토리 함수 입력으로 camelCase를 전달하되, 출력 형태가 곧 페이지 소비 형태이므로 문제없다.

### 4.3 adapter 메서드 출력 패턴

```javascript
// 일반 패턴 -- transformer가 snake_case 출력
async function getXxx(input = {}) {
  try {
    const raw = await apiPost('/api/v1/xxx', { field: input.field || 'coding' });
    return createUIState({ state: 'success', data: transformXxxResponse(raw), isDemo: false });
  } catch (err) {
    return toErrorUIState(err);
  }
}

// 대시보드 패턴 -- raw 응답을 직접 사용 (이미 snake_case)
async function getDashboardSummary({ field } = {}) {
  const [, compRaw, demandRaw] = await Promise.all([...]);
  const cards = [
    createSummaryCard('id', 'title', demandRaw.predicted_enrollment, '명', ...),
  ];
  return createUIState({ state: 'success', data: cards, isDemo: false });
}
```

---

## 5. 환경 설정

### 5.1 프론트엔드 환경변수

| 파일 | 변수 | 기본값 | 설명 |
|---|---|---|---|
| `.env.development` | `VITE_API_BASE_URL` | (빈 문자열) | API 기본 URL (proxy 사용 시 불필요) |
| `.env.development` | `VITE_ADAPTER` | `mock` | 어댑터 선택 |
| `.env.production` | `VITE_ADAPTER` | `real` | 운영 환경은 항상 real |

### 5.2 Vite Dev Proxy

```javascript
// vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

개발 모드에서 `/api/*` 요청이 자동으로 FastAPI 서버(`localhost:8000`)로 전달된다.
CORS 설정 없이 개발 가능.

### 5.3 백엔드 환경변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `MODEL_VERSION` | `1` | 사용할 모델 버전 (`model/saved/{name}/v{N}/`) |

```python
# edupulse/model/predict.py
MODEL_VERSION = int(os.environ.get("MODEL_VERSION", 1))
```

---

## 6. 실행 방법

### 6.1 Mock 모드 (백엔드 불필요)

```bash
cd frontend
echo 'VITE_ADAPTER=mock' > .env.development.local
npm run dev
# -> http://localhost:5173 (전체 mock 데이터)
```

### 6.2 Hybrid 모드 (백엔드 + mock 대시보드)

```bash
# 터미널 1 -- 백엔드
cd /path/to/edupulse
.venv/bin/python -m uvicorn edupulse.api.main:app --reload

# 터미널 2 -- 프론트엔드
cd frontend
echo 'VITE_ADAPTER=hybrid' > .env.development.local
npm run dev
# -> Dashboard: mock, 나머지 4페이지: 실제 API
```

### 6.3 Real 모드 (전체 실시간)

```bash
# 터미널 1 -- 백엔드 (동일)
# 터미널 2 -- 프론트엔드
echo 'VITE_ADAPTER=real' > .env.development.local
npm run dev
# -> 전체 5페이지 실제 API
```

---

## 7. 알려진 제한사항

> LSTM 모델 하이퍼파라미터 튜닝 이력은 -> [data-and-model.md](data-and-model.md) SS6.4 참조

### 7.1 Prophet 모델 로딩 실패

```
앙상블: Prophet 로딩 실패: StringDtype.__init__() got an unexpected keyword argument 'na_value'
```

pandas와 Prophet 간 버전 호환성 문제. Prophet 1.3.0으로 업그레이드 완료된 상태이나
pandas 2.x의 `StringDtype` 변경이 원인으로, 추후 Prophet 업데이트 시 해결 예상.
앙상블 모델은 Prophet 실패 시 자동으로 XGBoost 단독 예측으로 폴백된다.

### 7.2 대시보드 데이터 제한

- `getDashboardSummary`의 trend 값은 `null` (이력 비교 API 미존재)
- `getDemandChart`는 최대 5포인트, confidence band 없음
- 향후 전용 `GET /api/v1/demand/forecast` 엔드포인트 추가 시 개선 가능

### 7.3 기본값 의존

realAdapter의 여러 메서드가 기본값을 사용:
- `course_name`: `'기본과정'`
- `field`: `'coding'`
- `price_per_student`: `500000`

실제 운영 시 페이지에서 사용자 입력을 전달하도록 연결 필요.

---

## 8. 파일 변경 총정리

### 신규 생성 (8개)

| 파일 | Phase | 설명 |
|---|---|---|
| `src/api/types.js` | B | JSDoc 타입 정의 |
| `src/api/transformers.js` | B | 백엔드 응답 변환 (10개 함수) |
| `src/api/errors.js` | B | HTTP 에러 -> 한글 UIState |
| `src/api/client.js` | C | fetch 래퍼 (apiGet, apiPost) |
| `src/api/adapters/hybridAdapter.js` | C | mock/real 혼합 어댑터 |
| `.env.development` | C | 개발 환경변수 |
| `.env.production` | C | 운영 환경변수 |
| `docs/frontend-integration.md` | -- | 본 문서 |

### 수정 (4개)

| 파일 | Phase | 변경 내용 |
|---|---|---|
| `vite.config.js` | C | dev proxy 추가 (`/api` -> `localhost:8000`) |
| `src/api/adapters/index.js` | C | 환경변수 기반 어댑터 선택 + hybrid 지원 |
| `src/api/adapters/realAdapter.js` | C+D | 12개 메서드 전체 구현 |
| `src/pages/Dashboard.jsx` | D | 데모 스위처 개발 모드 한정 |

### 변경 없음

- `mockAdapter.js`, `viewModels.js`, fixtures 전체, 5개 페이지 (Dashboard 1줄 제외)

---

## 9. Frontend <-> Backend 엔드포인트 매핑 전체표

| Adapter 메서드 | HTTP Method | Backend Endpoint | 요청 Body 주요 필드 |
|---|---|---|---|
| `getSystemStatus` | GET | `/api/v1/health` | (없음) |
| `getLeadConversion` | POST | `/api/v1/marketing/lead-conversion` | `field` |
| `getDemographics` | POST | `/api/v1/simulation/demographics` | `field` |
| `getCompetitors` | POST | `/api/v1/simulation/competitors` | `field` |
| `getClosureRisk` | POST | `/api/v1/demand/closure-risk` | `course_name`, `start_date`, `field` |
| `getScheduleSuggest` | POST | `/api/v1/demand/predict` -> `/api/v1/schedule/suggest` | `course_name`, `start_date`, `field` |
| `getMarketingTiming` | POST | `/api/v1/marketing/timing` x 3 | `course_name`, `start_date`, `demand_tier` |
| `getOptimalStart` | POST | `/api/v1/simulation/optimal-start` | `course_name`, `field`, `search_window_start/end` |
| `simulateDemand` | POST | `/api/v1/simulation/simulate` -> timing + suggest | `course_name`, `field`, `start_date`, `price_per_student` |
| `getDashboardSummary` | POST | demographics + competitors + demand/predict | `field` |
| `getDemandChart` | POST | `/api/v1/simulation/optimal-start` | `course_name`, `field`, `search_window_start/end` |
| `getDashboardAlerts` | POST | `/api/v1/demand/closure-risk` | `course_name`, `start_date`, `field` |
