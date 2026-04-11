# EduPulse Frontend UI/UX Improvements

## TL;DR
> **Summary**: Rework the EduPulse frontend so the product value from `README.md` is immediately legible in the UI: 운영 효율화, 마케팅·매출 연계, 전략 기획. Improve the shared shell and component language first, then align all five pages to express outcomes, next actions, and trustworthy data states.
> **Deliverables**:
> - Shared visual language and shell updates in `frontend/src/index.css` and `frontend/src/components/Layout.jsx`
> - Improved state, alert, chart, and score components that better communicate action and trust
> - Page-level UX updates across Dashboard, Simulator, Marketing, Operations, and Market
> - Lint/build verification plus browser-based QA evidence for all tasks
> **Effort**: Large
> **Parallel**: YES - 2 waves
> **Critical Path**: 1 → 2/3 → 4/5/6/7/8

## Context
### Original Request
- Improve the `frontend/` UI/UX and determine where to start.
- Make the UI feel more like the core service value described in `README.md`, because the current experience is not landing emotionally or functionally.

### Interview Summary
- Improvement lens: balanced across usability, visual polish, and persuasion.
- Device priority: desktop-first.
- Verification strategy: keep existing `lint/build` + manual/browser QA; do not add frontend test frameworks.
- Scope: entire frontend, not only Dashboard.
- Persuasion clarified: the UI must make the three README value pillars tangible:
  - 운영 효율화
  - 마케팅·매출 연계
  - 전략 기획

### Metis Review (gaps addressed)
- Do **not** rebuild the CSS system from scratch; patch the existing token/class system in `frontend/src/index.css:1-326`.
- Preserve current architecture: Router, adapter pattern, local page state, and existing file boundaries.
- Do **not** add dependencies, routes, hooks, contexts, i18n, backend/API changes, or mobile-first redesign.
- Reuse existing patterns rather than inventing new ones: `StatusPanel`, cross-page links in `Operations.jsx`, and current `UIState` rendering behavior.
- Convert “persuasion” into explicit UI outcomes: clearer summaries, stronger section framing, and next-action CTAs tied to README product value.

## Work Objectives
### Core Objective
Transform the frontend from a generic analytics dashboard into a product narrative that clearly shows how EduPulse helps academies decide what to open, how to operate it, and when/how to market it.

### Deliverables
- Shared shell and styling improvements that make product pillars visible at the app level.
- Stronger loading/empty/error trust states.
- More actionable charts, cards, and alert surfaces.
- Page-level hierarchy and CTA improvements aligned to README service pillars.
- Explicit browser QA evidence for each task.

### Definition of Done (verifiable conditions with commands)
- `cd frontend && npm run lint` exits 0.
- `cd frontend && npm run build` exits 0.
- `grep -n "운영 효율화\|마케팅·매출 연계\|전략 기획" frontend/src/components/Layout.jsx frontend/src/pages/*.jsx` returns matches in the intended summary/CTA surfaces.
- All five routes render without runtime crash in dev mode: `/`, `/simulator`, `/marketing`, `/operations`, `/market`.
- Shared components still compile with existing imports and adapter-driven page flows.

### Must Have
- Preserve current routing in `frontend/src/App.jsx:21-35`.
- Preserve adapter imports and page data flow via `../api/adapters/index.js`.
- Improve clarity of the three product pillars from `README.md:16-37` inside the frontend shell and page sections.
- Use existing CSS variables/classes as the primary styling mechanism.
- Provide deterministic, agent-executable QA for each task.

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- Must NOT add new dependencies.
- Must NOT add or change routes.
- Must NOT refactor adapter/client/transformer/viewModel layers.
- Must NOT introduce global state/context/custom hooks.
- Must NOT start i18n/string extraction work.
- Must NOT expand into backend, docs, or mobile-first redesign.
- Must NOT replace current CSS approach with Tailwind, CSS modules, or styled-components.

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: tests-after with existing `npm run lint` + `npm run build`; no new framework.
- QA policy: Every task includes browser QA scenarios using app text/roles plus command verification.
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks for max parallelism.

Wave 1: 1 shared shell/value framing, 2 shared state+alert surfaces, 3 charts+gauges semantics

Wave 2: 4 Dashboard, 5 Simulator, 6 Marketing, 7 Operations, 8 Market

### Dependency Matrix (full, all tasks)
| Task | Depends On | Enables |
|---|---|---|
| 1 | none | 4,5,6,7,8 |
| 2 | 1 | 4,5,6,7,8 |
| 3 | 1 | 4,6,7,8 |
| 4 | 1,2,3 | F1-F4 |
| 5 | 1,2 | F1-F4 |
| 6 | 1,2,3 | F1-F4 |
| 7 | 1,2,3 | F1-F4 |
| 8 | 1,2,3 | F1-F4 |

### Agent Dispatch Summary (wave → task count → categories)
| Wave | Task Count | Categories |
|---|---:|---|
| 1 | 3 | visual-engineering, unspecified-high |
| 2 | 5 | visual-engineering |
| Final | 4 | oracle, unspecified-high, deep |

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [x] 1. Reframe the app shell around the three service pillars

  **What to do**: Update `frontend/src/components/Layout.jsx` and `frontend/src/index.css` so the global shell communicates product value before a page is read. Replace the generic “EduPulse Console” framing with shell copy and supporting microcopy that foreground the README pillars. Keep the existing sidebar route structure, but add concise descriptive helper text and stronger active-state hierarchy so users understand each route’s operational purpose at a glance.
  **Must NOT do**: Do not add routes, drawers, hamburger menus, or mobile-specific navigation. Do not remove current five-page navigation.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: shell hierarchy, navigation semantics, and shared polish are primarily UI concerns.
  - Skills: [] - No special skill required.
  - Omitted: [`frontend-ui-ux`] - Not needed because the plan already specifies concrete changes.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 2,3,4,5,6,7,8 | Blocked By: none

  **References**:
  - Product value source: `README.md:16-37` - three value pillars and nine service functions to make tangible.
  - Router contract: `frontend/src/App.jsx:23-31` - route structure must remain unchanged.
  - Current shell: `frontend/src/components/Layout.jsx:4-241` - sidebar, top header, and main content framing.
  - Existing design tokens: `frontend/src/index.css:1-180` - colors, spacing, card, page header, toolbar, button group.

  **Acceptance Criteria**:
  - [ ] `grep -n "운영 효율화\|마케팅·매출 연계\|전략 기획" frontend/src/components/Layout.jsx` returns all three phrases.
  - [ ] `grep -n "EduPulse Console" frontend/src/components/Layout.jsx` returns no matches.
  - [ ] `cd frontend && npm run lint` exits 0.
  - [ ] `cd frontend && npm run build` exits 0.

  **QA Scenarios** (MANDATORY - task incomplete without these):
  ```
  Scenario: Shell communicates value before navigation
    Tool: Playwright
    Steps: Open http://localhost:5173/ ; verify the sidebar shows links for 대시보드, 시뮬레이터, 마케팅 분석, 운영 관리, 시장 분석 ; verify the header or shell helper text includes 운영 효율화, 마케팅·매출 연계, 전략 기획.
    Expected: All three README pillars are visible without navigating away from the landing route.
    Evidence: .sisyphus/evidence/task-1-shell-pillars.png

  Scenario: Active navigation remains intact
    Tool: Playwright
    Steps: Click text "운영 관리" in the sidebar ; verify the active nav item is visually highlighted and the page title "운영 관리" is visible.
    Expected: Existing route navigation still works and active-state hierarchy is clearer than the inactive items.
    Evidence: .sisyphus/evidence/task-1-shell-active.png
  ```

  **Commit**: YES | Message: `feat: reframe app shell around service pillars` | Files: `frontend/src/components/Layout.jsx`, `frontend/src/index.css`

- [x] 2. Standardize trust-building state and alert surfaces

  **What to do**: Improve `frontend/src/components/StatusPanel.jsx`, `frontend/src/components/AlertPanel.jsx`, `frontend/src/components/TierBadge.jsx`, and shared CSS in `frontend/src/index.css` so loading/empty/error/critical states feel intentional and trustworthy. Ensure alerts visually distinguish urgency, TierBadge handles “알 수 없음” more gracefully, and alert actions are explicitly interactive rather than decorative.
  **Must NOT do**: Do not introduce modal flows, toast systems, or backend-driven real-time notification work.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: component polish, semantics, and action affordance refinement.
  - Skills: [] - No special skill required.
  - Omitted: [`ai-slop-remover`] - This is not a style cleanup pass; it is targeted UX work.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 4,5,6,7,8 | Blocked By: 1

  **References**:
  - Status pattern: `frontend/src/components/StatusPanel.jsx:3-97` - current loading/error/empty/info handling.
  - Alert pattern: `frontend/src/components/AlertPanel.jsx:3-107` - current severity display and action button rendering.
  - Tier badge pattern: `frontend/src/components/TierBadge.jsx:3-67` - current High/Mid/Low/unknown visual treatment.
  - Existing state usage on Dashboard: `frontend/src/pages/Dashboard.jsx:112-179` - target for consistency across pages.
  - Existing utility classes: `frontend/src/index.css:154-326` - card, buttons, form, metric, badge styles.

  **Acceptance Criteria**:
  - [ ] `grep -n "actionLabel" frontend/src/components/AlertPanel.jsx` still returns the action rendering path and the updated component exposes a real interaction path for action buttons.
  - [ ] `grep -n "알 수 없음" frontend/src/components/TierBadge.jsx` returns the fallback copy and it is wrapped in clearer explanatory badge copy rather than a bare label.
  - [ ] `grep -n "loading\|empty\|error" frontend/src/components/StatusPanel.jsx` returns all three variant branches.
  - [ ] `cd frontend && npm run lint` exits 0.
  - [ ] `cd frontend && npm run build` exits 0.

  **QA Scenarios**:
  ```
  Scenario: Dashboard loading and empty states feel intentional
    Tool: Playwright
    Steps: Run app in dev mode ; on 대시보드 click the demo state button "로딩 중" ; capture the loading panel ; click "데이터 없음" ; capture the empty panel.
    Expected: Both states are visually distinct, legible, and read as trustworthy product states rather than broken screens.
    Evidence: .sisyphus/evidence/task-2-state-panels.png

  Scenario: Critical alerts communicate urgency and action
    Tool: Playwright
    Steps: Navigate to /simulator ; submit inputs that trigger a low-tier result if mock state supports it ; inspect the critical alert rendered above results.
    Expected: Critical severity is visually stronger than informational states and any action button/link appears clearly clickable.
    Evidence: .sisyphus/evidence/task-2-alert-critical.png
  ```

  **Commit**: YES | Message: `feat: strengthen shared state and alert feedback` | Files: `frontend/src/components/StatusPanel.jsx`, `frontend/src/components/AlertPanel.jsx`, `frontend/src/components/TierBadge.jsx`, `frontend/src/index.css`

- [x] 3. Make charts and score surfaces explain decisions, not just display data

  **What to do**: Update `frontend/src/components/DemandChart.jsx`, `frontend/src/components/RiskGauge.jsx`, and `frontend/src/components/ScoreBar.jsx` so chart/gauge surfaces better communicate what the user should infer. Replace hardcoded colors with token-driven values where possible, strengthen labels and legends, and add clearer supporting copy/semantics that connect metrics to decisions.
  **Must NOT do**: Do not change charting library, API payload shape, or introduce export/report functionality.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: this is chart/gauge comprehension and semantic clarity work.
  - Skills: [] - No special skill required.
  - Omitted: [`playwright`] - Browser QA will happen after implementation, not during planning.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 4,6,7,8 | Blocked By: 1

  **References**:
  - Demand chart: `frontend/src/components/DemandChart.jsx:14-145` - current confidence band, legend, tooltip, and empty state.
  - Risk gauge: `frontend/src/components/RiskGauge.jsx:24-72` - percentage and bar rendering.
  - Score bar: `frontend/src/components/ScoreBar.jsx:3-49` - recommended-score display.
  - Dashboard chart embedding: `frontend/src/pages/Dashboard.jsx:148-179` - target usage pattern.
  - Market recommendation cards: `frontend/src/pages/Market.jsx:281-327` - score surface currently used for optimal start recommendation.

  **Acceptance Criteria**:
  - [ ] `grep -n "var(--color-primary\|var(--color-border\|var(--color-text-muted\|var(--color-success-text\|var(--color-warning-text\|var(--color-error-text" frontend/src/components/DemandChart.jsx frontend/src/components/RiskGauge.jsx frontend/src/components/ScoreBar.jsx` returns token-based styling usage in all three components.
  - [ ] `grep -n "예상 수요\|상한선\|하한선" frontend/src/components/DemandChart.jsx` returns all legend labels after update.
  - [ ] `grep -n "percentage" frontend/src/components/RiskGauge.jsx frontend/src/components/ScoreBar.jsx` still returns the percentage rendering logic.
  - [ ] `cd frontend && npm run lint` exits 0.
  - [ ] `cd frontend && npm run build` exits 0.

  **QA Scenarios**:
  ```
  Scenario: Dashboard demand chart now reads like a decision aid
    Tool: Playwright
    Steps: Open / ; ensure demo state is "성공" ; inspect the card titled "예상 수요 트렌드" and its legend/summary text.
    Expected: The chart clearly explains predicted demand and confidence range without requiring domain guesswork.
    Evidence: .sisyphus/evidence/task-3-demand-chart.png

  Scenario: Market score bars highlight the recommended start option
    Tool: Playwright
    Steps: Open /market ; locate the card group titled "최적 개강일 추천" ; compare the first candidate card against the others.
    Expected: The recommended option is visibly dominant and the score bar explains why it is recommended.
    Evidence: .sisyphus/evidence/task-3-scorebar-market.png
  ```

  **Commit**: YES | Message: `feat: clarify chart and score decision surfaces` | Files: `frontend/src/components/DemandChart.jsx`, `frontend/src/components/RiskGauge.jsx`, `frontend/src/components/ScoreBar.jsx`, `frontend/src/index.css`

- [x] 4. Rebuild Dashboard hierarchy around product outcomes

  **What to do**: Update `frontend/src/pages/Dashboard.jsx` so the page immediately communicates the three product outcomes: current demand signal, urgent operating risk, and recommended next action. Keep the demo switcher in dev mode, but reorganize summary cards, chart framing, and alert framing so the page feels like a command center rather than a generic analytics page.
  **Must NOT do**: Do not remove field filtering, refresh behavior, or the dev-only demo switcher.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: primary value-story page with information hierarchy and CTA improvements.
  - Skills: [] - No special skill required.
  - Omitted: [`review-work`] - Review belongs in final verification wave, not implementation.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: F1-F4 | Blocked By: 1,2,3

  **References**:
  - Dashboard page: `frontend/src/pages/Dashboard.jsx:13-185`.
  - Summary cards: `frontend/src/pages/Dashboard.jsx:112-145`.
  - Chart card: `frontend/src/pages/Dashboard.jsx:148-158`.
  - Alert card: `frontend/src/pages/Dashboard.jsx:160-179`.
  - README value proposition: `README.md:11-12`, `README.md:18-37`.

  **Acceptance Criteria**:
  - [ ] `grep -n "운영 효율화\|마케팅·매출 연계\|전략 기획" frontend/src/pages/Dashboard.jsx` returns at least one explicit value-pillar phrase in the page framing or action copy.
  - [ ] `grep -n "추천\|다음 액션\|바로가기" frontend/src/pages/Dashboard.jsx` returns explicit action-oriented copy.
  - [ ] `grep -n "import.meta.env.DEV" frontend/src/pages/Dashboard.jsx` still returns the dev-only demo switcher guard.
  - [ ] `cd frontend && npm run lint` exits 0.
  - [ ] `cd frontend && npm run build` exits 0.

  **QA Scenarios**:
  ```
  Scenario: Dashboard immediately shows what matters
    Tool: Playwright
    Steps: Open / ; capture the first viewport without scrolling.
    Expected: The first viewport makes it clear what the current demand status is, what risk exists, and what action the operator should take next.
    Evidence: .sisyphus/evidence/task-4-dashboard-fold.png

  Scenario: Dashboard state switching still works in dev
    Tool: Playwright
    Steps: Open / ; click the demo buttons "오류", "데이터 없음", and "성공" in sequence.
    Expected: Summary cards, chart card, and alert card all render the correct state without layout collapse.
    Evidence: .sisyphus/evidence/task-4-dashboard-states.png
  ```

  **Commit**: YES | Message: `feat: align dashboard hierarchy with product outcomes` | Files: `frontend/src/pages/Dashboard.jsx`, `frontend/src/index.css`

- [x] 5. Turn Simulator into a decision brief, not just a form

  **What to do**: Update `frontend/src/pages/Simulator.jsx` so the page better expresses README strategic planning value. Improve scenario comparison readability, make the result summary more executive, and strengthen cross-page next steps to operations and marketing based on the simulation outcome.
  **Must NOT do**: Do not change fixture contracts in `frontend/src/fixtures/simulatorStates.js` or API request shape.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: form/result clarity and scenario storytelling.
  - Skills: [] - No special skill required.
  - Omitted: [`git-master`] - No git operation is part of implementation.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: F1-F4 | Blocked By: 1,2

  **References**:
  - Scenario cards: `frontend/src/pages/Simulator.jsx:15-64`.
  - Form inputs and validation: `frontend/src/pages/Simulator.jsx:66-126`, `188-289`.
  - Result summary and cross-page action: `frontend/src/pages/Simulator.jsx:316-409`.
  - Existing operations link: `frontend/src/pages/Simulator.jsx:393-407`.
  - README strategic pillar: `README.md:32-37`.

  **Acceptance Criteria**:
  - [ ] `grep -n "시나리오 비교" frontend/src/pages/Simulator.jsx` returns the comparison section with stronger framing copy.
  - [ ] `grep -n "운영 계획 보기\|마케팅" frontend/src/pages/Simulator.jsx` returns explicit next-step navigation tied to the simulation result.
  - [ ] `grep -n "validationError" frontend/src/pages/Simulator.jsx` still returns validation handling after UX improvements.
  - [ ] `cd frontend && npm run lint` exits 0.
  - [ ] `cd frontend && npm run build` exits 0.

  **QA Scenarios**:
  ```
  Scenario: Empty simulator state guides the user clearly
    Tool: Playwright
    Steps: Open /simulator ; do not enter any values.
    Expected: The empty state clearly explains what the user will learn about demand, operations, and marketing after running the simulation.
    Evidence: .sisyphus/evidence/task-5-simulator-empty.png

  Scenario: Successful simulation leads to next actions
    Tool: Playwright
    Steps: Open /simulator ; fill courseName="Python 웹개발 심화" ; select field="코딩" ; choose a future date ; click "시뮬레이션 실행".
    Expected: The result card summarizes demand, operations, and marketing recommendations and provides an explicit next action link.
    Evidence: .sisyphus/evidence/task-5-simulator-success.png
  ```

  **Commit**: YES | Message: `feat: make simulator results more actionable` | Files: `frontend/src/pages/Simulator.jsx`, `frontend/src/index.css`

- [x] 6. Make Marketing feel like a revenue decision cockpit

  **What to do**: Update `frontend/src/pages/Marketing.jsx` so it clearly expresses the README marketing/revenue value: lead conversion, ad launch timing, and discount strategy. Strengthen metric hierarchy, emphasize the current demand tier card, and improve recommendation blocks so “what to do next” is obvious.
  **Must NOT do**: Do not add export/report download features or campaign creation flows.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: chart hierarchy, recommendation framing, and tier-card emphasis.
  - Skills: [] - No special skill required.
  - Omitted: [`writing`] - This is UX product copy inside the UI, not documentation.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: F1-F4 | Blocked By: 1,2,3

  **References**:
  - Marketing page: `frontend/src/pages/Marketing.jsx:9-248`.
  - Lead conversion KPI: `frontend/src/pages/Marketing.jsx:101-127`.
  - Trend charts: `frontend/src/pages/Marketing.jsx:129-162`.
  - Recommendation list: `frontend/src/pages/Marketing.jsx:165-188`.
  - Tier timing cards: `frontend/src/pages/Marketing.jsx:191-239`.
  - README marketing pillar: `README.md:25-30`.

  **Acceptance Criteria**:
  - [ ] `grep -n "잠재 수강생 전환 예측\|광고 타이밍 추천" frontend/src/pages/Marketing.jsx` returns both core section headings.
  - [ ] `grep -n "현재" frontend/src/pages/Marketing.jsx` returns the current-tier emphasis marker in the timing card section.
  - [ ] `grep -n "바로가기" frontend/src/pages/Marketing.jsx` returns recommendation links where available.
  - [ ] `cd frontend && npm run lint` exits 0.
  - [ ] `cd frontend && npm run build` exits 0.

  **QA Scenarios**:
  ```
  Scenario: Marketing page makes the revenue story obvious
    Tool: Playwright
    Steps: Open /marketing ; wait for data load ; capture the page from top through the first recommendation block.
    Expected: The user can immediately read expected conversions, trend movement, and the recommended ad launch window.
    Evidence: .sisyphus/evidence/task-6-marketing-overview.png

  Scenario: Current demand tier is visually dominant in timing cards
    Tool: Playwright
    Steps: Open /marketing ; inspect the "광고 타이밍 추천" section.
    Expected: One tier card is clearly marked as current and appears visually prioritized over the others.
    Evidence: .sisyphus/evidence/task-6-marketing-tier-cards.png
  ```

  **Commit**: YES | Message: `feat: strengthen marketing decision hierarchy` | Files: `frontend/src/pages/Marketing.jsx`, `frontend/src/index.css`

- [x] 7. Make Operations the clearest “operating response” page

  **What to do**: Update `frontend/src/pages/Operations.jsx` so it expresses the README 운영 효율화 value more concretely. Strengthen the risk summary, make the response path clearer when closure risk is high, and improve schedule-assignment readability so the operator understands the operational consequence of the forecast.
  **Must NOT do**: Do not change scheduling data contracts or convert the time-slot UI into drag-and-drop.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: operational hierarchy, risk framing, and action clarity.
  - Skills: [] - No special skill required.
  - Omitted: [`ultrabrain`] - This is not a logic-heavy redesign problem.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: F1-F4 | Blocked By: 1,2,3

  **References**:
  - Operations page: `frontend/src/pages/Operations.jsx:16-381`.
  - Input form: `frontend/src/pages/Operations.jsx:84-159`.
  - Risk section: `frontend/src/pages/Operations.jsx:181-292`.
  - Cross-page CTA pattern: `frontend/src/pages/Operations.jsx:249-290`.
  - Assignment table: `frontend/src/pages/Operations.jsx:295-360`.
  - README operations pillar: `README.md:18-23`.

  **Acceptance Criteria**:
  - [ ] `grep -n "폐강 위험도 평가\|강사/강의실 배정" frontend/src/pages/Operations.jsx` returns both main sections.
  - [ ] `grep -n "마케팅 분석 바로가기\|시뮬레이터에서 재분석" frontend/src/pages/Operations.jsx` returns the existing response-path CTA copy or improved equivalents.
  - [ ] `grep -n "TIME_SLOT_OPTIONS" frontend/src/pages/Operations.jsx` still returns the assignment selector options contract.
  - [ ] `cd frontend && npm run lint` exits 0.
  - [ ] `cd frontend && npm run build` exits 0.

  **QA Scenarios**:
  ```
  Scenario: High-risk result clearly suggests what to do next
    Tool: Playwright
    Steps: Open /operations ; fill courseName="게임 기획 실전" ; select field="게임 개발" ; choose a date ; click "분석 실행".
    Expected: If high risk is returned, the page highlights the risk and displays strong next-action links to marketing or simulator re-analysis.
    Evidence: .sisyphus/evidence/task-7-operations-risk.png

  Scenario: Assignment table remains usable after hierarchy improvements
    Tool: Playwright
    Steps: In the same /operations result, locate the table under "강사/강의실 배정" ; change one 시간대 select value.
    Expected: The assignment table remains readable and the select interaction still works without layout breakage.
    Evidence: .sisyphus/evidence/task-7-operations-schedule.png
  ```

  **Commit**: YES | Message: `feat: clarify operations response flow` | Files: `frontend/src/pages/Operations.jsx`, `frontend/src/index.css`

- [x] 8. Turn Market into a strategic planning board

  **What to do**: Update `frontend/src/pages/Market.jsx` so it better communicates strategic planning value: who the learners are, how the market is moving, and which start date is most advantageous. Make the top recommendation feel definitive and improve the connection between demographics, competition, and optimal-start outputs.
  **Must NOT do**: Do not change API calls, add maps, or redesign this page into a reporting/export module.

  **Recommended Agent Profile**:
  - Category: `visual-engineering` - Reason: strategic-card hierarchy and chart/result coherence.
  - Skills: [] - No special skill required.
  - Omitted: [`deep`] - The page already has the necessary data relationships; this is presentation work.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: F1-F4 | Blocked By: 1,2,3

  **References**:
  - Market page: `frontend/src/pages/Market.jsx:37-336`.
  - Filter row: `frontend/src/pages/Market.jsx:125-159`.
  - Demographics section: `frontend/src/pages/Market.jsx:170-229`.
  - Competitor section: `frontend/src/pages/Market.jsx:231-279`.
  - Optimal start section: `frontend/src/pages/Market.jsx:281-327`.
  - README strategic pillar: `README.md:32-37`.

  **Acceptance Criteria**:
  - [ ] `grep -n "수강생 인구통계\|경쟁 학원 동향\|최적 개강일 추천" frontend/src/pages/Market.jsx` returns all three strategic sections.
  - [ ] `grep -n "recommended\|추천" frontend/src/pages/Market.jsx frontend/src/components/ScoreBar.jsx` returns the recommendation emphasis path.
  - [ ] `grep -n "PIE_COLORS" frontend/src/pages/Market.jsx` still returns the chart-color configuration, updated to align with token-driven intent if changed.
  - [ ] `cd frontend && npm run lint` exits 0.
  - [ ] `cd frontend && npm run build` exits 0.

  **QA Scenarios**:
  ```
  Scenario: Market page reads like strategy, not raw analytics
    Tool: Playwright
    Steps: Open /market ; wait for load ; capture the full page.
    Expected: The user can clearly understand learner demographics, competitor pressure, and the recommended launch date from one pass through the page.
    Evidence: .sisyphus/evidence/task-8-market-overview.png

  Scenario: Top start-date candidate is unmistakably preferred
    Tool: Playwright
    Steps: In /market, inspect the "최적 개강일 추천" card group ; compare candidate 1 to candidate 2 and 3.
    Expected: Candidate 1 is visually dominant and justified by score/competition/search context.
    Evidence: .sisyphus/evidence/task-8-market-candidates.png
  ```

  **Commit**: YES | Message: `feat: strengthen market strategy storytelling` | Files: `frontend/src/pages/Market.jsx`, `frontend/src/index.css`

## Final Verification Wave (MANDATORY — after ALL implementation tasks)
> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback -> fix -> re-run -> present again -> wait for okay.
- [x] F1. Plan Compliance Audit — oracle
- [x] F2. Code Quality Review — unspecified-high
- [x] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [x] F4. Scope Fidelity Check — deep

## Commit Strategy
- Commit after each numbered task; do not batch multiple pages into a single commit.
- Preferred prefixes: `feat:` for user-facing UX improvements.
- Keep commits scoped to the task files listed above.
- Final verification wave happens after all task commits and before declaring work complete.

## Success Criteria
- First-view product understanding improves: the shell and primary pages visibly express 운영 효율화, 마케팅·매출 연계, 전략 기획.
- Dashboard feels like an action console, not a passive chart page.
- Simulator, Marketing, Operations, and Market each communicate a clear next decision.
- Shared components make loading, empty, error, and severity states feel productized and trustworthy.
- All changes remain within current frontend architecture and pass `lint/build`.
