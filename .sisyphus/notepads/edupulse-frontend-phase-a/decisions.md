# Decisions
- Translated user-facing strings across Dashboard, Simulator, components, and fixtures.
- Kept mock/demo surface explicit, but translated it to Korean (예: "데모 환경", "가상의 데이터").
- Tier labels are displayed in Korean but underlying structure logic was kept unchanged.
- Mapped internal state values like 'success' or 'coding' or 'high' to Korean UI labels in Dashboard, Simulator, and TierBadge so that internal state flow is completely untouched.
- Repaired fixture strings in `systemStatusStates.js` that were still English.
