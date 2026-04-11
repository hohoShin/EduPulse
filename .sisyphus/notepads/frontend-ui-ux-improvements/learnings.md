
- Task 2 reinforced that `StatusPanel`, `AlertPanel`, and `TierBadge` are shared across Dashboard, Simulator, Marketing, Market, Operations, and App, so visual trust-state changes propagate broadly and must preserve prop compatibility.
- Repo-wide lint blockers were not isolated to the active shared-component files; `mockAdapter`, `realAdapter`, and `Marketing.jsx` needed minimal cleanup before any plan task could pass verification again.
- Task 3 showed that the chart/gauge layer had most of its remaining UX debt in explanatory copy and token drift rather than data shape problems; preserving existing props was enough once the legend/supporting text became more explicit.
- Browser QA for Task 3 was reliable only with Playwright route mocking because the normal dev runtime still defaults some paths to real API calls; mocked responses were sufficient to verify the decision-surface copy and score emphasis.
- Task 4 confirmed that reorganizing Dashboard into a command-center format was achievable by simply rearranging the existing state and data structures into prioritized folds (current demand signal, urgent risk, next action).

### Simulator Page Strategy
- Emphasized a "brief" structure over just a dashboard output.
- Grouping metrics into strategic categories (Predictions, Operations, Marketing) directly serves the goal of turning simple tool inputs into actionable business plans.
- Task 6 reinforced the pattern of reframing existing charts and values into explicit action surfaces by using the dashboard priority grid classes.
- Presenting the current demand tier actively (via box-shadow, opacity differences, and a clear "현재 수요" label) shifts the page from a generic data dump into a clear instruction set.

### Task 7: Operations UX Improvements
* Operations UX is much more impactful when framed as a "Response Brief" (ACTION REQUIRED vs ON TRACK) rather than two detached data panels.
* Using narrative text to explain the mathematical shortfall (e.g., "최소 개강 인원 15명에 3명 미달합니다") makes the dashboard feel like an assistant rather than just a reporting tool.
- By framing raw analytics blocks as sequential steps (e.g., Step 1. 타겟 분석, Step 2. 경쟁 환경, Step 3. 전략적 결론), a page changes from a generic dashboard to a strategic planning board.
- The use of `dashboard-priority-card--signal` and distinct visual hierarchy (size, border weight, explicit justification) makes the primary recommendation feel definitive compared to alternative options.

- [2026-04-11 11:42] Final-wave remediation confirmed that pages consuming adapter entrypoints must branch on returned `UIState.state`, because the real adapter frequently resolves error payloads instead of throwing; shared action surfaces also need a route fallback when fixtures only provide `actionLabel` text.
