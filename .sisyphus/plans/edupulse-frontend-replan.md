# EduPulse Frontend Replan

## TL;DR
> **Summary**: 저장소 현실에 맞춰 EduPulse 프론트엔드를 그린필드로 구축한다. 실제 사용자 가치의 중심은 Simulator의 실 API 연동이며, Dashboard는 백엔드 확장 없이 가능한 고정 샘플 요청 기반 요약 화면으로 제한한다.
> **Deliverables**:
> - Vite + React 기반 `frontend/` 앱 스캐폴드
> - Demand / Schedule / Marketing / Health 연동 API 클라이언트
> - Dashboard, Simulator, 공통 Layout 및 상태 UI
> - Frontend Dockerfile + nginx SPA/proxy 설정
> - 수동 QA 중심 검증 절차와 증적 경로
> **Effort**: Medium
> **Parallel**: YES - 2 waves
> **Critical Path**: 1 → 2 → 4 → 6 → 8

## Context
### Original Request
`docs/ai_plans/edupulse-frontend.md`를 읽고 분석한 뒤, 현재 저장소 상태에 맞는 새 계획으로 재수립.

### Interview Summary
- 범위: **프론트 중심 + API 연동만**
- 백엔드 대규모 수정은 제외, 계약 확인과 소규모 연동 가드레일만 포함
- 검증 전략: **수동 QA 중심**
- 프론트엔드는 현재 저장소에 없으므로 기존 앱 개선이 아니라 **신규 구축**으로 계획

### Metis Review (gaps addressed)
- Dashboard용 실제 집계/시계열 API가 없으므로 “실데이터 차트” 전제를 폐기
- 프론트에서 수요 등급을 재계산하지 않고 백엔드 `demand_tier`를 그대로 사용하도록 결정
- `assignment_plan`을 구조화된 보드 데이터로 가정하지 않도록 제한
- 422/503/네트워크 오류, 비정상 health 상태, 빈 `models_loaded`를 명시적으로 검증 범위에 포함

## Work Objectives
### Core Objective
현재 FastAPI 계약에 맞는 EduPulse MVP 프론트엔드를 새로 구축해, 사용자가 브라우저에서 수요 예측 시뮬레이션과 운영/마케팅 추천 결과를 확인할 수 있게 한다.

### Deliverables
- `frontend/` Vite React 앱
- `Dashboard`, `Simulator`, `Layout`, `TierBadge`, `DemandChart`, `AlertPanel`
- `frontend/src/api/client.js`, `mockData.js`, `sampleRequests.js`
- `frontend/Dockerfile`, `frontend/nginx.conf`
- README 실행/배포 절차 업데이트

### Definition of Done (verifiable conditions with commands)
- `cd frontend && npm install && npm run dev` 실행 시 개발 서버가 정상 기동한다.
- `cd frontend && npm run build`가 성공한다.
- 백엔드 실행 상태에서 Simulator가 `POST /api/v1/demand/predict`, `POST /api/v1/schedule/suggest`, `POST /api/v1/marketing/timing`을 순서대로 사용해 결과를 렌더링한다.
- `docker compose up --build` 후 `http://localhost:3000` 및 `/simulator`가 응답한다.
- 오류 상태(오프라인/422/503/health 저하)가 빈 화면 없이 처리된다.

### Must Have
- React 18 + Vite 기반 구조
- 라우팅: `/` Dashboard, `/simulator` Simulator
- API 경로는 상대 경로 `/api/v1` 사용
- 개발은 Vite proxy, Docker는 nginx proxy 사용
- Dashboard는 고정 샘플 요청 기반 결과 요약 화면
- Simulator는 실제 핵심 API 체인을 수행
- 수동 QA 시나리오와 증적 경로 명시

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- 신규 백엔드 엔드포인트 추가 금지
- 프론트에서 수요 등급 임계값 하드코딩 후 재판정 금지
- `assignment_plan`을 표/보드 구조로 가정한 UI 금지
- Reports/analytics/scheduling board 같은 범위 외 화면 추가 금지
- 프론트 테스트 프레임워크(Vitest/Jest/Playwright) 도입을 기본 범위에 포함하지 않음

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: none (frontend test infra 미도입) + 수동 QA/명령 기반 검증
- QA policy: Every task has agent-executed scenarios
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks for max parallelism.

Wave 1: foundation + contracts + local runtime (Tasks 1-4)
Wave 2: feature assembly + packaging + docs (Tasks 5-8)

### Dependency Matrix (full, all tasks)
- 1 blocks 2, 3, 4, 5, 6, 7, 8
- 2 blocks 5, 6
- 3 blocks 5, 6
- 4 blocks 5, 6
- 5 blocks 6
- 6 blocks 7, 8
- 7 blocks final verification
- 8 blocks final verification

### Agent Dispatch Summary (wave → task count → categories)
- Wave 1 → 4 tasks → quick / writing / visual-engineering
- Wave 2 → 4 tasks → visual-engineering / quick / writing

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [ ] 1. Bootstrap greenfield frontend workspace

  **What to do**: Create the missing `frontend/` application with Vite + React 18, install runtime dependencies needed by the approved scope (`react-router-dom`, `recharts`), add base scripts in `package.json`, wire `src/main.jsx` and `src/App.jsx`, and ensure the initial render path is stable. Reuse existing root `.gitignore` frontend entries instead of reworking root ignore rules.
  **Must NOT do**: Do not add TypeScript, state libraries, Tailwind, ESLint/Prettier overhauls, or frontend test frameworks.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: predictable scaffold creation with low architectural risk
  - Skills: [] - scaffolding is straightforward
  - Omitted: [`frontend-ui-ux`] - visual design is not the core concern yet

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [2, 3, 4, 5, 6, 7, 8] | Blocked By: []

  **References**:
  - Pattern: `docs/ai_plans/edupulse-frontend.md:142` - approved Vite/React initialization direction
  - Pattern: `README.md` - existing project run-command style to align docs later
  - Pattern: `docker-compose.yml` - existing placeholder frontend service to wire against later

  **Acceptance Criteria**:
  - [ ] `frontend/package.json` exists with `dev`, `build`, and `preview` scripts.
  - [ ] `frontend/src/main.jsx` mounts the app without runtime errors.
  - [ ] `cd frontend && npm install && npm run build` succeeds.

  **QA Scenarios**:
  ```
  Scenario: Fresh scaffold build
    Tool: Bash
    Steps: Run `npm install` and `npm run build` in `frontend/`
    Expected: Install completes and Vite build outputs `dist/` without errors
    Evidence: .sisyphus/evidence/task-1-bootstrap-build.txt

  Scenario: Missing dependency regression
    Tool: Bash
    Steps: Run `npm run dev -- --host 127.0.0.1 --port 4173`
    Expected: Dev server starts successfully; no immediate module resolution failure
    Evidence: .sisyphus/evidence/task-1-bootstrap-dev.txt
  ```

  **Commit**: YES | Message: `feat(frontend): scaffold vite react app` | Files: [`frontend/**`]

- [ ] 2. Freeze API client contracts and runtime config

  **What to do**: Implement `frontend/src/api/client.js` around the live FastAPI contract using relative base path `/api/v1`. Add helpers for `predictDemand`, `suggestSchedule`, `getMarketingTiming`, and `checkHealth`. Normalize error handling so network errors, 422 validation payloads, and 503 model-loading responses map to stable frontend error objects. Keep `USE_MOCK` or equivalent environment-controlled switch for local mock mode, but structure the code so Simulator and Dashboard can share the same client.
  **Must NOT do**: Do not re-derive `demand_tier` from thresholds; do not assume 422 `detail` is always a string; do not hardcode absolute backend URLs.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: contract translation work with limited surface area
  - Skills: [] - existing backend contract is already known
  - Omitted: [`git-master`] - no git task required during implementation

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [5, 6] | Blocked By: [1]

  **References**:
  - API/Type: `edupulse/api/schemas/demand.py` - request/response fields for prediction
  - API/Type: `edupulse/api/schemas/schedule.py` - schedule contract including nullable assignment plan
  - API/Type: `edupulse/api/schemas/marketing.py` - marketing request/response fields
  - Pattern: `edupulse/api/routers/demand.py` - status/error behavior for prediction endpoint
  - Pattern: `edupulse/api/routers/health.py` - health response shape
  - Pattern: `edupulse/constants.py` - source of tier labels; do not duplicate thresholds in UI logic

  **Acceptance Criteria**:
  - [ ] API helper functions exist for all four live endpoints.
  - [ ] Error normalization supports offline, 422, 503, and unknown failures.
  - [ ] Mock mode and real mode can be toggled without code duplication in consumers.

  **QA Scenarios**:
  ```
  Scenario: Real-mode health check
    Tool: Bash
    Steps: Start backend, then exercise the health helper via the app flow or a lightweight page load that calls `/api/v1/health`
    Expected: Health status is surfaced without crashing even when `models_loaded` is empty
    Evidence: .sisyphus/evidence/task-2-health-check.txt

  Scenario: API offline handling
    Tool: interactive_bash
    Steps: Stop backend, open the frontend flow that triggers API access, and observe the first failing call
    Expected: UI receives normalized network error state; no unhandled promise rejection or blank screen
    Evidence: .sisyphus/evidence/task-2-offline.txt
  ```

  **Commit**: YES | Message: `feat(frontend): add api client and error normalization` | Files: [`frontend/src/api/client.js`, `frontend/src/api/*`]

- [ ] 3. Add shared shell, routing, and state surfaces

  **What to do**: Implement `Layout` and route structure for `/` and `/simulator`, including top-level status regions for loading/error banners. Provide a simple navigation model and page containers that both support success, loading, and failure states consistently.
  **Must NOT do**: Do not build extra pages from CLAUDE.md placeholders (`Reports`, `ScheduleBoard`); do not over-design the layout or introduce a global store.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: UI shell and route ergonomics matter here
  - Skills: [] - base React patterns are sufficient
  - Omitted: [`frontend-ui-ux`] - not necessary unless styling quality becomes a separate requirement

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [5, 6] | Blocked By: [1]

  **References**:
  - Pattern: `docs/ai_plans/edupulse-frontend.md:148` - planned route/layout responsibilities
  - Pattern: `edupulse/api/middleware.py` - allowed dev origins imply Vite on 5173 and nginx-served frontend on 3000

  **Acceptance Criteria**:
  - [ ] Root route and simulator route are reachable.
  - [ ] Shared layout renders persistent navigation/header plus page content outlet.
  - [ ] Global page-level error/loading surfaces are available for both routes.

  **QA Scenarios**:
  ```
  Scenario: Route navigation
    Tool: Playwright
    Steps: Open `/`, navigate to `/simulator`, then back to `/`
    Expected: Navigation works with no full page reload failure and layout remains mounted
    Evidence: .sisyphus/evidence/task-3-routing.png

  Scenario: Unknown route fallback
    Tool: Playwright
    Steps: Open an invalid route such as `/unknown`
    Expected: App shows a controlled fallback/redirect, not a raw error screen
    Evidence: .sisyphus/evidence/task-3-404.png
  ```

  **Commit**: YES | Message: `feat(frontend): add layout and routing shell` | Files: [`frontend/src/App.jsx`, `frontend/src/components/Layout.jsx`, `frontend/src/pages/*`]

- [ ] 4. Seed mock data and fixed dashboard sample requests

  **What to do**: Add `mockData.js` for local mock rendering and a separate `sampleRequests.js` (or equivalent) that defines the exact fixed demand prediction requests the Dashboard will use in real mode. Choose a stable set of sample courses spanning the four supported fields (`coding`, `security`, `game`, `art`) and document them in code comments so implementers do not invent requests later.
  **Must NOT do**: Do not imply these are historical datasets; do not claim true trend analytics; do not hardcode incorrect 25/12 thresholds anywhere.

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: careful contract-consistent fixture/sample authoring
  - Skills: [] - no extra skill needed
  - Omitted: [`frontend-ui-ux`] - this is data definition, not presentation

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [5] | Blocked By: [1]

  **References**:
  - API/Type: `edupulse/api/schemas/demand.py` - valid sample request shape including optional `model_name`
  - Pattern: `docs/ai_plans/edupulse-frontend.md:290` - prior mock dataset concept to replace with repo-grounded data
  - Pattern: `edupulse/constants.py` - tier names only; backend determines classification

  **Acceptance Criteria**:
  - [ ] Mock fixtures match live schema fields.
  - [ ] Dashboard sample requests are explicitly documented and reusable.
  - [ ] Sample requests avoid unsupported fields or endpoints.

  **QA Scenarios**:
  ```
  Scenario: Mock-mode dashboard render
    Tool: Playwright
    Steps: Start frontend in mock mode and open `/`
    Expected: Dashboard renders all configured sample items without API dependency
    Evidence: .sisyphus/evidence/task-4-dashboard-mock.png

  Scenario: Sample request contract drift
    Tool: Bash
    Steps: Manually compare sample request keys against live FastAPI schema/openapi output
    Expected: No extra or missing required keys in fixed dashboard requests
    Evidence: .sisyphus/evidence/task-4-contract-check.txt
  ```

  **Commit**: YES | Message: `feat(frontend): add mock fixtures and dashboard sample requests` | Files: [`frontend/src/api/mockData.js`, `frontend/src/api/sampleRequests.js`]

- [ ] 5. Implement Dashboard as curated prediction summary

  **What to do**: Build `Dashboard.jsx`, `DemandChart.jsx`, and `TierBadge.jsx` so the page shows curated sample prediction results rather than unsupported historical analytics. In real mode, execute the fixed sample requests defined in Task 4, render returned `predicted_enrollment`, `demand_tier`, and `confidence_interval`, and clearly label the view as a prediction summary. Use backend-returned tier labels directly for badges and risk styling.
  **Must NOT do**: Do not present the chart as historical truth or trend forecasting across stored cohorts; do not calculate badge tier from local thresholds.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: data visualization and conditional styling dominate this task
  - Skills: [] - existing chart library is enough
  - Omitted: [`frontend-ui-ux`] - optional refinement only

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [6] | Blocked By: [1, 2, 3, 4]

  **References**:
  - Pattern: `docs/ai_plans/edupulse-frontend.md:279` - chart/badge component intent
  - API/Type: `edupulse/api/schemas/demand.py` - response data to render
  - Pattern: `edupulse/constants.py` - only for label parity, not client-side classification

  **Acceptance Criteria**:
  - [ ] Dashboard renders in mock mode and real mode.
  - [ ] Each sample item displays enrollment, tier, confidence interval, and model metadata safely.
  - [ ] Float confidence interval values and ISO prediction dates are formatted without UI breakage.

  **QA Scenarios**:
  ```
  Scenario: Real-mode dashboard summary
    Tool: Playwright
    Steps: Start backend and frontend, open `/`, wait for all fixed sample requests to resolve
    Expected: Summary cards/chart render for all configured samples with no blank/error state
    Evidence: .sisyphus/evidence/task-5-dashboard-real.png

  Scenario: Partial API degradation
    Tool: interactive_bash
    Steps: Force one dashboard request path to fail (for example by making backend unavailable mid-load) and reload the page
    Expected: Page shows controlled degraded/error state rather than crashing the entire dashboard
    Evidence: .sisyphus/evidence/task-5-dashboard-error.txt
  ```

  **Commit**: YES | Message: `feat(frontend): add curated dashboard summary` | Files: [`frontend/src/pages/Dashboard.jsx`, `frontend/src/components/DemandChart.jsx`, `frontend/src/components/TierBadge.jsx`]

- [ ] 6. Implement Simulator as the primary real API workflow

  **What to do**: Build `Simulator.jsx` and `AlertPanel.jsx` around the live workflow: submit demand request, then parallelize schedule and marketing calls from the demand result, then render a consolidated output block. Include form validation for required fields and client-side past-date blocking, but treat backend validation as authoritative. Show low-tier risk messaging using the returned `demand_tier` and marketing response; handle nullable `assignment_plan` gracefully.
  **Must NOT do**: Do not assume `assignment_plan` contains nested assignment objects; do not silently swallow 422 or 503 errors; do not require future backend changes.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: interaction flow plus result presentation
  - Skills: [] - standard fetch/form handling
  - Omitted: [`frontend-ui-ux`] - can be omitted for MVP

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [7, 8] | Blocked By: [1, 2, 3, 5]

  **References**:
  - API/Type: `edupulse/api/schemas/demand.py` - Simulator primary request/response
  - API/Type: `edupulse/api/schemas/schedule.py` - downstream schedule response shape
  - API/Type: `edupulse/api/schemas/marketing.py` - downstream marketing response shape
  - Pattern: `docs/ai_plans/edupulse-frontend.md:366` - intended chaining flow, to retain
  - Pattern: `tests/test_demand.py` - known backend success/422/503 behaviors to mirror in UI expectations

  **Acceptance Criteria**:
  - [ ] Valid submit triggers demand call followed by parallel schedule/marketing calls.
  - [ ] Consolidated result view shows enrollment, tier, confidence interval, staffing/classroom recommendation, and marketing timing.
  - [ ] 422, 503, and offline errors each render distinct user feedback.
  - [ ] Low-tier result shows alert/risk messaging without relying on unsupported backend fields.

  **QA Scenarios**:
  ```
  Scenario: Happy-path simulation
    Tool: Playwright
    Steps: Open `/simulator`, enter a valid course name, future date, and field, then submit
    Expected: Result panel shows demand, schedule, and marketing data after the chained calls complete
    Evidence: .sisyphus/evidence/task-6-simulator-happy.png

  Scenario: Validation and model error handling
    Tool: Playwright
    Steps: Submit invalid input for client-side validation, then trigger backend 422 or 503 with a controlled backend state
    Expected: Form-level validation appears for invalid input; backend-specific error banner/message appears for API failures
    Evidence: .sisyphus/evidence/task-6-simulator-error.png
  ```

  **Commit**: YES | Message: `feat(frontend): add simulator api workflow` | Files: [`frontend/src/pages/Simulator.jsx`, `frontend/src/components/AlertPanel.jsx`]

- [ ] 7. Package frontend for Docker and align runtime proxying

  **What to do**: Create `frontend/Dockerfile` as a multi-stage Node→nginx build, add `frontend/nginx.conf` with SPA fallback and `/api/` proxy to service name `api:8000`, and update `docker-compose.yml` frontend service so the built image and port mapping are internally consistent. Prefer container listener port 80 inside nginx unless there is a strong reason otherwise; map host `3000` to container `80` to match the current compose placeholder.
  **Must NOT do**: Do not redesign the entire compose topology; do not proxy to `localhost` inside containers.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: bounded container wiring task
  - Skills: [] - existing compose conventions are enough
  - Omitted: [`git-master`] - unrelated

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [final verification] | Blocked By: [6]

  **References**:
  - Pattern: `docker-compose.yml` - existing `db`, `api`, `frontend` services and host port 3000 expectation
  - Pattern: `Dockerfile` - backend image conventions for production build flow
  - Pattern: `docs/ai_plans/edupulse-frontend.md:566` - prior Docker/nginx intent, corrected to align port mapping with compose placeholder

  **Acceptance Criteria**:
  - [ ] `frontend/Dockerfile` builds successfully.
  - [ ] nginx serves SPA routes and proxies `/api/` to backend service DNS.
  - [ ] `docker compose up --build` exposes frontend on `http://localhost:3000`.

  **QA Scenarios**:
  ```
  Scenario: Dockerized SPA routing
    Tool: Bash
    Steps: Run `docker compose up --build`, then request `/` and `/simulator`
    Expected: Both routes return HTTP 200 from nginx-served frontend
    Evidence: .sisyphus/evidence/task-7-docker-routes.txt

  Scenario: Dockerized API proxy
    Tool: Bash
    Steps: With the stack running, request `http://localhost:3000/api/v1/health`
    Expected: Request proxies through frontend nginx to backend API and returns JSON health data
    Evidence: .sisyphus/evidence/task-7-docker-proxy.txt
  ```

  **Commit**: YES | Message: `feat(frontend): add docker packaging` | Files: [`frontend/Dockerfile`, `frontend/nginx.conf`, `docker-compose.yml`]

- [ ] 8. Update project documentation and operator runbook

  **What to do**: Update `README.md` with frontend bootstrap, dev-server, backend+frontend local run sequence, Docker startup, and limitations of the MVP Dashboard. Explicitly document that the Dashboard uses fixed sample prediction requests, while Simulator is the primary interactive flow. Add troubleshooting notes for offline backend, unloaded models, and container proxy expectations.
  **Must NOT do**: Do not document unsupported features as complete; do not preserve stale assumptions from `docs/ai_plans/edupulse-frontend.md` such as incorrect thresholds or implied analytics endpoints.

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: docs clarity and operational accuracy are central
  - Skills: [] - simple technical writing
  - Omitted: [`frontend-ui-ux`] - not relevant

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [final verification] | Blocked By: [6]

  **References**:
  - Pattern: `README.md` - existing project setup and command style
  - Pattern: `docker-compose.yml` - compose commands to document
  - Pattern: `edupulse/api/main.py` - canonical backend app entrypoint
  - Pattern: `docs/ai_plans/edupulse-frontend.md` - source document being superseded; use only as historical reference

  **Acceptance Criteria**:
  - [ ] README includes frontend local dev and Docker instructions.
  - [ ] README explains MVP scope boundaries for Dashboard vs Simulator.
  - [ ] README troubleshooting notes cover offline API and model-loading scenarios.

  **QA Scenarios**:
  ```
  Scenario: Local operator path
    Tool: Bash
    Steps: Follow README local run commands exactly in a clean shell sequence
    Expected: Commands are syntactically valid and reflect actual project paths/ports
    Evidence: .sisyphus/evidence/task-8-readme-local.txt

  Scenario: Docker operator path
    Tool: Bash
    Steps: Follow README Docker commands and compare against compose service names and ports
    Expected: Documentation matches real container wiring with no stale path or port references
    Evidence: .sisyphus/evidence/task-8-readme-docker.txt
  ```

  **Commit**: YES | Message: `docs(frontend): document frontend workflows` | Files: [`README.md`]

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [ ] F1. Plan Compliance Audit — oracle
- [ ] F2. Code Quality Review — unspecified-high
- [ ] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [ ] F4. Scope Fidelity Check — deep

## Commit Strategy
- Prefer one commit per numbered task where the change is independently reviewable.
- Do not commit generated evidence files or secrets.
- Preserve frontend introduction as a sequence of small, auditable commits: scaffold → client/contracts → shell → data fixtures → dashboard → simulator → docker → docs.

## Success Criteria
- A new contributor can clone the repo, follow README instructions, and run the frontend locally.
- Simulator successfully demonstrates the real API value chain without backend endpoint expansion.
- Dashboard no longer claims unsupported analytics; it truthfully presents curated prediction summaries.
- Dockerized frontend serves the SPA and proxies backend requests correctly.
- Error and degraded-state handling is explicit, visible, and non-fatal.
