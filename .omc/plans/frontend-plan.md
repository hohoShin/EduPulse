# EduPulse Frontend 구현 계획서 (Person B 전용)

> **Plan ID:** frontend-plan
> **생성일:** 2026-04-07
> **상위 계획:** edupulse-full-build (v2)
> **담당:** Person B (Frontend + API 통합 + DevOps)
> **기간:** 10일 (Day 1 ~ Day 10)
> **기술 스택:** Vite + React 18 + Recharts + CSS Modules + fetch API

---

## 1. 프로젝트 초기 셋업

### 1.1 Vite 프로젝트 생성

```bash
# 프로젝트 루트에서 실행
cd /path/to/edupulse
npm create vite@latest frontend -- --template react
cd frontend
npm install
```

### 1.2 의존성 설치

```bash
# 핵심 의존성
npm install react-router-dom recharts

# 개발 의존성
npm install -D @types/react @types/react-dom
```

> **참고:** Tailwind CSS 대신 **CSS Modules**를 권장한다.
> - 이유 1: 추가 설정이 Vite에서 zero-config (`.module.css` 파일만 생성하면 동작)
> - 이유 2: 컴포넌트별 스타일 격리가 자동으로 보장됨
> - 이유 3: Tailwind 설치/설정 시간(PostCSS, tailwind.config.js)을 절약하여 MVP 속도에 유리
> - 이유 4: 2인 팀에서 클래스명 컨벤션 합의 없이도 충돌 없음

### 1.3 디렉토리 구조

```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── Dockerfile                    # Phase 4 (Day 9)
├── nginx.conf                    # Phase 4 (Day 9)
├── public/
│   └── favicon.svg
└── src/
    ├── main.jsx                  # ReactDOM.createRoot 진입점
    ├── App.jsx                   # React Router 라우팅 정의
    ├── App.module.css
    ├── index.css                 # 글로벌 CSS 리셋 + CSS 변수
    │
    ├── api/
    │   ├── client.js             # fetch 기반 API 클라이언트
    │   └── mockData.js           # Phase 2용 mock 데이터
    │
    ├── hooks/
    │   ├── useApi.js             # 범용 API 호출 hook (loading/error/data)
    │   └── useDemand.js          # 수요 예측 전용 hook
    │
    ├── pages/
    │   ├── Dashboard.jsx         # 메인 대시보드 페이지
    │   ├── Dashboard.module.css
    │   ├── Simulator.jsx         # 수요 시뮬레이션 페이지
    │   └── Simulator.module.css
    │
    └── components/
        ├── Layout.jsx            # 공통 레이아웃 (사이드바 + 헤더 + main)
        ├── Layout.module.css
        ├── DemandChart.jsx       # Recharts 시계열 차트
        ├── DemandChart.module.css
        ├── TierBadge.jsx         # High/Mid/Low 수요 등급 뱃지
        ├── TierBadge.module.css
        ├── AlertPanel.jsx        # 폐강 리스크 알림 패널
        ├── AlertPanel.module.css
        ├── LoadingSpinner.jsx    # 로딩 상태 표시
        ├── ErrorMessage.jsx      # 에러 상태 표시
        └── EmptyState.jsx        # 데이터 없음 상태 표시
```

### 1.4 vite.config.js

```js
// frontend/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
});
```

### 1.5 글로벌 CSS 변수 (index.css)

```css
/* frontend/src/index.css */
:root {
  /* 색상 팔레트 */
  --color-primary: #2563eb;
  --color-primary-light: #3b82f6;
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-text: #1e293b;
  --color-text-secondary: #64748b;
  --color-border: #e2e8f0;

  /* 수요 등급 색상 */
  --color-tier-high: #16a34a;
  --color-tier-high-bg: #dcfce7;
  --color-tier-mid: #ca8a04;
  --color-tier-mid-bg: #fef9c3;
  --color-tier-low: #dc2626;
  --color-tier-low-bg: #fee2e2;

  /* 간격 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;

  /* 폰트 */
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 16px;
  line-height: 1.5;
  color: var(--color-text);
  background-color: var(--color-bg);
}

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  min-height: 100vh;
}
```

---

## 2. 컴포넌트 계층 구조 (Props / State)

### 2.1 컴포넌트 트리

```
App
├── Layout
│   ├── Sidebar (Layout 내부)
│   ├── Header (Layout 내부)
│   └── <Outlet />  ← React Router
│       ├── Dashboard
│       │   ├── DemandChart      (props: predictions[])
│       │   ├── TierBadge        (props: tier, size?)
│       │   ├── AlertPanel       (props: alerts[])
│       │   ├── LoadingSpinner
│       │   ├── ErrorMessage     (props: message, onRetry?)
│       │   └── EmptyState       (props: message)
│       │
│       └── Simulator
│           ├── SimulatorForm    (Simulator 내부)
│           ├── TierBadge        (props: tier)
│           ├── DemandChart      (props: predictions[])
│           ├── LoadingSpinner
│           └── ErrorMessage     (props: message, onRetry?)
```

### 2.2 각 컴포넌트 시그니처

#### Layout.jsx

```jsx
/**
 * 공통 레이아웃 컴포넌트.
 * 사이드바 내비게이션 + 상단 헤더 + 메인 콘텐츠 영역.
 * React Router의 <Outlet />으로 하위 페이지를 렌더링한다.
 *
 * State: 없음 (순수 레이아웃)
 * Props: 없음 (children은 <Outlet />으로 주입)
 */
export default function Layout() { ... }
```

- 사이드바 네비게이션 항목: Dashboard (`/`), Simulator (`/simulator`)
- 현재 활성 경로는 `useLocation()` 으로 판별하여 시각적 강조
- 헤더: "EduPulse" 로고 텍스트 + 현재 페이지 제목

#### Dashboard.jsx (Page)

```jsx
/**
 * 메인 대시보드 페이지.
 * 4개 분야별 수요 예측 결과를 차트 + 카드 형태로 표시.
 *
 * State:
 *   predictions: DemandResponse[] | null    -- 4개 분야별 예측 결과 배열
 *   loading: boolean                        -- API 호출 중 여부
 *   error: string | null                    -- 에러 메시지
 *   selectedField: string | 'all'           -- 분야 필터 ('all' | 'coding' | 'security' | 'game' | 'art')
 *
 * API 호출:
 *   마운트 시 4개 분야에 대해 POST /api/v1/demand/predict 호출 (Promise.all)
 */
export default function Dashboard() { ... }
```

#### Simulator.jsx (Page)

```jsx
/**
 * 수요 시뮬레이션 페이지.
 * 사용자가 과정 정보를 입력하면 수요 예측 + 스케줄링 + 마케팅 타이밍을 표시.
 *
 * State:
 *   formData: { course_name: string, start_date: string, field: string }
 *   result: {
 *     demand: DemandResponse | null,
 *     schedule: ScheduleResponse | null,
 *     marketing: MarketingResponse | null,
 *   }
 *   loading: boolean
 *   error: string | null
 *   step: 'form' | 'result'                -- 폼 입력 vs 결과 표시 전환
 *
 * API 호출 순서 (submit 시):
 *   1. POST /api/v1/demand/predict -> demand 결과
 *   2. demand 결과의 predicted_enrollment로 POST /api/v1/schedule/suggest
 *   3. demand 결과의 demand_tier로 POST /api/v1/marketing/timing
 *   세 호출 중 2, 3은 1의 결과에 의존하므로 1 완료 후 Promise.all([2, 3])
 */
export default function Simulator() { ... }
```

#### DemandChart.jsx (Component)

```jsx
/**
 * Recharts 기반 수요 예측 시각화 차트.
 *
 * Props:
 *   predictions: Array<{
 *     course_name: string,
 *     field: string,
 *     predicted_enrollment: number,
 *     demand_tier: 'High' | 'Mid' | 'Low',
 *     confidence_interval: { lower: number, upper: number },
 *   }>
 *   chartType?: 'bar' | 'composed'         -- 기본: 'bar'
 *     - 'bar': 분야별 예측 인원 비교 (Dashboard용)
 *     - 'composed': 예측 인원 + 신뢰 구간 (Simulator용)
 *
 * State: 없음 (순수 표현 컴포넌트)
 */
export default function DemandChart({ predictions, chartType = 'bar' }) { ... }
```

- Dashboard에서는 `chartType='bar'`: 4개 분야별 예측 인원을 BarChart로 비교
- Simulator에서는 `chartType='composed'`: 단일 과정의 예측 인원 + 신뢰 구간을 ComposedChart(Bar + ErrorBar 또는 Area)로 표시

#### TierBadge.jsx (Component)

```jsx
/**
 * 수요 등급 뱃지. High=초록, Mid=노랑, Low=빨강.
 *
 * Props:
 *   tier: 'High' | 'Mid' | 'Low'           -- 수요 등급
 *   size?: 'sm' | 'md' | 'lg'              -- 기본: 'md'
 *
 * State: 없음 (순수 표현 컴포넌트)
 */
export default function TierBadge({ tier, size = 'md' }) { ... }
```

- 색상 매핑: `High -> --color-tier-high`, `Mid -> --color-tier-mid`, `Low -> --color-tier-low`
- 크기: `sm(12px/20px)`, `md(14px/28px)`, `lg(16px/36px)` (font-size/height)

#### AlertPanel.jsx (Component)

```jsx
/**
 * 폐강 리스크 및 마케팅 타이밍 알림 패널.
 * demand_tier가 'Low'인 과정에 대해 경고를 표시한다.
 *
 * Props:
 *   alerts: Array<{
 *     course_name: string,
 *     field: string,
 *     demand_tier: 'High' | 'Mid' | 'Low',
 *     predicted_enrollment: number,
 *     message: string,                     -- 예: "폐강 리스크: 예상 등록 8명 (기준 12명 미만)"
 *   }>
 *
 * State: 없음 (순수 표현 컴포넌트)
 */
export default function AlertPanel({ alerts }) { ... }
```

- Low 등급: 빨간색 경고 아이콘 + "폐강 리스크" 메시지
- Mid 등급: 노란색 주의 아이콘 + "마케팅 강화 권장" 메시지
- High 등급: AlertPanel에 표시하지 않음

#### LoadingSpinner.jsx / ErrorMessage.jsx / EmptyState.jsx

```jsx
// LoadingSpinner.jsx
/**
 * Props: 없음 (또는 message?: string)
 * 화면 중앙 CSS spinner + "데이터를 불러오는 중..." 텍스트
 */

// ErrorMessage.jsx
/**
 * Props:
 *   message: string             -- 에러 메시지
 *   onRetry?: () => void        -- 재시도 버튼 클릭 핸들러 (없으면 버튼 숨김)
 */

// EmptyState.jsx
/**
 * Props:
 *   message?: string            -- 기본: "표시할 데이터가 없습니다."
 */
```

---

## 3. 페이지별 구현 상세

### 3.1 Dashboard.jsx

#### 레이아웃 구성

```
+------------------------------------------------------------------+
|  Layout (사이드바 + 헤더)                                          |
|  +--------------------------------------------------------------+|
|  |  Dashboard                                                    ||
|  |  +----------------------------------------------------------+||
|  |  |  필터 바: [전체] [코딩] [보안] [게임] [아트]                 |||
|  |  +----------------------------------------------------------+||
|  |  |                                                          |||
|  |  |  +------------------------+  +------------------------+  |||
|  |  |  | 요약 카드 1            |  | 요약 카드 2            |  |||
|  |  |  | "코딩" [High]         |  | "보안" [Mid]           |  |||
|  |  |  | 예상 등록: 28명        |  | 예상 등록: 18명        |  |||
|  |  |  +------------------------+  +------------------------+  |||
|  |  |  +------------------------+  +------------------------+  |||
|  |  |  | 요약 카드 3            |  | 요약 카드 4            |  |||
|  |  |  | "게임" [Low]          |  | "아트" [Mid]           |  |||
|  |  |  | 예상 등록: 9명         |  | 예상 등록: 15명        |  |||
|  |  |  +------------------------+  +------------------------+  |||
|  |  |                                                          |||
|  |  |  +------------------------------------------------------+|||
|  |  |  | DemandChart (BarChart)                                ||||
|  |  |  | 분야별 예측 인원 비교                                   ||||
|  |  |  +------------------------------------------------------+|||
|  |  |                                                          |||
|  |  |  +------------------------------------------------------+|||
|  |  |  | AlertPanel                                            ||||
|  |  |  | [경고] 게임 분야: 폐강 리스크 (9명 < 12명)              ||||
|  |  |  +------------------------------------------------------+|||
|  |  +----------------------------------------------------------+||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+
```

#### 데이터 흐름

1. 마운트 시 4개 분야에 대해 수요 예측 API를 호출한다 (기본 과정명 + 다음 달 시작일 기준)
2. 결과를 `predictions` state에 저장
3. 요약 카드 4개를 그리드(2x2)로 렌더링. 각 카드에 `TierBadge` 포함
4. `DemandChart`에 전체 predictions 배열 전달
5. `AlertPanel`에 `demand_tier === 'Low'` 또는 `'Mid'`인 항목만 필터링하여 전달
6. 분야 필터 클릭 시 `selectedField` state 변경 -> 카드와 차트를 필터링

#### Dashboard 기본 예측 요청 목록

```js
// Dashboard 마운트 시 호출할 4개 요청
const DEFAULT_COURSES = [
  { course_name: 'Python 웹개발 부트캠프', start_date: '2026-05-01', field: 'coding' },
  { course_name: '정보보안 전문가 과정', start_date: '2026-05-01', field: 'security' },
  { course_name: '게임 개발 Unity 과정', start_date: '2026-05-01', field: 'game' },
  { course_name: '디지털 아트 포트폴리오', start_date: '2026-05-01', field: 'art' },
];
```

### 3.2 Simulator.jsx

#### 레이아웃 구성

```
+------------------------------------------------------------------+
|  Layout                                                           |
|  +--------------------------------------------------------------+|
|  |  Simulator                                                    ||
|  |  +----------------------------------------------------------+||
|  |  |  [step: 'form']                                          |||
|  |  |                                                          |||
|  |  |  과정명:    [___________________________]                 |||
|  |  |  시작일:    [____-__-__] (date picker)                    |||
|  |  |  분야:      (o) 코딩  ( ) 보안  ( ) 게임  ( ) 아트        |||
|  |  |                                                          |||
|  |  |            [     예측 실행     ]                           |||
|  |  +----------------------------------------------------------+||
|  |                                                               ||
|  |  +----------------------------------------------------------+||
|  |  |  [step: 'result'] (예측 완료 후 표시)                      |||
|  |  |                                                          |||
|  |  |  +--- 수요 예측 결과 ---+  +--- 운영 제안 ---+            |||
|  |  |  | 예상 등록: 28명      |  | 필요 강사: 2명   |            |||
|  |  |  | 등급: [High]        |  | 필요 강의실: 1개 |            |||
|  |  |  | 신뢰구간: 22~34명   |  | 배정 계획: ...   |            |||
|  |  |  | 모델: xgboost       |  |                  |            |||
|  |  |  +---------------------+  +------------------+            |||
|  |  |                                                          |||
|  |  |  +--- 마케팅 타이밍 ---+                                  |||
|  |  |  | 광고 시작: 2주 전    |                                  |||
|  |  |  | 얼리버드: 7일       |                                  |||
|  |  |  | 할인율: 5%          |                                  |||
|  |  |  +---------------------+                                  |||
|  |  |                                                          |||
|  |  |  +------------------------------------------------------+|||
|  |  |  | DemandChart (composed)                                ||||
|  |  |  | 예측 인원 + 신뢰 구간 시각화                             ||||
|  |  |  +------------------------------------------------------+|||
|  |  |                                                          |||
|  |  |  [     다시 시뮬레이션     ]                               |||
|  |  +----------------------------------------------------------+||
|  +--------------------------------------------------------------+|
+------------------------------------------------------------------+
```

#### 폼 검증 규칙

| 필드 | 타입 | 검증 규칙 | 에러 메시지 |
|---|---|---|---|
| `course_name` | text | 필수, 2자 이상 100자 이하 | "과정명을 입력해 주세요." |
| `start_date` | date | 필수, 오늘 이후 날짜 | "시작일은 오늘 이후여야 합니다." |
| `field` | radio | 필수, 4개 중 택 1 | "분야를 선택해 주세요." |

#### API 호출 시퀀스

```
사용자 [예측 실행] 클릭
  |
  v
POST /api/v1/demand/predict
  |
  +---> 성공: demand 결과 수신
  |       |
  |       +---> Promise.all([
  |       |       POST /api/v1/schedule/suggest  (predicted_enrollment 사용)
  |       |       POST /api/v1/marketing/timing  (demand_tier 사용)
  |       |     ])
  |       |       |
  |       |       +---> 성공: schedule + marketing 결과 수신 -> step='result'
  |       |       +---> 실패: 부분 결과 표시 (demand 결과는 보이고, 나머지는 에러)
  |       |
  |       +---> 실패: error state 설정 -> ErrorMessage 표시
```

---

## 4. API Client 구현

### 4.1 fetch Wrapper (`frontend/src/api/client.js`)

```js
// frontend/src/api/client.js

const BASE_URL = '/api/v1';

// 환경 변수로 mock/real 전환
// .env.development에 VITE_USE_MOCK=true 설정하면 mock 데이터 사용
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

/**
 * 공통 fetch wrapper.
 * - JSON request/response 기본 처리
 * - 에러 응답 시 message 추출하여 throw
 * - mock 모드일 때 mockData 반환
 *
 * @param {string} endpoint - API 경로 (예: '/demand/predict')
 * @param {object} options - fetch options (method, body 등)
 * @param {Function|null} mockFn - mock 모드일 때 호출할 함수
 * @returns {Promise<object>} API 응답 JSON
 */
async function request(endpoint, options = {}, mockFn = null) {
  // mock 모드
  if (USE_MOCK && mockFn) {
    // 네트워크 지연 시뮬레이션 (300-800ms)
    await new Promise((r) => setTimeout(r, 300 + Math.random() * 500));
    return mockFn(options.body ? JSON.parse(options.body) : null);
  }

  const url = `${BASE_URL}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    let errorMessage = `API 오류 (${response.status})`;

    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // JSON 파싱 실패 시 기본 메시지 사용
    }

    if (response.status === 503) {
      throw new Error('모델이 아직 로딩되지 않았습니다. 잠시 후 다시 시도해 주세요.');
    }
    if (response.status === 422) {
      throw new Error('입력값이 올바르지 않습니다. 다시 확인해 주세요.');
    }

    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * 수요 예측 API
 * @param {{ course_name: string, start_date: string, field: string }} params
 * @returns {Promise<DemandResponse>}
 */
export async function predictDemand(params) {
  return request(
    '/demand/predict',
    {
      method: 'POST',
      body: JSON.stringify(params),
    },
    (body) => getMockDemandResponse(body)
  );
}

/**
 * 강사 스케줄링 API
 * @param {{ course_name: string, start_date: string, predicted_enrollment: number }} params
 * @returns {Promise<ScheduleResponse>}
 */
export async function suggestSchedule(params) {
  return request(
    '/schedule/suggest',
    {
      method: 'POST',
      body: JSON.stringify(params),
    },
    (body) => getMockScheduleResponse(body)
  );
}

/**
 * 마케팅 타이밍 API
 * @param {{ course_name: string, start_date: string, demand_tier: string }} params
 * @returns {Promise<MarketingResponse>}
 */
export async function getMarketingTiming(params) {
  return request(
    '/marketing/timing',
    {
      method: 'POST',
      body: JSON.stringify(params),
    },
    (body) => getMockMarketingResponse(body)
  );
}

/**
 * 헬스 체크 API
 * @returns {Promise<HealthResponse>}
 */
export async function checkHealth() {
  return request('/health', { method: 'GET' }, () => getMockHealthResponse());
}

// --- Mock 함수 import ---
import {
  getMockDemandResponse,
  getMockScheduleResponse,
  getMockMarketingResponse,
  getMockHealthResponse,
} from './mockData';
```

### 4.2 Mock/Real 전환 메커니즘

```bash
# frontend/.env.development (개발 중 mock 사용)
VITE_USE_MOCK=true

# frontend/.env.development.local (API 서버 연결 후 real 전환)
VITE_USE_MOCK=false
```

- `VITE_USE_MOCK=true`: mock 함수가 호출되며, 300-800ms 지연을 시뮬레이션한다
- `VITE_USE_MOCK=false`: 실제 fetch 호출. Vite proxy를 통해 localhost:8000으로 전달
- `.env.development.local`은 `.env.development`보다 우선순위가 높으므로, 개인 환경에서 덮어쓸 수 있음

### 4.3 Custom Hook: useApi

```js
// frontend/src/hooks/useApi.js
import { useState, useCallback } from 'react';

/**
 * 범용 API 호출 hook.
 * loading, error, data 상태를 관리한다.
 *
 * @param {Function} apiFn - API 클라이언트 함수 (예: predictDemand)
 * @returns {{ data, loading, error, execute, reset }}
 *
 * 사용 예:
 *   const { data, loading, error, execute } = useApi(predictDemand);
 *   // 호출: execute({ course_name: '...', start_date: '...', field: '...' });
 */
export default function useApi(apiFn) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(
    async (params) => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiFn(params);
        setData(result);
        return result;
      } catch (err) {
        setError(err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiFn]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}
```

---

## 5. Mock 데이터 전략

### 5.1 Mock 데이터 구조 (`frontend/src/api/mockData.js`)

모든 mock 데이터는 API 계약(Pydantic 스키마)과 1:1로 대응해야 한다.

```js
// frontend/src/api/mockData.js

// === 수요 등급별 기본 데이터 ===
const MOCK_ENROLLMENT = {
  coding: { predicted_enrollment: 28, demand_tier: 'High' },
  security: { predicted_enrollment: 18, demand_tier: 'Mid' },
  game: { predicted_enrollment: 9, demand_tier: 'Low' },
  art: { predicted_enrollment: 15, demand_tier: 'Mid' },
};

/**
 * POST /api/v1/demand/predict mock 응답
 *
 * @param {{ course_name: string, start_date: string, field: string }} body
 * @returns {DemandResponse}
 */
export function getMockDemandResponse(body) {
  const base = MOCK_ENROLLMENT[body.field] || MOCK_ENROLLMENT.coding;
  const enrollment = base.predicted_enrollment;

  return {
    course_name: body.course_name,
    field: body.field,
    predicted_enrollment: enrollment,
    demand_tier: base.demand_tier,
    confidence_interval: {
      lower: Math.round(enrollment * 0.8),
      upper: Math.round(enrollment * 1.2),
    },
    model_used: 'xgboost',
    prediction_date: new Date().toISOString(),
  };
}

/**
 * POST /api/v1/schedule/suggest mock 응답
 *
 * @param {{ course_name: string, start_date: string, predicted_enrollment: number }} body
 * @returns {ScheduleResponse}
 */
export function getMockScheduleResponse(body) {
  const enrollment = body.predicted_enrollment;
  const instructors = Math.ceil(enrollment / 15);
  const classrooms = Math.ceil(enrollment / 30);

  return {
    required_instructors: instructors,
    required_classrooms: classrooms,
    assignment_plan: Array.from({ length: instructors }, (_, i) => ({
      instructor_id: i + 1,
      instructor_name: `강사 ${String.fromCharCode(65 + i)}`,
      assigned_students: Math.min(
        15,
        enrollment - i * 15
      ),
      classroom: `${Math.floor(i / 2) + 1}0${(i % 2) + 1}호`,
    })),
  };
}

/**
 * POST /api/v1/marketing/timing mock 응답
 *
 * @param {{ course_name: string, start_date: string, demand_tier: string }} body
 * @returns {MarketingResponse}
 */
export function getMockMarketingResponse(body) {
  const tierConfig = {
    High: { ad_launch_weeks_before: 2, earlybird_duration_days: 7, discount_rate: 0.05 },
    Mid: { ad_launch_weeks_before: 3, earlybird_duration_days: 14, discount_rate: 0.1 },
    Low: { ad_launch_weeks_before: 4, earlybird_duration_days: 21, discount_rate: 0.15 },
  };

  return tierConfig[body.demand_tier] || tierConfig.Mid;
}

/**
 * GET /api/v1/health mock 응답
 * @returns {HealthResponse}
 */
export function getMockHealthResponse() {
  return {
    status: 'ok',
    models_loaded: ['xgboost'],
    db_connected: true,
    memory_usage_mb: 456.7,
  };
}

// === Dashboard 초기 로딩용 기본 과정 목록 ===
export const DEFAULT_COURSES = [
  { course_name: 'Python 웹개발 부트캠프', start_date: '2026-05-01', field: 'coding' },
  { course_name: '정보보안 전문가 과정', start_date: '2026-05-01', field: 'security' },
  { course_name: '게임 개발 Unity 과정', start_date: '2026-05-01', field: 'game' },
  { course_name: '디지털 아트 포트폴리오', start_date: '2026-05-01', field: 'art' },
];

// === 분야별 한글 라벨 ===
export const FIELD_LABELS = {
  coding: '코딩',
  security: '보안',
  game: '게임',
  art: '아트',
};
```

### 5.2 Mock 데이터 검증 체크리스트

| API 엔드포인트 | Mock 응답 필드 | 실제 API 스키마 필드 | 일치 여부 |
|---|---|---|---|
| `/demand/predict` | `course_name, field, predicted_enrollment, demand_tier, confidence_interval.lower, confidence_interval.upper, model_used, prediction_date` | 동일 | O |
| `/schedule/suggest` | `required_instructors, required_classrooms, assignment_plan[].instructor_id, instructor_name, assigned_students, classroom` | 동일 | O |
| `/marketing/timing` | `ad_launch_weeks_before, earlybird_duration_days, discount_rate` | 동일 | O |
| `/health` | `status, models_loaded[], db_connected, memory_usage_mb` | 동일 | O |

---

## 6. 에러/로딩/빈 상태 처리

### 6.1 상태별 표시 전략

| 페이지 | Loading 상태 | Error 상태 | Empty 상태 |
|---|---|---|---|
| **Dashboard** | 요약 카드 4개 + 차트 영역에 skeleton shimmer 또는 `<LoadingSpinner />` | `<ErrorMessage message="..." onRetry={refetch} />` 전체 교체 | `<EmptyState message="예측 데이터가 없습니다. API 서버 상태를 확인해 주세요." />` |
| **Simulator (form)** | 해당 없음 | 해당 없음 | 기본 폼 표시 |
| **Simulator (submit 후)** | 버튼 비활성화 + `<LoadingSpinner />` 결과 영역에 표시 | `<ErrorMessage message="..." onRetry={handleSubmit} />` 결과 영역에 표시 | 해당 없음 (API가 항상 결과 반환) |
| **AlertPanel** | 상위 Dashboard loading에 종속 | 상위 Dashboard error에 종속 | "현재 폐강 리스크가 있는 과정이 없습니다." 메시지 |

### 6.2 에러 메시지 매핑

```js
// 에러 유형별 사용자 친화적 메시지
const ERROR_MESSAGES = {
  // fetch 자체 실패 (네트워크 오류)
  'Failed to fetch': '서버에 연결할 수 없습니다. 네트워크 상태를 확인해 주세요.',

  // API 서버 에러
  503: '모델이 아직 로딩되지 않았습니다. 잠시 후 다시 시도해 주세요.',
  422: '입력값이 올바르지 않습니다. 다시 확인해 주세요.',
  500: '서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',

  // 기본
  default: '알 수 없는 오류가 발생했습니다.',
};
```

### 6.3 ErrorMessage 컴포넌트 렌더링 예시

```jsx
// 사용 예시
<ErrorMessage
  message="서버에 연결할 수 없습니다."
  onRetry={() => fetchPredictions()}
/>

// 렌더링 결과:
// +------------------------------------------+
// |  [!] 오류 발생                             |
// |                                          |
// |  서버에 연결할 수 없습니다.                  |
// |                                          |
// |       [ 다시 시도 ]                        |
// +------------------------------------------+
```

---

## 7. App.jsx 라우팅 구성

```jsx
// frontend/src/App.jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Simulator from './pages/Simulator';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="simulator" element={<Simulator />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

---

## 8. Day-by-Day 작업 분해 (Person B)

### Day 1-2: Phase 1 -- 프로젝트 초기화

#### Day 1 (공동 작업)

| 작업 | 산출물 | 예상 소요 |
|---|---|---|
| .gitignore 수정 (Python + Node.js 패턴 추가) | `.gitignore` | 30분 |
| 프로젝트 전체 디렉토리 빈 폴더 생성 | 각 디렉토리에 `.gitkeep` | 30분 |
| Person A와 스키마 계약 리뷰 | 계약 문서 확인 | 1시간 |

**Day 1 수락 기준:**
```bash
# .gitignore에 node_modules, frontend/dist 포함 확인
grep "node_modules" .gitignore
grep "frontend/dist" .gitignore
# 디렉토리 구조 확인
ls frontend/ data/ api/ model/ preprocessing/
```

#### Day 2 (Frontend 착수)

| 작업 | 산출물 | 예상 소요 |
|---|---|---|
| Vite + React 프로젝트 초기화 | `frontend/` 전체 | 30분 |
| 의존성 설치 (react-router-dom, recharts) | `package.json` 업데이트 | 15분 |
| vite.config.js proxy 설정 | `frontend/vite.config.js` | 15분 |
| index.css 글로벌 CSS 변수 작성 | `frontend/src/index.css` | 30분 |
| App.jsx 라우팅 구성 | `frontend/src/App.jsx` | 30분 |
| Layout.jsx + Layout.module.css 구현 | 사이드바 + 헤더 + Outlet | 2시간 |
| API client.js 기본 구조 작성 (fetch wrapper) | `frontend/src/api/client.js` | 1시간 |
| useApi.js custom hook 작성 | `frontend/src/hooks/useApi.js` | 30분 |
| .env.development 파일 작성 (VITE_USE_MOCK=true) | `frontend/.env.development` | 10분 |

**Day 2 수락 기준:**
```bash
# 1. 개발 서버 기동
cd frontend && npm run dev
# 기대: VITE v5.x.x ready -- Local: http://localhost:5173/

# 2. 브라우저에서 확인
# http://localhost:5173/ -> Layout 렌더링 (사이드바 + 헤더 + 빈 메인 영역)
# http://localhost:5173/simulator -> Layout + "Simulator" 텍스트 (placeholder)

# 3. 사이드바 네비게이션 동작
# "대시보드" 클릭 -> / 이동
# "시뮬레이터" 클릭 -> /simulator 이동
# 현재 페이지 네비게이션 항목이 시각적으로 강조됨

# 4. Vite proxy 설정 확인 (API 서버 미기동 상태에서)
# 브라우저 DevTools Network 탭에서 /api/v1/health 호출 시
# 502 Bad Gateway (서버 없으므로 정상 -- proxy는 동작)
```

---

### Day 3-4: Phase 2 -- Dashboard + Simulator (Mock Data)

#### Day 3

| 작업 | 산출물 | 예상 소요 |
|---|---|---|
| mockData.js 작성 (4개 API 모두) | `frontend/src/api/mockData.js` | 1시간 |
| client.js mock 함수 연결 | `frontend/src/api/client.js` 수정 | 30분 |
| TierBadge.jsx + CSS 구현 | `TierBadge.jsx`, `TierBadge.module.css` | 1시간 |
| DemandChart.jsx + CSS 구현 (BarChart) | `DemandChart.jsx`, `DemandChart.module.css` | 2시간 |
| Dashboard.jsx 기본 구조 (요약 카드 4개 + 차트 + 필터) | `Dashboard.jsx`, `Dashboard.module.css` | 3시간 |

**Day 3 수락 기준:**
```
# 브라우저에서 http://localhost:5173/ 확인

1. 4개 요약 카드가 2x2 그리드로 표시됨
   - 각 카드에 과정명, 분야, 예상 등록 인원, TierBadge 표시
   - coding: 28명 [High], security: 18명 [Mid], game: 9명 [Low], art: 15명 [Mid]

2. DemandChart(BarChart)에 4개 분야 막대가 표시됨
   - X축: 분야명 (코딩, 보안, 게임, 아트)
   - Y축: 예측 인원
   - 각 막대에 수요 등급별 색상 적용

3. TierBadge 색상 구분
   - High: 초록색 배경
   - Mid: 노란색 배경
   - Low: 빨간색 배경

4. 분야 필터 버튼 동작
   - [전체] 클릭 -> 4개 모두 표시
   - [코딩] 클릭 -> 코딩만 표시

5. Mock 데이터 사용 중 (VITE_USE_MOCK=true)
   - 300-800ms 로딩 지연이 발생하고, LoadingSpinner가 잠깐 표시됨
```

#### Day 4

| 작업 | 산출물 | 예상 소요 |
|---|---|---|
| Simulator.jsx 폼 구현 (입력 + 검증) | `Simulator.jsx`, `Simulator.module.css` | 2시간 |
| Simulator 결과 표시 영역 (수요 + 스케줄 + 마케팅) | `Simulator.jsx` 확장 | 3시간 |
| DemandChart composed 모드 구현 (신뢰 구간) | `DemandChart.jsx` 확장 | 1.5시간 |
| AlertPanel.jsx 구현 | `AlertPanel.jsx`, `AlertPanel.module.css` | 1.5시간 |

**Day 4 수락 기준:**
```
# 브라우저에서 http://localhost:5173/simulator 확인

1. 폼 입력 + 검증
   - 과정명 빈 칸으로 제출 -> "과정명을 입력해 주세요." 에러 표시
   - 시작일 과거 날짜 선택 -> "시작일은 오늘 이후여야 합니다." 에러 표시
   - 분야 미선택으로 제출 -> "분야를 선택해 주세요." 에러 표시

2. 정상 제출 후 결과 표시
   - 예측 실행 버튼 클릭 -> 로딩 스피너 -> 결과 3개 패널 표시
   - 수요 예측: 예상 등록 인원, TierBadge, 신뢰 구간, 모델명
   - 운영 제안: 필요 강사 수, 필요 강의실 수, 배정 계획 리스트
   - 마케팅 타이밍: 광고 시작 시점, 얼리버드 기간, 할인율

3. DemandChart (composed)
   - 예측 인원 막대 + 신뢰 구간 표시 (error bar 또는 area)

4. "다시 시뮬레이션" 버튼 -> 폼으로 돌아감 (이전 입력값 유지)

# 브라우저에서 http://localhost:5173/ 확인

5. AlertPanel이 Dashboard 하단에 표시됨
   - game 분야: "폐강 리스크: 예상 등록 9명 (기준 12명 미만)" 빨간색 경고
   - 기타 Low 등급 과정 경고 표시
```

---

### Day 5-6: Phase 2-3 -- API 연결 준비 + 에러 처리

#### Day 5

| 작업 | 산출물 | 예상 소요 |
|---|---|---|
| LoadingSpinner.jsx 구현 | `LoadingSpinner.jsx` | 30분 |
| ErrorMessage.jsx 구현 (재시도 버튼 포함) | `ErrorMessage.jsx` | 1시간 |
| EmptyState.jsx 구현 | `EmptyState.jsx` | 30분 |
| Dashboard 에러/로딩/빈 상태 통합 | `Dashboard.jsx` 수정 | 2시간 |
| Simulator 에러/로딩 상태 통합 | `Simulator.jsx` 수정 | 2시간 |
| client.js 에러 핸들링 강화 (네트워크 오류, timeout 처리) | `client.js` 수정 | 1시간 |

**Day 5 수락 기준:**
```
1. Dashboard 로딩 상태
   - 페이지 새로고침 시 LoadingSpinner가 표시되다가 데이터 로딩 후 사라짐

2. Dashboard 에러 상태 (mock에서 강제 에러 테스트)
   - ErrorMessage 표시 + "다시 시도" 버튼 클릭 시 재요청

3. Simulator 에러 상태
   - 예측 실행 실패 시 ErrorMessage 표시
   - "다시 시도" 클릭 시 재요청

4. AlertPanel 빈 상태
   - 모든 과정이 High일 때: "현재 폐강 리스크가 있는 과정이 없습니다." 표시

5. 네트워크 오류 처리
   - API 서버 꺼진 상태에서 VITE_USE_MOCK=false로 테스트
   - "서버에 연결할 수 없습니다." 메시지 표시 (빈 화면 아님)
```

#### Day 6

| 작업 | 산출물 | 예상 소요 |
|---|---|---|
| .env.development.local 생성 (VITE_USE_MOCK=false 전환) | `frontend/.env.development.local` | 10분 |
| Person A의 API 서버와 실제 연결 테스트 | client.js 동작 확인 | 2시간 |
| Dashboard에서 실제 API 응답으로 차트 렌더링 확인 | `Dashboard.jsx` 미세 조정 | 2시간 |
| API 응답 형식 차이 대응 (필요시 변환 로직 추가) | `client.js` 수정 | 2시간 |

**Day 6 수락 기준:**
```
# Person A의 API 서버가 localhost:8000에서 실행 중인 상태

1. VITE_USE_MOCK=false 상태에서 Dashboard 정상 렌더링
   - 실제 XGBoost 모델의 예측 결과가 차트에 표시됨
   - TierBadge가 실제 demand_tier 값 반영

2. Vite proxy 동작 확인
   - 브라우저 DevTools Network 탭에서 /api/v1/demand/predict 요청이 200 반환
   - CORS 에러 없음

3. API 서버 중지 후 에러 처리 확인
   - "서버에 연결할 수 없습니다." 메시지 표시
   - "다시 시도" 버튼 동작
```

---

### Day 7-8: Phase 3 -- 전체 API 연결 + AlertPanel

#### Day 7

| 작업 | 산출물 | 예상 소요 |
|---|---|---|
| Simulator -> demand API 실제 연결 | `Simulator.jsx` 수정 | 1.5시간 |
| Simulator -> schedule API 실제 연결 | `Simulator.jsx` 수정 | 1시간 |
| Simulator -> marketing API 실제 연결 | `Simulator.jsx` 수정 | 1시간 |
| 3개 API 순차/병렬 호출 로직 검증 | 통합 테스트 | 1.5시간 |
| AlertPanel에 실제 데이터 연결 | `Dashboard.jsx` + `AlertPanel.jsx` | 2시간 |

**Day 7 수락 기준 (중간 시연 목표):**
```
# 전체 시스템 동작 확인 (API + Frontend)

1. Dashboard -> 실제 API 예측 데이터로 차트 렌더링
2. Simulator -> 폼 제출 -> 실제 3개 API 호출 -> 결과 표시
   - 수요 예측 결과 (인원, 등급, 신뢰 구간)
   - 강사/강의실 배정 계획
   - 마케팅 타이밍 권장
3. AlertPanel -> Low 등급 과정에 대한 폐강 리스크 경고 표시
4. End-to-end 시나리오: "Python 웹개발, 2026-05-01, coding" 입력 -> 전체 결과 확인
```

#### Day 8

| 작업 | 산출물 | 예상 소요 |
|---|---|---|
| 반응형 레이아웃 적용 (모바일/태블릿) | CSS Modules 미디어 쿼리 | 3시간 |
| UI 디테일 다듬기 (간격, 폰트, 그림자 등) | 각 `.module.css` 수정 | 2시간 |
| 브라우저 호환성 확인 (Chrome, Safari) | 수동 테스트 | 1시간 |
| edge case 처리 (긴 과정명, 큰 숫자 등) | 컴포넌트 수정 | 1시간 |

**Day 8 수락 기준:**
```
1. 반응형 레이아웃
   - 데스크탑 (1280px+): 사이드바 고정 + 메인 영역
   - 태블릿 (768px-1279px): 사이드바 접힘, 햄버거 메뉴
   - 모바일 (767px 이하): 요약 카드 1열 배치, 차트 풀 너비

2. 크로스 브라우저
   - Chrome 최신: 정상 동작
   - Safari 최신: 정상 동작

3. edge case
   - 과정명 50자 이상: 텍스트 말줄임(...) 처리
   - 예측 인원 100명 이상: 차트 Y축 자동 조정
```

---

### Day 9: Phase 4 -- Frontend Dockerfile + nginx

#### Day 9

| 작업 | 산출물 | 예상 소요 |
|---|---|---|
| Frontend Dockerfile 작성 (multi-stage) | `frontend/Dockerfile` | 1.5시간 |
| nginx.conf 작성 (SPA fallback + API proxy) | `frontend/nginx.conf` | 1시간 |
| docker-compose.yml의 frontend 서비스 추가/확인 (Person A와 협업) | `docker-compose.yml` 수정 | 1시간 |
| Docker 빌드 + 실행 테스트 | 빌드/실행 검증 | 2시간 |
| Docker 내 API proxy 동작 확인 | 통합 테스트 | 1.5시간 |

#### Dockerfile (Multi-stage Build)

```dockerfile
# frontend/Dockerfile

# ---- Stage 1: Build ----
FROM node:20-alpine AS builder

WORKDIR /app

# 의존성 설치 (캐시 최적화)
COPY package.json package-lock.json ./
RUN npm ci --production=false

# 소스 복사 + 빌드
COPY . .
RUN npm run build

# ---- Stage 2: Serve ----
FROM nginx:1.27-alpine

# nginx 설정 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 빌드 결과물 복사
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### nginx.conf

```nginx
# frontend/nginx.conf

server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # gzip 압축
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1000;

    # API 프록시 -> FastAPI 서버
    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SPA 라우팅 fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 정적 파일 캐싱 (JS/CSS/이미지)
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

#### docker-compose.yml의 frontend 서비스 (참고)

```yaml
# docker-compose.yml 중 frontend 서비스 부분
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  ports:
    - "3000:80"
  depends_on:
    - api
  restart: unless-stopped
```

**Day 9 수락 기준:**
```bash
# 1. Frontend Docker 빌드 성공
docker build -t edupulse-frontend ./frontend
# 기대: Successfully built ... Successfully tagged edupulse-frontend:latest

# 2. 전체 서비스 기동
docker-compose up --build -d
docker-compose ps
# 기대: db(Up), api(Up), frontend(Up)

# 3. Frontend 접근 (nginx)
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# 기대: 200

# 4. SPA 라우팅 fallback
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/simulator
# 기대: 200 (nginx가 index.html 반환)

# 5. API proxy 동작 (nginx -> api 서비스)
curl -s http://localhost:3000/api/v1/health
# 기대: {"status":"ok","models_loaded":["xgboost"],...}

# 6. Docker 이미지 크기 확인
docker images edupulse-frontend --format "{{.Size}}"
# 기대: < 50MB (nginx:alpine + 빌드 결과물)
```

---

### Day 10: Phase 4 -- 마무리 + 문서화

#### Day 10

| 작업 | 산출물 | 예상 소요 |
|---|---|---|
| README.md Frontend 섹션 작성 | `README.md` 수정 | 1.5시간 |
| 전체 E2E 흐름 수동 테스트 (Docker 환경) | 테스트 기록 | 2시간 |
| 버그 수정 (Day 7-9에서 발견된 이슈) | 각 파일 수정 | 2시간 |
| 코드 정리 (console.log 제거, 주석 정리) | 전체 파일 | 1시간 |
| Person A와 최종 통합 확인 | 통합 테스트 | 1.5시간 |

**Day 10 수락 기준:**
```
1. README.md에 Frontend 실행 방법 포함
   - npm install, npm run dev, npm run build 명령어
   - 환경 변수 설명 (VITE_USE_MOCK)
   - Docker 빌드/실행 방법

2. E2E 시나리오 통과 (Docker 환경)
   a. http://localhost:3000 -> Dashboard 로딩 -> 4개 분야 예측 표시
   b. 분야 필터 동작
   c. AlertPanel 경고 표시 (Low 등급 존재 시)
   d. /simulator -> 폼 입력 -> 예측 실행 -> 3개 결과 패널 표시
   e. 에러 상태 확인 (API 서버 중지 후 재접속)

3. console.log 잔여 없음
   grep -r "console.log" frontend/src/ | grep -v node_modules
   # 기대: 결과 없음 (또는 의도적 로그만)

4. S3 참조 없음 확인 (메인 계획 요구사항)
   grep -ri "s3" README.md
   # 기대: 결과 없음
```

---

## 9. Recharts 차트 구현 참고

### 9.1 Dashboard용 BarChart

```jsx
// DemandChart.jsx 내부 (chartType === 'bar')
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts';

// 차트 데이터 변환
const chartData = predictions.map((p) => ({
  name: FIELD_LABELS[p.field],
  enrollment: p.predicted_enrollment,
  tier: p.demand_tier,
}));

// 등급별 색상
const TIER_COLORS = {
  High: '#16a34a',
  Mid: '#ca8a04',
  Low: '#dc2626',
};

<ResponsiveContainer width="100%" height={300}>
  <BarChart data={chartData}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="name" />
    <YAxis label={{ value: '예측 인원 (명)', angle: -90, position: 'insideLeft' }} />
    <Tooltip formatter={(value) => [`${value}명`, '예측 인원']} />
    <Legend />
    {/* 폐강 기준선 */}
    <ReferenceLine y={12} stroke="#dc2626" strokeDasharray="5 5" label="폐강 기준 (12명)" />
    <Bar dataKey="enrollment" name="예측 인원">
      {chartData.map((entry, index) => (
        <Cell key={index} fill={TIER_COLORS[entry.tier]} />
      ))}
    </Bar>
  </BarChart>
</ResponsiveContainer>
```

### 9.2 Simulator용 ComposedChart (신뢰 구간 포함)

```jsx
// DemandChart.jsx 내부 (chartType === 'composed')
import {
  ComposedChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ErrorBar,
} from 'recharts';

// 신뢰 구간을 ErrorBar로 표현
const chartData = [{
  name: prediction.course_name,
  enrollment: prediction.predicted_enrollment,
  // ErrorBar는 값 대비 +/- 범위를 받는다
  errorLower: prediction.predicted_enrollment - prediction.confidence_interval.lower,
  errorUpper: prediction.confidence_interval.upper - prediction.predicted_enrollment,
}];

<ResponsiveContainer width="100%" height={250}>
  <ComposedChart data={chartData}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="name" />
    <YAxis />
    <Tooltip />
    <Bar dataKey="enrollment" fill={TIER_COLORS[prediction.demand_tier]} barSize={60}>
      <ErrorBar
        dataKey="errorUpper"
        width={4}
        strokeWidth={2}
        stroke="#374151"
        direction="y"
      />
    </Bar>
  </ComposedChart>
</ResponsiveContainer>
```

---

## 10. 전체 체크리스트 (최종 검증)

### 기능 체크리스트

| 항목 | Phase | 완료 기준 |
|---|---|---|
| Vite + React 프로젝트 기동 | Phase 1 | `npm run dev` -> localhost:5173 접근 가능 |
| Layout (사이드바 + 헤더 + 라우팅) | Phase 1 | 페이지 이동 동작, 현재 페이지 강조 |
| API client (fetch wrapper + mock 전환) | Phase 1 | `VITE_USE_MOCK` 환경 변수로 전환 |
| Dashboard (mock data) | Phase 2 | 4개 카드 + 차트 + 필터 동작 |
| TierBadge (High/Mid/Low) | Phase 2 | 3색 뱃지 정상 표시 |
| DemandChart (BarChart) | Phase 2 | 4개 분야 막대 + 폐강 기준선 |
| Simulator (폼 + 검증 + 결과) | Phase 2 | 3개 API 결과 패널 표시 |
| AlertPanel | Phase 2 | Low 등급 경고 표시 |
| 로딩/에러/빈 상태 처리 | Phase 2-3 | 모든 페이지에서 3가지 상태 처리 |
| Dashboard -> 실제 API 연결 | Phase 3 | XGBoost 예측 결과 차트 렌더링 |
| Simulator -> 실제 API 연결 | Phase 3 | 3개 API 순차 호출 + 결과 표시 |
| 반응형 레이아웃 | Phase 3 | 모바일/태블릿/데스크탑 대응 |
| Dockerfile (multi-stage) | Phase 4 | 빌드 성공, 이미지 < 50MB |
| nginx SPA fallback + API proxy | Phase 4 | /simulator 직접 접근 가능, API 프록시 동작 |
| docker-compose 통합 | Phase 4 | 3개 서비스 정상 기동 |

### 파일 최종 목록

```
frontend/
├── Dockerfile
├── nginx.conf
├── package.json
├── package-lock.json
├── vite.config.js
├── index.html
├── .env.development              # VITE_USE_MOCK=true
├── .env.development.local        # VITE_USE_MOCK=false (git 미추적)
├── public/
│   └── favicon.svg
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── App.module.css
    ├── index.css
    ├── api/
    │   ├── client.js              # fetch wrapper (mock/real 전환)
    │   └── mockData.js            # 4개 API mock 데이터
    ├── hooks/
    │   ├── useApi.js              # 범용 API hook
    │   └── useDemand.js           # 수요 예측 전용 hook (선택)
    ├── pages/
    │   ├── Dashboard.jsx
    │   ├── Dashboard.module.css
    │   ├── Simulator.jsx
    │   └── Simulator.module.css
    └── components/
        ├── Layout.jsx
        ├── Layout.module.css
        ├── DemandChart.jsx
        ├── DemandChart.module.css
        ├── TierBadge.jsx
        ├── TierBadge.module.css
        ├── AlertPanel.jsx
        ├── AlertPanel.module.css
        ├── LoadingSpinner.jsx
        ├── ErrorMessage.jsx
        └── EmptyState.jsx
```

---

## 부록: Person A와의 협업 포인트

| 시점 | Person A가 제공해야 할 것 | Person B가 확인할 것 |
|---|---|---|
| **Day 2** | `api/schemas/` Pydantic 스키마 확정 | mock 데이터 구조가 스키마와 일치하는지 |
| **Day 5** | API 서버 localhost:8000 기동 가능 상태 | Vite proxy로 /api 호출 성공 |
| **Day 6** | `POST /api/v1/demand/predict` 동작 | Dashboard 실제 API 연결 |
| **Day 7** | schedule, marketing API 동작 | Simulator 3개 API 연결 |
| **Day 9** | `docker-compose.yml`에 frontend 서비스 포함 | docker-compose 전체 기동 |
| **Day 10** | 최종 API 안정성 | E2E 흐름 통과 |

---

> **이 계획서는 Person B가 독립적으로 작업할 수 있도록 mock 데이터 전략과 mock/real 전환 메커니즘을 포함하고 있다. Person A의 API가 준비되기 전까지 mock 모드로 UI를 완성하고, Day 6부터 실제 API로 전환하는 흐름을 따른다.**
