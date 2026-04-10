## Handoff: Phase 2 → Phase 3+4 (병렬 진행)
- **Decided**: Phase 3 대부분 Phase 1에서 선행 구현됨. demand.py 수정 + 테스트만 남음. Phase 3+4 병렬 진행.
- **Completed**: 합성 데이터 64행 (4분야x16기수), 전처리 (cleaner/transformer/merger), XGBoost v1 (MAPE 26.6%), 10/10 tests pass
- **Integration gap**: demand.py가 `model.predict_from_request()` 호출하나 이 메서드는 BaseForecaster에 없음. `edupulse.model.predict.predict_demand()` 또는 직접 feature 빌드 후 `model.predict(df)` 사용해야 함.
- **Files to fix**: edupulse/api/routers/demand.py (predict_from_request → predict_demand 또는 _build_features+predict)
- **Files to create**: tests/test_demand.py, Dockerfile, docker-compose.yml, .dockerignore, edupulse/model/retrain.py, scripts/deploy.sh
- **Risks**: docker-compose.dev.yml 이미 존재 — 충돌 주의. FakeForecaster에 predict_from_request 없음 (conftest.py도 수정 필요할 수 있음)
