# EduPulse Frontend Phase A

## TL;DR
> **Summary**: Phase A는 EduPulse 프론트엔드를 디자인 우선으로 선행 구축하는 단계다. 모든 핵심 화면은 mock adapter 기반으로 완결되며, 백엔드 API 가용성이나 확장을 성공 조건으로 삼지 않는다.
> **Deliverables**:
> - Vite + React 기반 `frontend/` 앱 스캐폴드
> - Dashboard / Simulator mock-first UI
> - loading / success / empty / error 상태 UI 전부
> - mock adapter + future real adapter seam
> - Phase B-D 후속 문서화
> **Effort**: Medium
> **Parallel**: YES - 2 waves
> **Critical Path**: 1 → 2 → 4 → 5 → 6

## Context
### Original Request
Phase A용 프론트 선행 계획을 만들고, 나머지 Phase는 문서화해서 정리.

### Interview Summary
- 방향: 백엔드 선행이 아니라 **프론트 디자인/UX 선행**
- Phase A는 **mock-first**로 시연 가능해야 함
- 이후 백엔드/API 개선은 후속 단계로 문서화만 수행
- 현재 저장소에는 `frontend/`가 없으며, Dashboard를 실데이터 기반으로 만들 API도 부족함

### Metis Review (gaps addressed)
- Phase A의 Definition of Done에서 라이브 API 의존성을 제거
- Dashboard는 분석 대시보드가 아니라 **curated demo surface**로 고정
- Simulator도 Phase A에서는 mock adapter를 기본 경로로 고정
- health/schedule/marketing 관련 UI는 현재 계약을 닮은 mock shape를 사용하되, 실제 백엔드 semantics를 가정하지 않음

## Work Objectives
### Core Objective
백엔드 구현 상태와 무관하게 EduPulse의 사용자 경험, 정보 구조, 시각적 우선순위, 상태 UI를 검증할 수 있는 프론트엔드 MVP를 먼저 완성한다.

### Deliverables
- `frontend/` React/Vite 앱
- `Dashboard`, `Simulator`, `Layout`, `DemandChart`, `TierBadge`, `AlertPanel`
- `frontend/src/api/adapters/mockAdapter.js`
- `frontend/src/api/adapters/realAdapter.js` 또는 동등한 placeholder seam
- 화면 상태 설계: loading / success / empty / error
- 후속 단계 문서화: Phase B / C / D

### Definition of Done (verifiable conditions with commands)
- `cd frontend && npm install && npm run dev` 실행 시 앱이 정상 기동한다.
- `cd frontend && npm run build`가 성공한다.
- `/`와 `/simulator`에서 백엔드가 꺼져 있어도 mock data 기반으로 정상 시연된다.
- 각 핵심 화면은 loading / success / empty / error 상태를 명시적으로 렌더링한다.
- mock adapter와 real adapter seam이 분리되어 있어, 후속 연동 시 컴포넌트 교체 없이 adapter 교체만 가능하다.

### Must Have
- Vite + React 18 기반 앱
- 페이지 범위: `/` Dashboard, `/simulator` Simulator
- mock data 기반 결과 표시
- API adapter 추상화 계층
- demo 데이터임을 숨기지 않는 UI 레이블/설명
- 후속 Phase 문서화 섹션 포함

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- 신규 백엔드 API 구현 금지
- 실 API 연결을 Phase A 완료 조건으로 삼지 않음
- Dashboard를 실시간/집계/히스토리 분석처럼 과장 금지
- `assignment_plan`을 구조화된 스케줄 보드처럼 설계 금지
- Reports/추가 페이지/프론트 테스트 프레임워크 도입 금지

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: none + mock-first manual QA flows
- QA policy: Every task has agent-executed scenarios
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks for max parallelism.

Wave 1: scaffold + state model + adapter contract + shell (Tasks 1-4)
Wave 2: feature assembly + polish + documentation (Tasks 5-7)

### Dependency Matrix (full, all tasks)
- 1 blocks 2, 3, 4, 5, 6, 7
- 2 blocks 5, 6
- 3 blocks 5, 6, 7
- 4 blocks 5, 6
- 5 blocks 6
- 6 blocks 7
- 7 blocks final verification

### Agent Dispatch Summary (wave → task count → categories)
- Wave 1 → 4 tasks → quick / visual-engineering / writing
- Wave 2 → 3 tasks → visual-engineering / quick / writing

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [x] 1. Bootstrap the greenfield frontend app

  **What to do**: Create `frontend/` with Vite + React 18, set up `react-router-dom` and `recharts`, add a stable root render, and establish a minimal but clean file structure for pages, components, adapters, and fixtures. Reuse the existing root `.gitignore` frontend exclusions rather than reworking repo-wide ignore rules.
  **Must NOT do**: Do not add TypeScript, Tailwind, global state libraries, or frontend test frameworks in Phase A.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: deterministic scaffold work
  - Skills: [] - no specialty skill required
  - Omitted: [`frontend-ui-ux`] - visual refinement comes later in the wave

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [2, 3, 4, 5, 6, 7] | Blocked By: []

  **References**:
  - Pattern: `docs/ai_plans/edupulse-frontend.md:146` - Vite React initialization direction
  - Pattern: `docker-compose.yml` - future frontend service placeholder
  - Pattern: `README.md` - project command style for later docs alignment

  **Acceptance Criteria**:
  - [ ] `frontend/package.json` includes `dev`, `build`, and `preview` scripts.
  - [ ] `frontend/src/main.jsx` mounts successfully.
  - [ ] `cd frontend && npm install && npm run build` succeeds.

  **QA Scenarios**:
  ```
  Scenario: Fresh frontend bootstrap
    Tool: Bash
    Steps: Run `npm install` then `npm run build` in `frontend/`
    Expected: Dependencies install successfully and build completes without missing-module errors
    Evidence: .sisyphus/evidence/task-1-bootstrap.txt

  Scenario: Dev server startup
    Tool: Bash
    Steps: Run `npm run dev -- --host 127.0.0.1 --port 4173`
    Expected: Vite dev server starts cleanly and exposes a local URL
    Evidence: .sisyphus/evidence/task-1-devserver.txt
  ```

  **Commit**: YES | Message: `feat(frontend): scaffold phase a app` | Files: [`frontend/**`]

- [x] 2. Define UI state model and demo content contract

  **What to do**: Design and codify the canonical frontend view-model shapes for Dashboard cards, chart points, simulator results, alerts, and system status panels. Define explicit loading, success, empty, and error state payloads so component behavior is stable before any real API integration. Include demo labels that make it clear the data is mocked.
  **Must NOT do**: Do not mirror raw backend responses directly into component props; do not let components invent their own incompatible state shapes.

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: this is contract and content-shape design work
  - Skills: [] - straightforward schema authoring
  - Omitted: [`frontend-ui-ux`] - focus is structure, not visuals

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [5, 6] | Blocked By: [1]

  **References**:
  - API/Type: `edupulse/api/schemas/demand.py` - source inspiration for simulator result fields
  - API/Type: `edupulse/api/schemas/schedule.py` - note nullable/limited schedule shape
  - API/Type: `edupulse/api/schemas/marketing.py` - marketing response fields to model mock data after
  - Pattern: `edupulse/constants.py` - tier labels only

  **Acceptance Criteria**:
  - [ ] Shared view-model definitions exist for Dashboard and Simulator.
  - [ ] All four UI states are modeled explicitly.
  - [ ] Demo/mock labeling is included in the content model.

  **QA Scenarios**:
  ```
  Scenario: State completeness review
    Tool: Bash
    Steps: Inspect the frontend fixtures/view-model definitions used by Dashboard and Simulator
    Expected: Each primary surface has loading, success, empty, and error payloads defined
    Evidence: .sisyphus/evidence/task-2-state-model.txt

  Scenario: Drift prevention review
    Tool: Bash
    Steps: Compare mock/view-model keys against the adapter contract and component usage
    Expected: Components consume normalized shapes consistently instead of ad hoc payloads
    Evidence: .sisyphus/evidence/task-2-contract-parity.txt
  ```

  **Commit**: YES | Message: `feat(frontend): define phase a view models` | Files: [`frontend/src/api/**`, `frontend/src/fixtures/**`]

- [x] 3. Create adapter seams with mock-first default

  **What to do**: Implement an adapter boundary that makes `mockAdapter` the Phase A default and provides a `realAdapter` placeholder shaped for later use. The real adapter may reference the current backend schemas and routes, but it must not be required for the app to function. Ensure the selection mechanism is centralized and swappable without touching page components.
  **Must NOT do**: Do not make real API availability part of startup logic; do not let pages call `fetch` directly.

  **Recommended Agent Profile**:
  - Category: `quick` - Reason: bounded architecture seam implementation
  - Skills: [] - no special skill needed
  - Omitted: [`git-master`] - irrelevant

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [5, 6, 7] | Blocked By: [1]

  **References**:
  - Pattern: `edupulse/api/routers/demand.py` - later real adapter target
  - Pattern: `edupulse/api/routers/schedule.py` - later real adapter target
  - Pattern: `edupulse/api/routers/marketing.py` - later real adapter target
  - Pattern: `edupulse/api/routers/health.py` - later advisory status target

  **Acceptance Criteria**:
  - [ ] `mockAdapter` powers the app by default.
  - [ ] `realAdapter` exists as a seam or placeholder without breaking the app.
  - [ ] Pages/components depend only on the adapter interface.

  **QA Scenarios**:
  ```
  Scenario: Mock-only runtime
    Tool: Bash
    Steps: Start the frontend with backend offline and the default adapter selection
    Expected: App boots and all primary views render from mock data
    Evidence: .sisyphus/evidence/task-3-mock-runtime.txt

  Scenario: Seam swap safety
    Tool: Bash
    Steps: Toggle the adapter selection to the real-adapter placeholder mode in a controlled local run
    Expected: The app still builds and any unavailable backend path fails in a controlled, isolated way
    Evidence: .sisyphus/evidence/task-3-seam-swap.txt
  ```

  **Commit**: YES | Message: `feat(frontend): add mock first adapters` | Files: [`frontend/src/api/adapters/**`]

- [x] 4. Build shared layout and navigation shell

  **What to do**: Implement the app shell with a coherent header/sidebar/top navigation, route structure for `/` and `/simulator`, and reusable status surfaces for banners, section headers, and empty/error cards. The shell should visually establish EduPulse’s information architecture before deep feature logic is added.
  **Must NOT do**: Do not add Reports or extra routes; do not couple layout behavior to backend status.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: UX structure and page shell are the focus
  - Skills: [] - standard React routing/layout patterns suffice
  - Omitted: [`frontend-ui-ux`] - optional, not required

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [5, 6] | Blocked By: [1]

  **References**:
  - Pattern: `docs/ai_plans/edupulse-frontend.md:148` - original layout/router intent to simplify
  - Pattern: `edupulse/api/middleware.py` - dev/prod origin assumptions only for future integration context

  **Acceptance Criteria**:
  - [ ] `/` and `/simulator` routes exist.
  - [ ] Layout remains mounted during route transitions.
  - [ ] Shared status surfaces can be reused across both pages.

  **QA Scenarios**:
  ```
  Scenario: Route navigation shell
    Tool: Playwright
    Steps: Open `/`, navigate to `/simulator`, then return to `/`
    Expected: Navigation works and the shared layout persists across route changes
    Evidence: .sisyphus/evidence/task-4-shell-routing.png

  Scenario: Fallback route handling
    Tool: Playwright
    Steps: Open an undefined route such as `/missing`
    Expected: User sees a controlled fallback/redirect rather than a raw crash
    Evidence: .sisyphus/evidence/task-4-shell-fallback.png
  ```

  **Commit**: YES | Message: `feat(frontend): add phase a shell` | Files: [`frontend/src/App.jsx`, `frontend/src/components/Layout.jsx`, `frontend/src/pages/**`]

- [x] 5. Implement the Dashboard as a curated mock demo surface

  **What to do**: Build the main Dashboard using curated demo scenarios, summary cards, demand visualizations, tier badges, and alert highlights. Use mock data that resembles the intended product story, but label it truthfully as demo content. Include all four primary UI states and ensure chart rendering is stable even with sparse/empty data.
  **Must NOT do**: Do not present the Dashboard as live analytics, historical truth, or API-backed intelligence in Phase A.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: this is the core design-first deliverable
  - Skills: [] - standard chart/UI implementation
  - Omitted: [`frontend-ui-ux`] - optional unless higher visual polish is separately requested

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [6] | Blocked By: [1, 2, 3, 4]

  **References**:
  - Pattern: `docs/ai_plans/edupulse-frontend.md:269` - original Dashboard component intent
  - Pattern: `edupulse/constants.py` - valid tier labels for badge display only

  **Acceptance Criteria**:
  - [ ] Dashboard renders loading, success, empty, and error states.
  - [ ] Summary cards, chart, and alert surfaces are visually coherent.
  - [ ] Demo/mock labeling is visible and unambiguous.

  **QA Scenarios**:
  ```
  Scenario: Dashboard happy-path demo
    Tool: Playwright
    Steps: Open `/` in default mock mode
    Expected: Curated dashboard content renders completely with chart, badges, and summary content
    Evidence: .sisyphus/evidence/task-5-dashboard-success.png

  Scenario: Dashboard empty/error states
    Tool: Playwright
    Steps: Switch the dashboard fixture to empty state, then error state, and reload each view
    Expected: Both states render intentionally with no broken layout or undefined text
    Evidence: .sisyphus/evidence/task-5-dashboard-states.png
  ```

  **Commit**: YES | Message: `feat(frontend): add mock dashboard experience` | Files: [`frontend/src/pages/Dashboard.jsx`, `frontend/src/components/DemandChart.jsx`, `frontend/src/components/TierBadge.jsx`, `frontend/src/components/AlertPanel.jsx`]

- [x] 6. Implement the Simulator as a mock-first interaction flow

  **What to do**: Build the Simulator form and result flow so users can enter a course concept, start date, and field, then receive mock prediction, staffing, and marketing guidance through the adapter interface. Preserve the future orchestration shape conceptually, but in Phase A all results may come from the mock adapter. Include clear form validation, result hierarchy, and low-tier risk messaging.
  **Must NOT do**: Do not require backend availability; do not imply real forecast accuracy; do not design around unsupported structured assignment data.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: interaction design and result presentation dominate
  - Skills: [] - straightforward UI state work
  - Omitted: [`frontend-ui-ux`] - optional

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [7] | Blocked By: [1, 2, 3, 4, 5]

  **References**:
  - Pattern: `docs/ai_plans/edupulse-frontend.md:346` - Simulator intent, simplified to mock-first
  - API/Type: `edupulse/api/schemas/demand.py` - inspiration for result contents
  - API/Type: `edupulse/api/schemas/schedule.py` - use simple counts, not structured board data
  - API/Type: `edupulse/api/schemas/marketing.py` - marketing recommendation content shape

  **Acceptance Criteria**:
  - [ ] Valid form submission produces a coherent mock result panel.
  - [ ] loading, success, validation error, and adapter error states all render.
  - [ ] Risk/alert messaging is shown for low-tier scenarios.

  **QA Scenarios**:
  ```
  Scenario: Simulator happy path
    Tool: Playwright
    Steps: Open `/simulator`, enter valid inputs, and submit
    Expected: Mock result panel shows demand, schedule, and marketing guidance in one coherent layout
    Evidence: .sisyphus/evidence/task-6-simulator-success.png

  Scenario: Simulator validation and error states
    Tool: Playwright
    Steps: Submit missing/invalid fields, then switch the simulator fixture to an adapter error state
    Expected: Validation feedback and adapter error UI appear clearly without collapsing layout
    Evidence: .sisyphus/evidence/task-6-simulator-states.png
  ```

  **Commit**: YES | Message: `feat(frontend): add mock simulator flow` | Files: [`frontend/src/pages/Simulator.jsx`, `frontend/src/components/AlertPanel.jsx`]

- [x] 7. Document Phase B-D activation path and Phase A operator guidance

  **What to do**: Update `README.md` and/or adjacent project docs so Phase A can be run and reviewed by others, and document the remaining phases as follow-on activation phases rather than immediate implementation scope. Phase B should cover contract hardening, Phase C real integration, and Phase D dashboard/data expansion. For each later phase, document objective, unlock condition, backend prerequisites, and explicit non-goals.
  **Must NOT do**: Do not write later phases as if they are already scheduled for immediate execution; do not preserve stale assumptions like dashboard-ready APIs.

  **Recommended Agent Profile**:
  - Category: `writing` - Reason: the task is documentation-heavy and requires precise scoping
  - Skills: [] - plain technical writing
  - Omitted: [`frontend-ui-ux`] - not relevant

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [final verification] | Blocked By: [1, 2, 3, 6]

  **References**:
  - Pattern: `README.md` - operator setup and run flow
  - Pattern: `docs/ai_plans/edupulse-frontend.md` - historical source to supersede, not preserve
  - Pattern: `edupulse/api/routers/*.py` - current backend limitations that should be documented honestly

  **Acceptance Criteria**:
  - [ ] Phase A local run instructions are accurate.
  - [ ] Phase B, C, and D are documented with objective, unlock condition, prerequisites, and non-goals.
  - [ ] Documentation clearly states that Phase A is mock-first and backend-independent.

  **QA Scenarios**:
  ```
  Scenario: Phase A operator walkthrough
    Tool: Bash
    Steps: Follow the documented Phase A run instructions in a clean shell sequence
    Expected: Instructions are valid and sufficient to start the frontend demo locally
    Evidence: .sisyphus/evidence/task-7-phase-a-docs.txt

  Scenario: Later-phase clarity review
    Tool: Bash
    Steps: Inspect the documented Phase B-D sections for objective, unlock condition, prerequisites, and non-goals
    Expected: Each later phase is documented as a future activation path, not an immediate task list
    Evidence: .sisyphus/evidence/task-7-future-phases.txt
  ```

  **Commit**: YES | Message: `docs(frontend): document phase a and follow on phases` | Files: [`README.md`, `docs/**`]

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [x] F1. Plan Compliance Audit — oracle
- [x] F2. Code Quality Review — unspecified-high
- [x] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [x] F4. Scope Fidelity Check — deep

## Commit Strategy
- Keep Phase A commits reviewable and UI-focused: scaffold → state model → adapters → shell → dashboard → simulator → docs.
- Do not mix future real-integration work into Phase A commits.
- Do not commit mock evidence artifacts or secrets.

## Success Criteria
- The team can demo EduPulse frontend UX with no backend dependency.
- The UI truthfully represents mock/demo data rather than pretending to be production analytics.
- Later real integration can happen by replacing adapter implementations rather than rewriting page components.
- Future backend work is clarified in documentation rather than silently expanding Phase A scope.

## Deferred Follow-On Phases (Documentation Only)
### Phase B — Contract Hardening
- **Objective**: Freeze request/response contracts, normalize error shapes, and decide canonical adapter interfaces.
- **Unlock Condition**: Phase A UI structure and demo content are accepted.
- **Backend Prerequisites**: Confirm exact API response examples for demand, schedule, marketing, health.
- **Non-Goals**: No large dashboard aggregation work yet.

### Phase C — Real Integration
- **Objective**: Connect the Simulator to real backend APIs first, keeping Dashboard mock-backed if needed.
- **Unlock Condition**: Stable backend availability and agreed error semantics.
- **Backend Prerequisites**: Working demand/schedule/marketing endpoints, predictable 422/503 behavior, agreed health semantics.
- **Non-Goals**: No dashboard analytics expansion unless supported by API.

### Phase D — Dashboard/Data Expansion
- **Objective**: Upgrade Dashboard from curated demo surface to real data surface once dedicated aggregation/list/trend APIs exist.
- **Unlock Condition**: Backend ships dashboard summary, batch/list, and trend endpoints.
- **Backend Prerequisites**: New dashboard-focused APIs, documented KPI definitions, performance/caching decisions.
- **Non-Goals**: Do not retrofit the existing mock dashboard into “real analytics” without the required data contracts.
