# Open Questions

## edupulse-full-build - 2026-04-07

### RESOLVED (Iteration 2)

- [x] 공모전 제출 데드라인이 언제인지 확인 필요 -- **해결: 2주 이내 데드라인 확인. MVP-First 전략 채택.**
- [x] 합성 데이터의 규모(기수 수, 기간)를 어느 수준까지 생성할지 결정 필요 -- **해결: 4개 분야 x 최소 8기수 x 2년치. 계절성/트렌드/상관관계 반영.**
- [x] 수요 등급(High/Mid/Low) 임계값을 어떻게 설정할지 결정 필요 -- **해결: 통합 임계값 (모든 분야 동일). High >= 25명, Mid >= 12명, Low < 12명.**
- [x] Frontend를 Phase 3-4와 병렬로 진행할 인력이 있는지 -- **해결: 2인 팀 확정. Person A(Backend/Data/Model), Person B(Frontend + API 통합).**
- [x] PostgreSQL을 로컬 개발에서도 사용할지, SQLite로 대체할지 -- **해결: PostgreSQL via Docker (docker-compose.dev.yml). 서버와 동일 환경 유지.**
- [x] MLflow 통합을 Phase 3에 포함할지 Phase 6으로 미룰지 -- **해결: 2주 데드라인으로 제외. 공모전 이후 장기 과제로 연기.**
- [x] 네이버 API 키와 Google API 접근 권한이 확보되었는지 -- **해결: Naver DataLab 키 확보 (무료). Google Trends는 pytrends 사용 (키 불필요). 수집 모듈은 MVP 이후 우선순위.**

### Architect/Critic 피드백에서 발생한 추가 질문 (모두 해결됨)

- [x] requirements.txt 환경 분리 필요 -- **해결: 3-파일 분리 (requirements.txt, requirements-dev.txt, requirements-server.txt). boto3/mlflow 제거.**
- [x] Droplet 2GB에서 3개 모델 동시 서빙 가능한지 -- **해결: 불가능. XGBoost 단일 모델 서빙 전략 채택. 메모리 예산 ~800MB 사용, ~1200MB 여유.**
- [x] 기존 main.py -> api/main.py 마이그레이션 계획 -- **해결: api/main.py 신규 생성, 기존 main.py 삭제 또는 진입점 변환. 실행 커맨드 uvicorn api.main:app으로 변경.**
- [x] pydantic-settings 누락 -- **해결: requirements.txt에 pydantic-settings>=2.3.0 추가.**
- [x] edupulse/models/ (ORM) vs model/ (ML) 명명 혼동 -- **해결: ORM 디렉토리를 edupulse/db_models/로 변경하여 model/ (ML)과 명확히 분리.**
- [x] Frontend 기술 선택 미지정 -- **해결: Vite + React 18 + Recharts + npm. CSS Modules 또는 Tailwind CSS.**
- [x] .gitignore 불완전 -- **해결: Python + Node.js + data/ + model artifacts + OS 파일 + Docker 패턴 추가.**
- [x] README.md S3 vs scp 불일치 -- **해결: S3 참조 전부 제거, scp로 통일. Phase 4 수락 기준에 grep 검증 포함.**
- [x] cron vs APScheduler -- **해결: Droplet에서 시스템 cron 사용. retrain.py는 standalone 스크립트로 구현.**
- [x] MAPE 수락 기준 미구체화 -- **해결: 합성 데이터 기준 MAPE < 30%. 실데이터 전환 시 < 25% 목표.**
- [x] 테스트 전략 부재 -- **해결: Unit(전처리/모델utils) + Integration(API) + E2E Smoke(Docker) 3단계 전략 수립.**

## lstm-data-improvement - 2026-04-08

- [ ] Augmentation hyperparameters (jitter_std=0.02, scale_range=0.95-1.05, n_augments=2) are initial guesses — May need tuning based on MAPE results after implementation
- [ ] If LSTM MAPE remains above 25% after this change, next steps need to be decided: more augmentation types (time-warping, window slicing) vs. architectural changes (attention, bidirectional)
- [ ] The `_compute_trend()` function hardcodes year-based transitions — If the project later needs to generate data for years beyond 2025, the trend function will need extension
- [ ] Existing saved model weights under `model/saved/lstm/` will be invalidated by the data change — Retraining must happen after data regeneration

## search-volume-collectors - 2026-04-08

- [ ] Naver DataLab daily quota limit exact number needs verification — Plan assumes 1000/day but actual limit may differ per API key tier. Affects quota.py default and config.py setting.
- [ ] Starter keyword list (FIELD_KEYWORDS) is an initial best guess — May need refinement based on actual Naver DataLab search volume results. Low-volume keywords should be replaced after first collection run.
- [ ] Naver API response ratio values are relative (0-100) not absolute — Summing across keywords produces a composite score, not actual search counts. Document this in the output so downstream consumers understand the scale.
- [ ] When transitioning from synthetic to real data, the search_volume scale will change significantly — Models trained on synthetic data will need retraining after switching to real Naver data. Plan a retraining step.
- [ ] Google Trends rate limiting behavior is unpredictable — pytrends uses unofficial endpoints. If Google blocks aggressively, the cache-only strategy means no Google data at all, which is acceptable but worth noting.

## expand-synthetic-data-generators - 2026-04-09

### Resolved in v2 revision (Architect/Critic review)

- [x] Feature count arithmetic error (plan said 10+7=17 but actually 10+5+7=22) — **Resolved: Corrected to 22 total features with explicit reconciliation table.**
- [x] test_augment_sequences will break due to hardcoded n_feat=10 — **Resolved: Step 7 adds fix to use len(FEATURE_COLUMNS).**
- [x] All saved models become incompatible after FEATURE_COLUMNS change — **Resolved: Step 6 adds model migration (version bump to v2, retrain all models).**
- [x] Forward-fill corruption of binary flags — **Resolved: Step 3 adds binary flag zero-fill after merge, separate from continuous column ffill.**
- [x] Positional index lists are fragile — **Resolved: Step 4c replaces hardcoded indices with name-based derivation from _PROTECTED_NAMES set.**
- [x] _build_features() in predict.py underspecified — **Resolved: Step 5 has full pseudo-code for all 12 new feature loads including seasonal_events (date-only lookup) and age_group_diversity (Shannon entropy computation).**
- [x] No test creation step — **Resolved: Step 7 added with test_generators.py (10+ tests) and test_augment_sequences fix.**
- [x] generate_seasonal_events() has no seed parameter — **Resolved: All generators accept seed for API consistency, even deterministic ones.**
- [x] competitor_avg_price needs max(0) guard — **Resolved: Step 2b formula includes max(0, raw_price) clamp.**
- [x] weeks_to_exam computation not specified — **Resolved: Step 2a includes _weeks_to_next_exam() pseudo-code with 12-month forward search and cap at 26.**
- [x] No Risks section in the plan — **Resolved: Risks table added with 5 identified risks and mitigations.**
- [x] Vectorize Shannon entropy — **Resolved: Step 4a uses numpy vectorized operations instead of apply(lambda).**
- [x] Synthetic correlation inflation not documented — **Resolved: Step 9c adds explicit warning section; each generator also gets a docstring warning.**

### Open (from v1, still applicable)

- [ ] Should `student_profiles.csv` include individual ratio columns (age_20s_ratio, etc.) or only the derived entropy feature? — Individual ratios are currently generated for transparency and real-data replacement, but only entropy is used as a model feature. Keeping both means extra columns in the CSV that are not directly consumed by the model.
- [ ] Should `seasonal_events.csv` be field-specific or global? — Current plan uses global (no field column) since vacation/exam seasons apply across all fields. However, some events (cert exams) are already field-specific in a separate CSV. Confirm this split is acceptable.
- [ ] What should `competitor_avg_price` units be? — Plan uses KRW (won) with values like 400,000-600,000. This creates large numeric values that may need scaling in the model. Alternative: use 만원 units (40-60) for cleaner feature values.
- [ ] Are the cert exam month mappings realistic enough? — Plan uses approximate Korean national cert exam months. Real schedules vary year to year. The synthetic generator uses fixed months, which is a simplification.

### New (from v2 revision)

- [ ] Should v1 model files be deleted after v2 retraining succeeds, or kept permanently as archive? — Keeping them wastes disk but provides rollback. Plan currently says "preserve" but no cleanup policy is defined.
- [ ] After real data replaces synthetic generators, should feature selection/PCA be applied to reduce from 22 features? — With small real datasets, 22 features may cause overfitting. Need to decide threshold for feature pruning.
- [ ] Should predict_demand() support both v1 (10-feature) and v2 (22-feature) models simultaneously? — Current plan changes default to v2 but callers could still request v1, which would fail with dimension mismatch. Consider adding a version compatibility check.
