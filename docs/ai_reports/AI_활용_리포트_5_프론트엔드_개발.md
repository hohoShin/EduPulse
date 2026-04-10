# AI 활용 리포트 5 — 프론트엔드 대시보드 개발 과정

> **작성일:** 2026-04-10
> **사용 도구:** Claude Code (Claude Opus 4.6) + oh-my-claudecode (Ralph, Team, Autopilot)
> **목적:** React 대시보드 5페이지 구현 및 UX 고도화 과정에서의 AI 멀티에이전트 활용 기록

---

## 1. 배경

EduPulse는 AI 기반 수강 수요 예측 솔루션이다. 백엔드(FastAPI) API 서버와 예측 모델(XGBoost, Prophet, LSTM) 구현이 완료된 상태에서 프론트엔드 대시보드 개발에 착수했다.

**기술 스택:**

| 항목 | 선택 |
|------|------|
| UI 라이브러리 | React 18.3 |
| 라우팅 | React Router 7 |
| 차트 | Recharts 3.8 |
| 빌드 도구 | Vite 8 |
| 스타일링 | CSS custom properties (`--color-*`, `--space-*`, `--radius-*`) |

Tailwind CSS는 사용하지 않았다. CSS custom properties를 직접 정의하여 일관된 디자인 토큰 체계를 구성했다.

**구현 대상 5개 페이지:**

| 페이지 | 경로 | 역할 |
|--------|------|------|
| Dashboard | `/` | 메인 수요 예측 대시보드 |
| Simulator | `/simulator` | 신규 강좌 수요 시뮬레이터 |
| Marketing | `/marketing` | 마케팅 타이밍 분석 |
| Operations | `/operations` | 운영 관리 (폐강 위험, 강사 배정) |
| Market | `/market` | 시장 분석 (인구통계, 경쟁사, 최적 개강일) |

---

## 2. 아키텍처 설계 — Adapter 패턴

### 2.1 설계 동기

백엔드 API와 프론트엔드를 병렬로 개발해야 했다. AI(Planner + Architect)가 Mock/Hybrid/Real 3단계 전환이 가능한 Adapter 패턴을 설계했다.

### 2.2 구조

```
frontend/src/api/
├── adapters/
│   ├── index.js          # Adapter 선택기 (VITE_ADAPTER 환경변수)
│   ├── mockAdapter.js    # Fixture 데이터 반환 (백엔드 불필요)
│   ├── realAdapter.js    # 실제 API 호출
│   └── hybridAdapter.js  # Mock + Real 선택적 혼합
├── client.js             # HTTP 클라이언트
├── errors.js             # 에러 타입 정의
├── transformers.js       # API 응답 변환
├── types.js              # 타입 정의
└── viewModels.js         # 뷰모델 변환
```

### 2.3 전환 메커니즘

```javascript
// adapters/index.js
const ACTIVE_ADAPTER = import.meta.env.VITE_ADAPTER || 'mock';

function getAdapter() {
  if (ACTIVE_ADAPTER === 'real') return realAdapter;
  if (ACTIVE_ADAPTER === 'hybrid') return hybridAdapter;
  return mockAdapter;
}
```

환경변수 `VITE_ADAPTER`를 `mock`, `real`, `hybrid` 중 하나로 설정하면 코드 수정 없이 데이터 소스가 전환된다. 페이지와 컴포넌트는 `adapters/index.js`만 import하므로 어댑터 구현에 대한 직접 의존이 없다.

Adapter는 12개 비동기 함수를 제공한다: `getDashboardSummary`, `getDemandChart`, `getDashboardAlerts` (Dashboard), `simulateDemand` (Simulator), `getLeadConversion`, `getMarketingTiming` (Marketing), `getClosureRisk`, `getScheduleSuggest` (Operations), `getDemographics`, `getCompetitors`, `getOptimalStart` (Market), `getSystemStatus` (공통).

이 설계로 백엔드 API가 준비되지 않은 상태에서도 Mock adapter로 프론트엔드 전체를 개발할 수 있었으며, 백엔드 완성 후 환경변수 하나만 변경하여 실 API로 전환했다.

---

## 3. Phase A — Mock 데이터 기반 5페이지 구현

### 3.1 워크플로우

Team 워크플로우를 사용하여 복수 에이전트가 TaskList를 공유하며 병렬 구현을 수행했다. 각 Phase 완료 시 Handoff 문서를 작성하여 다음 Phase로 인수인계했다.

### 3.2 구현 결과

**공통 컴포넌트 7개:** `Layout`(레이아웃+네비게이션), `FieldSelector`(분야 선택기), `StatusPanel`(상태 표시), `TierBadge`(수요 등급), `RiskGauge`(위험도 게이지), `ScoreBar`(점수 막대), `AlertPanel`(알림 패널), `DemandChart`(수요 차트)

**Fixture 데이터 6개:** 페이지별 `dashboardStates.js`, `simulatorStates.js`, `marketingStates.js`, `operationsStates.js`, `marketStates.js` + 공통 `systemStatusStates.js`

### 3.3 문제 발생 및 해결

**Scope creep 문제:**

Task 1 실행 중 Executor가 프론트엔드 범위를 넘어 백엔드 파일까지 수정하는 문제가 발생했다. Verifier가 `git diff`에서 범위 초과를 탐지하여 `git restore`로 백엔드 파일을 복원했다.

```
[Executor] ── Task 1 구현 (프론트엔드 + 백엔드 파일 수정)
    ↓
[Verifier] ── 범위 초과 탐지 → git restore로 백엔드 복원
```

이 사례는 멀티에이전트 워크플로우에서 Verifier의 범위 검증 역할이 실질적으로 작동한 예시이다.

**React 버전 문제:**

Vite 8이 React 19를 자동 선택하는 문제가 발생했다. Task spec에서 React 18을 명시적으로 요구하여 `package.json`에 `"react": "^18.3.1"`로 고정하고 다운그레이드를 수행했다.

---

## 4. Phase B — 백엔드 연동

Mock adapter에서 Real adapter로 전환하는 단계이다.

### 4.1 주요 작업

1. `realAdapter.js`에서 `client.js`를 통해 FastAPI 엔드포인트 12개와 연결
2. API 응답을 `transformers.js`에서 프론트엔드 뷰모델로 변환
3. `errors.js`에 에러 타입을 정의하고 모든 페이지에 통일된 에러 핸들링 적용

### 4.2 Adapter 패턴의 효과

Mock adapter에서 개발한 페이지 코드를 **한 줄도 수정하지 않고** Real adapter로 전환할 수 있었다. `VITE_ADAPTER=real`로 환경변수만 변경하면 동일한 페이지가 실제 API 데이터를 표시한다.

---

## 5. Phase C — UX 고도화 (18항목 + 공통 3항목)

AI(Planner)가 5개 페이지를 분석하여 18개 페이지별 개선사항과 3개 공통 개선사항을 도출했다.

### 5.1 Dashboard 개선

| 항목 | 내용 |
|------|------|
| 분야 필터 | FieldSelector로 분야별 데이터 필터링 추가 |
| 신뢰구간 시각화 | Recharts Area 차트로 예측 신뢰구간 표시 |

### 5.2 Simulator 개선

| 항목 | 내용 |
|------|------|
| 시나리오 비교 | baseline / optimistic / pessimistic 3종 동시 표시 |
| 수강료 입력 | 수강료 파라미터를 시뮬레이션 입력에 추가 |

### 5.3 Marketing 개선

| 항목 | 내용 |
|------|------|
| 전환율 변화율 | 전환율의 전주 대비 변화율 표시 |
| 목표선 | Recharts `ReferenceLine`으로 목표 전환율 시각화 |
| 수요등급별 카드 강조 | 수요 등급(High/Mid/Low)에 따라 카드 배경색 차등 적용 |

### 5.4 Operations 개선

| 항목 | 내용 |
|------|------|
| 위험도 추세 미니차트 | 폐강 위험도의 시계열 추세를 소형 차트로 표시 |
| 배정 편집 | 강사 배정 결과를 직접 수정 가능 |
| 폐강-마케팅 연계 | 폐강 위험 강좌에 대한 마케팅 페이지 바로가기 |

### 5.5 Market 개선

| 항목 | 내용 |
|------|------|
| 파이차트 범례 | 인구통계 파이차트에 범례 추가 |
| 경쟁사 증감 | 경쟁사 지표의 증감 방향 표시 |
| 최적 개강일 날짜 범위 | 단일 날짜 대신 날짜 범위로 추천 |
| 포화도 게이지 | 시장 포화도를 RiskGauge 컴포넌트로 시각화 |

### 5.6 공통 개선 (3항목)

| 항목 | 내용 |
|------|------|
| 페이지간 네비게이션 | 관련 페이지로의 바로가기 링크 추가 |
| 에러 핸들링 통일 | StatusPanel 컴포넌트로 에러 표시 방식 통일 |
| 새로고침 버튼 | 각 페이지에 데이터 수동 새로고침 기능 추가 |

---

## 6. 한글화 및 최종 정리

### 6.1 Ralph 루프를 활용한 한글화

Ralph(자기참조 실행 루프)로 전체 UI 문자열을 한글화했다. 한글화 원칙은 다음과 같다.

**내부 상태값은 영문 유지, UI 표시만 한국어로 매핑:**

```javascript
// 내부 값은 그대로 유지
{ field: "coding", tier: "high", status: "success" }

// UI 표시만 한국어
const FIELD_LABELS = {
  coding: "코딩",
  security: "보안",
  game: "게임",
  art: "아트"
};
```

Fixture 파일의 문자열도 한글화 대상에 포함했다. `systemStatusStates.js` 등의 상태 메시지를 모두 한국어로 변환했다.

### 6.2 Lint 수정

한글화 작업 후 `npm run lint`를 실행하여 발생한 에러 7건을 수정했다.

| 에러 유형 | 건수 |
|----------|------|
| unused imports | 4 |
| unused params | 3 |

Ralph 루프가 한글화 → lint 실행 → 에러 수정 → 재검증을 반복하여 자동으로 완료했다.

---

## 7. Docker 빌드

Multi-stage 빌드를 적용했다. Stage 1(node:22-alpine)에서 Vite 빌드를 수행하고, Stage 2(nginx:alpine)에서 정적 파일만 서빙한다. 최종 이미지에 Node.js 런타임이 포함되지 않아 이미지 크기가 최소화된다.

```dockerfile
# Stage 1: Build — Vite로 정적 파일 생성
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=""
ARG VITE_ADAPTER="api"
RUN npm run build

# Stage 2: Serve — nginx로 정적 파일만 서빙
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

nginx 설정에서 `try_files $uri $uri/ /index.html`로 SPA fallback을 적용하여 React Router가 클라이언트 사이드에서 라우팅을 처리한다. `/assets/` 경로에는 1년 캐시를 설정했다.

---

## 8. AI 활용 효과 분석

### 8.1 활용 방식별 효과

| 활용 방식 | 효과 |
|----------|------|
| Adapter 패턴 설계 (Architect) | 백엔드/프론트엔드 병렬 개발 가능, 데모 환경 즉시 제공 |
| Team 워크플로우 | 복수 에이전트가 페이지별 병렬 구현 — 5페이지 동시 작업 |
| Scope creep 탐지 (Verifier) | Task 범위 초과를 자동 탐지하여 백엔드 오염 방지 |
| UX 개선 도출 (Planner) | 18+3개 구체적 개선사항을 fixture 수준까지 설계 |
| Ralph 루프 | 한글화 + lint 수정을 반복 검증하며 자동 완료 |
| Docker 빌드 자동화 | multi-stage 빌드 + nginx 설정을 한 번에 생성 |

### 8.2 Phase별 에이전트 투입

| Phase | 에이전트 | 역할 |
|-------|----------|------|
| A — Mock 구현 | Planner, Architect, Team, Verifier | 설계 + 병렬 구현 + 범위 검증 |
| B — 백엔드 연동 | Executor, Verifier | Real adapter 구현 + API 정합성 검증 |
| C — UX 고도화 | Planner, Team | 개선사항 도출 + 병렬 구현 |
| D — 한글화 + Docker | Ralph, Autopilot | 반복 루프 한글화 + Docker 자동 생성 |

Adapter 패턴으로 프론트엔드(Mock)와 백엔드를 독립 개발한 후, 환경변수 변경만으로 Real API에 전환했다.

---

## 9. 한계점

### 9.1 Mock 데이터 의존

Fixture 데이터가 실제 API 응답과 구조적으로 다를 수 있다. Mock adapter에서 정상 동작하더라도 Real adapter 전환 시 필드 누락이나 타입 불일치가 발생할 가능성이 있다. `transformers.js`에서 API 응답을 뷰모델로 변환하는 레이어가 이 간극을 완화하지만, 완전히 해소하지는 못한다.

### 9.2 CSS custom properties 관리 복잡성

Tailwind 같은 유틸리티 프레임워크 없이 CSS custom properties를 직접 관리하므로, 대규모 테마 변경이나 다크 모드 추가 시 변수 관리가 복잡해진다. 현재 규모(5페이지, 7컴포넌트)에서는 문제없으나, 페이지 수가 증가하면 디자인 토큰 시스템의 체계화가 필요하다.

### 9.3 접근성(a11y) 미완

기본 수준의 시맨틱 HTML만 적용되어 있다. WCAG 2.1 AA 기준을 충족하지 못하며, 특히 다음 항목의 보완이 필요하다:

- 차트 컴포넌트의 스크린 리더 대응
- 키보드 네비게이션 지원
- 색상 대비 비율 검증

---

## 10. 변경 파일 목록

| Phase | 생성 | 수정 | 주요 파일 |
|-------|------|------|----------|
| A — Mock 구현 | 24 | 0 | 설정 3 + 진입점 3 + 페이지 5 + 컴포넌트 8 + fixture 6 + adapter 2 |
| B — 백엔드 연동 | 6 | 0 | API 레이어 5(`client`, `errors`, `transformers`, `types`, `viewModels`) + `realAdapter` |
| C — UX 고도화 | 1 | 12 | 페이지 5 + 컴포넌트 7 + `hybridAdapter` (신규) |
| D — 한글화 + Docker | 2 | 13 | 페이지 5 + fixture 6 + 컴포넌트 2 + `Dockerfile`(신규) + `nginx.conf`(신규) |

**고유 파일 수:** 31개 (일부 파일은 복수 Phase에 걸쳐 수정됨)
