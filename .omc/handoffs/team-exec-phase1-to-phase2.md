## Handoff: Phase 1 (Foundation) → Phase 2 (Data + Model)
- **Decided**: edupulse/ 통합 패키지 완성, sync DB + Alembic, constants.py 단일 소스, FakeForecaster 테스트 패턴
- **Completed**: pyproject.toml, requirements*.txt, config.py, database.py, constants.py, db_models/*, alembic/, api/ scaffolding (main, routers, schemas, middleware), tests/conftest.py + test_health.py (3/3 pass)
- **Note**: worker-3가 Phase 1에서 demand/schedule/marketing 라우터 + 스키마를 미리 구현함 (Phase 3 범위). Phase 2에서는 이 파일 수정 불필요 — model/predict.py 구현 시 API dependencies와 연결만 하면 됨.
- **Existing files to UPDATE (not recreate)**: edupulse/model/base.py (PredictionResult already defined), edupulse/model/utils.py (get_device + classify_demand re-export)
- **Risks**: XGBoost MAPE <30% 목표 — 합성 데이터 품질에 의존. pandas/numpy는 requirements.txt에 이미 포함.
- **Remaining**: Phase 2 전체 (합성 데이터, 전처리, XGBoost 학습), Phase 3 (API 연결), Phase 4 (Docker)
