# EduPulse Frontend Phases & Activation Path

This document outlines the phased development strategy for the EduPulse frontend, distinguishing between the current Phase A implementation and future activation phases (B, C, and D).

---

## Phase A: Foundation & Mock-First Scaffold (Current)

**Status:** COMPLETED / IN REVIEW

### Objective
Establish a verified, mock-first frontend architecture that demonstrates core user surfaces (Dashboard and Simulator) using local fixtures and a robust adapter pattern.

### Current Reality
- **Framework:** React + Vite + Recharts scaffold.
- **Dashboard:** A curated demo surface displaying summary metrics (Enrollment, Active Courses, Market Demand), a time-series demand chart, and system-generated alerts.
- **Simulator:** A mock-first interaction flow where users can simulate course demand. It supports specific "magic string" triggers to demonstrate different UI states.
- **Architecture:** Adapter pattern implementation (`mockAdapter.js`) that wraps fixtures into `UIState` objects, providing a "backend-ready" interface for components.

### Mock Behavior (Operator Guidance)
Operators can exercise different UI flows in the **Simulator** using the following course name triggers:
- **Default Success**: Any standard course name returns a high-demand success state.
- **Low Demand Warning**: Including the word `low` in the course name (e.g., "Python low") triggers a "Low" tier result with specific operational warnings.
- **Validation/System Error**: Including the word `error` in the course name triggers the simulated error state.

---

## Phase B: Contract Hardening

### Objective
Freeze request/response contracts, normalize error shapes, and decide canonical adapter interfaces to ensure the frontend can transition safely to live data.

### Unlock Conditions
- [ ] Phase A UI structure and demo content are accepted.
- [ ] Canonical adapter interfaces for demand, schedule, marketing, and health are finalized.

### Backend Prerequisites
- Confirmed exact API response examples for demand, schedule, marketing, health.
- Predictable 422/5xx behavior definitions.

### Non-Goals
- No large dashboard aggregation work yet.
- Real backend connectivity is not required for contract finalization (can use updated mocks).

---

## Phase C: Real Integration

### Objective
Connect the Simulator and other core components to real backend APIs, replacing mock logic with live network requests via the `realAdapter`.

### Unlock Conditions
- [ ] Phase B contracts are finalized and implemented in the backend.
- [ ] Stable backend availability and agreed error semantics.

### Backend Prerequisites
- Working demand/schedule/marketing endpoints in the live API server.
- Agreed health semantics for service status monitoring.

### Non-Goals
- No dashboard analytics expansion unless supported by new aggregation APIs.

---

## Phase D: Dashboard/Data Expansion

### Objective
Upgrade the Dashboard from a curated demo surface to a real-time data surface powered by dedicated aggregation, list, and trend APIs.

### Unlock Conditions
- [ ] Backend ships dashboard-specific summary and trend endpoints.
- [ ] Multi-scenario simulation capabilities are ready in the backend.

### Backend Prerequisites
- New dashboard-focused APIs and KPI definitions.
- Implementation of a simulation engine for hypothetical scenarios.

### Non-Goals
- Do not retrofit the mock dashboard without verified data contracts from new APIs.


---

## Operator Guidance for Phase A Review

To review the current Phase A state:

1. **Start the Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. **Access the Dashboard:**
   Navigate to `http://localhost:5173/` to see the curated demo surface (Metrics, Chart, Alerts).
3. **Run a Simulation:**
   Navigate to `http://localhost:5173/simulator` and enter a course name.
   - Use "New Course" for success.
   - Use "Experimental low" to see low-tier handling.
   - Use "Broken error" to see error handling.
4. **Verify Stability:**
   Check the console for clean execution. The system uses local fixtures via `mockAdapter.js` and does not attempt network requests to `localhost:8000` in Phase A.

