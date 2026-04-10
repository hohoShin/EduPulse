# Issues & Scope-Creep Failures

## Verification Failure 1: Scope Creep (Initial Implementation)

**What Happened:**
- Task 1 should create ONLY `frontend/` and append-only notepad updates
- Initial implementation accidentally modified backend Python files (edupulse/model/*.py, edupulse/preprocessing/*.py, tests/conftest.py)
- Also created out-of-scope generator files (events_generator.py, internal_generator.py, test_generators.py)
- Modified root-level documentation (README.md, docs/合成_데이터_生成_ガイド.md)

**Root Cause:**
- Ambiguous task scope led to bundling unrelated work into Task 1
- Attempted to implement synthetic data generators (backend Task 3) in same session

**Resolution:**
- Reverted all backend/docs modifications via `git restore`
- Removed out-of-scope generator files
- Confirmed working tree now contains ONLY `frontend/` and `.sisyphus/` (untracked)

## Verification Failure 2: React Version Mismatch

**What Happened:**
- `frontend/package.json` initially specified React ^19.2.4 instead of React 18
- Task 1 explicitly requires React 18 per requirements

**Root Cause:**
- Vite scaffolding auto-selected latest React version
- Failed to validate version against Task 1 spec

**Resolution:**
- Downgraded React to ^18.3.1
- Updated @types/react to ^18.3.3
- Reinstalled dependencies to regenerate package-lock.json
- Verified build passes with React 18 (smaller bundle: 45.84kB gzipped vs 60.09kB)
