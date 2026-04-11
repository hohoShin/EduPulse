
- Standardized Task 2 trust surfaces by moving component styling toward reusable CSS classes in `index.css` while preserving existing component props and page call sites.
- Treated the visual-engineering delegation path as infrastructure-blocked after repeated 403 permission failures and used a narrow local implementation path to keep the active plan moving.
- Kept Task 3 entirely at the shared-component layer (`DemandChart`, `RiskGauge`, `ScoreBar`, `index.css`) so Dashboard, Market, and Operations gained stronger semantics without forcing page-level refactors.
- Normalized chart and score visuals onto existing semantic tokens instead of introducing separate chart palettes, which keeps later page-level UX tasks aligned with the current design system.
- Decided to reuse the existing `PILLAR_COPY` and CSS classes for the first fold of the Dashboard to communicate product outcomes without altering backend adapters, state shapes, or prop contracts.

### Simulator Redesign
- Added explicit styling (`brief-header`, `brief-section`, etc.) to visually group simulation outcomes.
- Emphasized actionable items by changing the link styles to primary buttons at the end of the simulation brief, guiding users explicitly to either Operations or Marketing planning.
- Added explicit "명 예상" unit labels to make numerical values clearer.
- Decided to preserve `getLeadConversion` and `getMarketingTiming` contracts while completely reorganizing their presentation.
- Used `dashboard-priority-panel` and `dashboard-priority-card` in `Marketing.jsx` to give the conversion prediction a clear visual hierarchy.
- Replaced the simple mapped timing list with styled cards to emphasize the current tier's ad launch parameters.
- **Marketing Timing Card Fallback**: If `leadData.current_demand_tier` is null or missing, we fall back to highlighting the first item in the `timingData` array (or 'mid' if empty) so that the UI always deterministically highlights exactly one action card, ensuring the "Cockpit" instruction-set layout never fails silently.

### Task 7: Operations UX Improvements
* Combined the separate "Risk Assessment" and "Instructor Assignment" cards into a single cohesive "Response Brief" card to represent a unified action plan for the operator.
* Replaced the standard 3-metric grid for risk with a prominent Risk Gauge alongside a textual, dynamic narrative summary that explains exactly what the forecast means.
* Upgraded the schedule assignment table UI to use subtle backgrounds and inline pill styles for the instructor slots, improving scanability without altering the underlying `TIME_SLOT_OPTIONS` contract or adding heavy drag-and-drop mechanics.
- Transformed Market.jsx to use a 3-step narrative flow (Demographics -> Competitors -> Optimal Start) instead of isolated vertical sections.
- Reused `brief-metric-card` and `dashboard-priority-card` CSS classes to give the layout the same aesthetic as the other operational dashboards.
- Refactored the `top_candidates[0]` into a highlighted hero card with explicit "Reason for Recommendation" text tying back to the target demographics and competitor count data.

- [2026-04-11 11:42] Kept final-wave fixes narrowly scoped: `AlertPanel` now prefers `actionUrl` but falls back to a small existing-label route map, `Simulator.jsx` only changed visible framing copy/empty-state promise, and Market switched the `RiskGauge` compatibility token from `mid` to `medium` without touching `PIE_COLORS`.
