# EduPulse Frontend 구현 계획서 (v2 — Revised)

> **Plan ID:** edupulse-frontend
> **원본:** edupulse-full-build.md (Person B 파트 분리)
> **생성일:** 2026-04-08
> **수정일:** 2026-04-08 (Backend v2 통합 패키지 구조 반영)
> **상태:** DRAFT
> **담당:** Person B (Frontend / API 통합 / DevOps)
> **전략:** MVP-First — Mock data 선행 → API 연결

---

## 기술 스택

| 항목 | 선택 | 사유 |
|---|---|---|
| 빌드 도구 | **Vite** | CRA 대비 10배 빠른 HMR |
| 프레임워크 | React 18 | CLAUDE.md 명시 |
| 차트 | Recharts | CLAUDE.md 명시, React 친화적 |
| HTTP 클라이언트 | fetch API | 추가 의존성 없음, Vite proxy로 CORS 우회 |
| 패키지 매니저 | npm | 기본 도구 |
| CSS | CSS Modules 또는 Tailwind CSS | MVP 수준 스타일링 |

---

## 일정 (Person B)

```
Week 1
-----------------------------------------------------------------------
Day  | 작업
-----------------------------------------------------------------------
1    | Phase 1: 프로젝트 구조 셋업 (공동)
     | .gitignore, requirements 분리
2    | Phase 1: Vite+React 프로젝트 초기화
     | API client stub, Layout 컴포넌트
-----------------------------------------------------------------------
3    | Phase 2: Dashboard 페이지 (mock data)
     | DemandChart, TierBadge 컴포넌트
4    | Phase 2: Simulator 페이지 (mock data)
     | 폼 입력 → mock 예측 결과 표시
5    | Phase 2: API client 실제 연결 준비
     | 에러 핸들링 UI, 로딩 상태
-----------------------------------------------------------------------

Week 2
-----------------------------------------------------------------------
Day  | 작업
-----------------------------------------------------------------------
6    | Phase 3: Dashboard ↔ API 연결
     | 실제 예측 데이터로 차트 렌더링
7    | Phase 3: Simulator ↔ API 연결
     | AlertPanel 구현
     | *** Day 7: 중간 시연 가능 ***
-----------------------------------------------------------------------
8    | Phase 3: 반응형 레이아웃, UI 다듬기
9    | Phase 4: Frontend Dockerfile
     | nginx 설정
10   | Phase 4: 통합 테스트, 문서화
     | README 업데이트
-----------------------------------------------------------------------

Day 11-12: 버퍼
```

---

## Phase 1: Foundation — Day 1-2

**목표:** .gitignore, Frontend 프로젝트 초기화, API client stub

### Task 1.1: 공통 인프라 (Day 1)

| 파일 | 설명 |
|---|---|
| `.gitignore` (수정) | Python + Node.js + 프로젝트별 패턴 추가 |

### .gitignore 내용 (v2 — 통합 패키지 경로 반영)

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

# Data (통합 패키지 경로)
edupulse/data/raw/
edupulse/data/processed/
edupulse/data/warehouse/
*.csv
*.parquet

# Model artifacts (통합 패키지 경로)
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

### Task 1.2: Frontend 프로젝트 초기화 (Day 2)

| 파일 | 설명 |
|---|---|
| `frontend/` (Vite 초기화) | `npm create vite@latest frontend -- --template react` |
| `frontend/vite.config.js` | proxy 설정 (localhost:8000) |
| `frontend/src/App.jsx` | React Router 라우팅 |
| `frontend/src/api/client.js` | fetch 기반 API 클라이언트 (스키마 계약 기반) |
| `frontend/src/components/Layout.jsx` | 공통 레이아웃 (사이드바, 헤더) |

### Vite proxy 설정

```js
// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

### Phase 1 수락 기준

```bash
# Frontend 개발 서버 기동
cd frontend && npm install && npm run dev
# 기대: VITE v5.x.x ready in xxx ms — Local: http://localhost:5173/

# Layout 컴포넌트 렌더링 확인
# 브라우저에서 http://localhost:5173 접속
# 기대: 사이드바 + 헤더 레이아웃, 빈 콘텐츠 영역
```

---

## Phase 2: Frontend 컴포넌트 (Mock Data) — Day 3-5

**목표:** Mock data 기반 Dashboard + Simulator 페이지 완성
**선행 조건:** Phase 1 완료, 스키마 계약 확정
**소요:** 3일 (Backend Phase 2 일정과 동기화)

### 개발 전략: Mock → Real

Phase 1에서 확정된 스키마 계약(DemandResponse 등)에 맞는 mock JSON을 작성하여 UI를 먼저 완성. API 연결은 Phase 3에서 수행. `USE_MOCK` 플래그로 mock/real 전환.

### 핵심 스키마 계약 (Backend에서 제공, Frontend에서 소비)

**v2 NOTE:** Backend에서 `DemandTier`는 `edupulse/constants.py`에 정의된 enum.
API 응답의 `demand_tier` 필드는 문자열 `"High"`, `"Mid"`, `"Low"` 중 하나.

```typescript
// 참고용 타입 (실제로는 JS에서 사용)

// POST /api/v1/demand/predict
// Request
interface DemandRequest {
  course_name: string
  start_date: string      // "YYYY-MM-DD"
  field: "coding" | "security" | "game" | "art"
}
// Response
interface DemandResponse {
  course_name: string
  field: string
  predicted_enrollment: number
  demand_tier: "High" | "Mid" | "Low"
  confidence_interval: { lower: number, upper: number }
  model_used: string
  prediction_date: string  // ISO datetime
}

// POST /api/v1/schedule/suggest  [rule-based MVP]
// Request
interface ScheduleRequest {
  course_name: string
  start_date: string
  predicted_enrollment: number
}
// Response
interface ScheduleResponse {
  required_instructors: number
  required_classrooms: number
  assignment_plan: object
}

// POST /api/v1/marketing/timing  [rule-based MVP]
// Request
interface MarketingRequest {
  course_name: string
  start_date: string
  demand_tier: "High" | "Mid" | "Low"
}
// Response
interface MarketingResponse {
  ad_launch_weeks_before: number
  earlybird_duration_days: number
  discount_rate: number
}

// GET /api/v1/health
interface HealthResponse {
  status: string
  models_loaded: string[]
  db_connected: boolean
  memory_usage_mb: number
}
```

### 수요 등급 임계값 (Backend과 동일 — 단일 소스: edupulse/constants.py)

```javascript
// frontend/src/api/constants.js
// Backend edupulse/constants.py와 동기화 유지
export const DEMAND_THRESHOLDS = { high: 25, mid: 12 }
export const DEMAND_TIERS = {
  HIGH: 'High',   // >= 25명
  MID: 'Mid',     // >= 12명
  LOW: 'Low',     // < 12명
}
```

### Task 2.1: Dashboard 페이지 (Day 3)

| 파일 | 설명 |
|---|---|
| `frontend/src/pages/Dashboard.jsx` | 메인 대시보드 (mock data) |
| `frontend/src/components/DemandChart.jsx` | Recharts 시계열 차트 |
| `frontend/src/components/TierBadge.jsx` | High/Mid/Low 뱃지 |
| `frontend/src/api/mockData.js` | 스키마 계약 기반 mock JSON |
| `frontend/src/api/constants.js` | 수요 등급 상수 |

**DemandChart 요구사항:**
- Recharts `LineChart` 또는 `AreaChart` 사용
- X축: 날짜 (기수별), Y축: 예상 수강 인원
- 수요 등급별 색상 구분 (High: green, Mid: yellow, Low: red)
- confidence interval 영역 표시 (`AreaChart` + `Area` for lower/upper)

**TierBadge 요구사항:**
- High: 초록색 뱃지
- Mid: 노란색 뱃지
- Low: 빨간색 뱃지 + 폐강 리스크 경고

**mockData.js 예시:**

```javascript
// frontend/src/api/mockData.js
export const mockDemandResponses = [
  {
    course_name: "Python 웹개발",
    field: "coding",
    predicted_enrollment: 28,
    demand_tier: "High",
    confidence_interval: { lower: 22, upper: 34 },
    model_used: "xgboost",
    prediction_date: "2026-04-08T10:00:00"
  },
  {
    course_name: "정보보안 실무",
    field: "security",
    predicted_enrollment: 18,
    demand_tier: "Mid",
    confidence_interval: { lower: 13, upper: 23 },
    model_used: "xgboost",
    prediction_date: "2026-04-08T10:00:00"
  },
  {
    course_name: "Unity 게임개발",
    field: "game",
    predicted_enrollment: 8,
    demand_tier: "Low",
    confidence_interval: { lower: 4, upper: 12 },
    model_used: "xgboost",
    prediction_date: "2026-04-08T10:00:00"
  },
  {
    course_name: "디지털 아트",
    field: "art",
    predicted_enrollment: 15,
    demand_tier: "Mid",
    confidence_interval: { lower: 10, upper: 20 },
    model_used: "xgboost",
    prediction_date: "2026-04-08T10:00:00"
  }
]

export const mockScheduleResponse = {
  required_instructors: 2,
  required_classrooms: 1,
  assignment_plan: {}
}

export const mockMarketingResponse = {
  ad_launch_weeks_before: 3,
  earlybird_duration_days: 14,
  discount_rate: 0.10
}
```

### Task 2.2: Simulator 페이지 (Day 4)

| 파일 | 설명 |
|---|---|
| `frontend/src/pages/Simulator.jsx` | 수요 시뮬레이터 (폼 → mock 결과) |
| `frontend/src/components/AlertPanel.jsx` | 폐강 리스크 알림 |

**Simulator 폼 필드:**
- 강좌명 (text input, required)
- 개강 예정일 (date input, required, min=today)
- 분야 선택 (select: coding / security / game / art)
- [예측하기] 버튼

**결과 표시 (3개 API 응답 통합):**
- 예상 수강 인원 (숫자, 크게)
- 수요 등급 (TierBadge)
- 신뢰 구간 (lower ~ upper)
- 권장 강사 수, 강의실 수 (schedule API 결과)
- 마케팅 타이밍 (marketing API 결과)

**Simulator 데이터 흐름:**
```
[폼 입력] → predictDemand()
              ↓ (demand_tier, predicted_enrollment 획득)
         suggestSchedule() + getMarketingTiming() 병렬 호출
              ↓
         [통합 결과 표시]
```

### Task 2.3: API Client + 에러 핸들링 (Day 5)

| 파일 | 설명 |
|---|---|
| `frontend/src/api/client.js` | mock/real 전환 지원, 에러 분류 |

**API Client 구조 (v2 — mock 전환 + 에러 분류):**

```javascript
// frontend/src/api/client.js
import { mockDemandResponses, mockScheduleResponse, mockMarketingResponse } from './mockData'

const API_BASE = '/api/v1'
const USE_MOCK = false  // Phase 2: true, Phase 3: false

class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

async function apiCall(url, body) {
  let res
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(10000)  // 10초 타임아웃
    })
  } catch (err) {
    if (err.name === 'AbortError' || err.name === 'TimeoutError') {
      throw new ApiError(0, '서버 응답 시간이 초과되었습니다')
    }
    throw new ApiError(0, '서버에 연결할 수 없습니다')
  }

  if (!res.ok) {
    if (res.status === 503) throw new ApiError(503, '예측 모델을 로딩 중입니다')
    if (res.status === 422) {
      const detail = await res.json().catch(() => ({}))
      throw new ApiError(422, detail.detail || '입력값을 확인해주세요')
    }
    throw new ApiError(res.status, `API 오류 (${res.status})`)
  }

  return res.json()
}

export async function predictDemand(request) {
  if (USE_MOCK) return mockDemandResponses[0]
  return apiCall(`${API_BASE}/demand/predict`, request)
}

export async function suggestSchedule(request) {
  if (USE_MOCK) return mockScheduleResponse
  return apiCall(`${API_BASE}/schedule/suggest`, request)
}

export async function getMarketingTiming(request) {
  if (USE_MOCK) return mockMarketingResponse
  return apiCall(`${API_BASE}/marketing/timing`, request)
}

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(5000) })
    return res.ok
  } catch {
    return false
  }
}
```

**에러 핸들링 UI 매핑:**

| ApiError.status | UI 표시 |
|---|---|
| 0 (네트워크) | "서버에 연결할 수 없습니다" 배너 |
| 503 | "예측 모델을 로딩 중입니다" + 재시도 버튼 |
| 422 | 폼 필드 옆에 에러 메시지 |
| 기타 | "API 오류가 발생했습니다" 토스트 |
| 로딩 중 | 버튼 비활성화 + 스피너 |

### Phase 2 수락 기준

```bash
# 1. Dashboard 페이지 렌더링
# 브라우저에서 http://localhost:5173 접속
# 기대: DemandChart에 mock 데이터 차트 (4개 강좌), TierBadge 표시

# 2. Simulator 페이지
# 브라우저에서 http://localhost:5173/simulator 접속
# 기대: 폼 입력 → mock 결과 (수강 인원 + 등급 + 강사/강의실 + 마케팅)

# 3. 에러 핸들링 (USE_MOCK=false, API 서버 미기동)
# Simulator에서 예측 시도
# 기대: "서버에 연결할 수 없습니다" 에러 메시지 (빈 화면 아님)

# 4. TierBadge 색상 확인
# Dashboard에서 High(초록), Mid(노란), Low(빨간) 뱃지 표시

# 5. AlertPanel
# Low 등급 mock 데이터 → 폐강 리스크 경고 표시
```

---

## Phase 3: Frontend ↔ API 연결 — Day 6-8

**목표:** Mock data → 실제 API 연결, UI 완성
**선행 조건:** Phase 2 (Frontend mock), Backend Phase 3 (API 라우터 완성)

### Task 3.1: Dashboard ↔ API 연결 (Day 6)

| 파일 | 수정 내용 |
|---|---|
| `frontend/src/api/client.js` | `USE_MOCK = false`로 전환 |
| `frontend/src/pages/Dashboard.jsx` | 실제 예측 데이터로 차트 렌더링 |

**Dashboard 데이터 로딩 전략:**
- 페이지 마운트 시 4개 분야 각각 `predictDemand()` 호출 (병렬)
- 로딩 중: 스켈레톤 UI
- 에러 시: 에러 배너 + 재시도 버튼
- 성공 시: DemandChart + TierBadge 렌더링

### Task 3.2: Simulator ↔ API 연결 (Day 7)

| 파일 | 수정 내용 |
|---|---|
| `frontend/src/pages/Simulator.jsx` | 폼 submit → API 호출 → 결과 표시 |
| `frontend/src/components/AlertPanel.jsx` | 폐강 리스크 강좌 표시 (Low 등급) |

**Simulator API 호출 순서 (체이닝):**
```
1. predictDemand({ course_name, start_date, field })
   → DemandResponse 획득

2. 병렬 호출:
   suggestSchedule({ course_name, start_date, predicted_enrollment })
   getMarketingTiming({ course_name, start_date, demand_tier })

3. 모든 결과 통합하여 UI 렌더링
```

**AlertPanel 요구사항:**
- Low 등급 강좌 목록 자동 표시
- "폐강 리스크" 경고 아이콘 + 빨간 배경
- 권장 조치: 마케팅 강화, 할인율 적용 등 (marketing API 결과 기반)

### Task 3.3: UI 다듬기 (Day 8)

- 반응형 레이아웃 (모바일/태블릿/데스크톱)
- 로딩 상태 스켈레톤 UI
- 차트 애니메이션
- 폼 validation 강화 (빈 값, 과거 날짜 방지)

### Phase 3 수락 기준

```bash
# 1. Dashboard 실데이터
# 브라우저에서 http://localhost:5173 접속 (Backend API 서버 기동 상태)
# 기대: DemandChart에 실제 예측 데이터 렌더링, TierBadge 표시

# 2. Simulator 실제 API 연결
# Simulator 페이지에서 폼 입력 → 예측하기
# 기대: 수강 인원 + 등급 + 강사/강의실 + 마케팅 타이밍 모두 실데이터

# 3. AlertPanel
# Low 등급 강좌가 존재할 때
# 기대: 폐강 리스크 알림 + 권장 마케팅 타이밍 표시

# 4. 에러 핸들링 (API 서버 중지 후 접속)
# 기대: "서버에 연결할 수 없습니다" 에러 메시지 (빈 화면 아님)

# 5. 503 에러 핸들링 (모델 미로딩)
# 기대: "예측 모델을 로딩 중입니다" + 재시도 버튼

# 6. 반응형 확인
# 브라우저 개발자 도구에서 모바일 뷰 (375px)
# 기대: 레이아웃 깨짐 없음, 차트 축소 정상
```

---

## Phase 4: Docker + 문서화 — Day 9-10

**목표:** Frontend Dockerfile, nginx 설정, 문서화
**선행 조건:** Phase 3 완료

### Task 4.1: Frontend Dockerfile (Day 9)

| 파일 | 설명 |
|---|---|
| `frontend/Dockerfile` | Frontend 빌드 (node:20-alpine → nginx) |
| `frontend/nginx.conf` | SPA fallback, API proxy |

**Frontend Dockerfile:**

```dockerfile
# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf (v2 — API proxy + SPA fallback):**

```nginx
server {
    listen 3000;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # API proxy — Backend 서비스명 'api' 사용 (Docker 네트워크)
    location /api/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SPA fallback — 모든 경로를 index.html로
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**docker-compose.yml 내 Frontend 서비스 (Backend 계획과 동기화):**

```yaml
# docker-compose.yml (frontend 부분)
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api
```

### Task 4.2: 문서화 (Day 10)

| 파일 | 설명 |
|---|---|
| `README.md` (수정) | S3 참조 제거, scp 전송으로 통일, 실행 방법 업데이트 |

**README 업데이트 항목:**
- 실행 방법: `uvicorn edupulse.api.main:app` (통합 패키지 경로)
- Frontend 개발: `cd frontend && npm run dev`
- Docker: `docker-compose up --build`
- S3 참조 → scp 전송으로 변경
- 환경 변수 설명 (.env.example 참조)

### Phase 4 수락 기준

```bash
# 1. Docker Frontend 접근
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# 기대: 200

# 2. SPA 라우팅
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/simulator
# 기대: 200 (nginx SPA fallback)

# 3. API proxy (Docker 내부)
curl -s http://localhost:3000/api/v1/health
# 기대: {"status":"ok","models_loaded":["xgboost"],"db_connected":true}

# 4. README S3 참조 없음
grep -i "s3" README.md
# 기대: 결과 없음

# 5. 실행 방법 정확성
grep "edupulse.api.main" README.md
# 기대: uvicorn edupulse.api.main:app 포함
```

---

## 디렉토리 구조

```
frontend/
├── package.json
├── vite.config.js
├── index.html
├── Dockerfile
├── nginx.conf
├── src/
│   ├── App.jsx
│   ├── main.jsx
│   ├── api/
│   │   ├── client.js          # fetch 기반 API 클라이언트 (mock/real 전환)
│   │   ├── mockData.js        # 개발용 mock 데이터
│   │   └── constants.js       # DEMAND_TIERS, DEMAND_THRESHOLDS
│   ├── pages/
│   │   ├── Dashboard.jsx      # MVP 핵심 페이지
│   │   └── Simulator.jsx      # 수요 시뮬레이션
│   └── components/
│       ├── Layout.jsx         # 사이드바 + 헤더
│       ├── DemandChart.jsx    # Recharts 시계열 차트
│       ├── TierBadge.jsx      # High/Mid/Low 뱃지
│       └── AlertPanel.jsx     # 폐강 리스크 알림
└── public/
```

---

## 리스크 및 완화

| 리스크 | 완화 전략 |
|---|---|
| Frontend-Backend 스키마 불일치 | Phase 1 스키마 계약 + OpenAPI spec 자동 생성 (/docs) |
| API 응답 지연으로 UX 저하 | 10초 타임아웃 + 스켈레톤 UI + 재시도 버튼 |
| 차트 렌더링 성능 | Recharts memo 최적화, 데이터 포인트 제한 |
| 반응형 레이아웃 깨짐 | 모바일-first 접근, CSS flexbox/grid |
| Docker nginx ↔ API 연결 실패 | nginx proxy_pass에서 서비스명 `api` 사용 (localhost 아님) |
| DEMAND_THRESHOLDS 불일치 | `constants.js`에 주석으로 Backend 소스 명시, 변경 시 동기화 |

---

## 의존성 (Backend와의 연결점)

| Phase | Backend 의존 | 설명 |
|---|---|---|
| Phase 1 | 스키마 계약 확정 | `edupulse/api/schemas/*.py`의 request/response 형태 |
| Phase 1 | 상수 동기화 | `edupulse/constants.py` → `frontend/src/api/constants.js` |
| Phase 2 | 없음 (mock data) | 독립 작업 가능 |
| Phase 3 | API 라우터 완성 | `POST /api/v1/demand/predict` 등 실제 동작 필요 |
| Phase 4 | docker-compose.yml | Backend `api` 서비스명, `db` 서비스명 |

---

## v2 변경사항 요약

| # | 변경 내용 |
|---|---|
| 1 | .gitignore 경로를 통합 패키지(`edupulse/data/`, `edupulse/model/saved/`)로 수정 |
| 2 | Alembic 디렉토리 `.gitignore`에 추가 |
| 3 | 스키마 계약에 Request 타입 추가 (DemandRequest, ScheduleRequest, MarketingRequest) |
| 4 | HealthResponse 타입 추가 |
| 5 | Schedule/Marketing API에 `[rule-based MVP]` 명시 |
| 6 | `constants.js` 파일 추가 — Backend `edupulse/constants.py`와 동기화 |
| 7 | `mockData.js` 전체 예시 코드 추가 (4개 분야 mock) |
| 8 | API client에 `USE_MOCK` 플래그 + `ApiError` 클래스 + 타임아웃 추가 |
| 9 | 에러 핸들링 UI 매핑 테이블 추가 (status별 표시 내용) |
| 10 | Simulator 데이터 흐름 명시 (demand → schedule + marketing 체이닝) |
| 11 | nginx.conf 전체 예시 추가 (API proxy `http://api:8000` + SPA fallback) |
| 12 | docker-compose.yml Frontend 서비스 설정 추가 |
| 13 | 의존성 테이블에 `상수 동기화`, `docker-compose 서비스명` 추가 |
| 14 | README 업데이트 항목에 통합 패키지 경로(`edupulse.api.main`) 명시 |
| 15 | Phase 3 수락 기준에 503 에러 핸들링 테스트 추가 |
