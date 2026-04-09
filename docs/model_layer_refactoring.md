# 모델 레이어 리팩토링 변경 내역

모델 레이어의 구조적 문제 8가지 중 5가지를 수정한 작업 기록.
기존 ModelMetadata 시스템(10/12 테스트 통과) 위에 진행되었으며,
Prophet `stan_backend` 2개 실패는 기존 의존성 버그로 이 작업과 무관하다.

---

## 1. 앙상블 서브모델 thread lock 우회 방지

**커밋**: `3468113` — `fix: 앙상블 서브모델 thread lock 우회 방지`

### 문제

`EnsembleForecaster._predict()`가 서브모델의 `model._predict(features)`를 직접 호출하고 있었다.
`BaseForecaster`는 `predict()` 메서드 안에서 `threading.Lock`을 잡고 `_predict()`를 호출하는 구조인데,
앙상블이 `_predict()`를 직접 호출하면 이 lock을 완전히 우회하게 된다.
멀티스레드 환경(FastAPI 등)에서 서브모델 내부 상태가 동시 접근에 의해 손상될 수 있는 버그였다.

### 변경

| 파일 | 내용 |
|---|---|
| `edupulse/model/ensemble.py` | line 143: `model._predict(features)` → `model.predict(features)` |
| `tests/test_model.py` | `test_ensemble_uses_public_predict` 추가 — mock으로 public `predict()` 호출 검증 |

### 영향

- 서브모델 예측 시 thread lock이 정상 동작하여 동시 요청 안전성 확보
- 기존 테스트 전부 통과 유지

---

## 2. 피처 컬럼 누락 시 경고 로그 추가

**커밋**: `a147359` — `feat: 피처 컬럼 누락 시 경고 로그 추가`

### 문제

XGBoost, LSTM, Prophet 모델 모두 `[c for c in FEATURE_COLUMNS if c in df.columns]` 패턴으로
누락된 피처 컬럼을 조용히 무시하고 있었다.
학습/예측 데이터에 컬럼이 빠져도 에러 없이 진행되므로,
성능 저하의 원인을 추적하기 어려웠다.

### 변경

| 파일 | 내용 |
|---|---|
| `edupulse/model/base.py` | `validate_feature_columns()` 헬퍼 함수 추가 — 누락 시 `warnings.warn()` + `logger.warning()` |
| `edupulse/model/xgboost_model.py` | 3곳 (`train`, `_predict`, `evaluate`) 교체 |
| `edupulse/model/lstm_model.py` | 3곳 (`_build_sequences_per_field`, `_prepare_arrays`, `_predict`) 교체 |
| `edupulse/model/prophet_model.py` | 4곳 (`_to_prophet_df`, `train` x2, `evaluate` x2) 교체 |
| `tests/test_model.py` | `test_missing_columns_warns` 추가 — 누락 시 경고 발생 및 전체 존재 시 경고 없음 검증 |

### 영향

- 피처 컬럼이 누락되면 로그와 경고로 즉시 확인 가능
- 기존 동작(누락 컬럼 제외 후 진행)은 그대로 유지하여 하위 호환성 보존

---

## 3. 모델 로딩 이중 캐시 통합 및 버전 불일치 해소

**커밋**: `2293182` — `refactor: 모델 로딩 이중 캐시 통합 및 버전 불일치 해소`

### 문제

모델 로딩 경로가 두 곳에 존재했다:

1. `api/dependencies.py`: `MODEL_REGISTRY` dict + `load_models()` — version=1 하드코딩
2. `model/predict.py`: `_model_cache` dict + `_load_model()` — version=2 기본값

동일 요청이 코드 경로에 따라 다른 캐시, 다른 모델 버전을 사용할 수 있는 구조적 결함이었다.
또한 `_build_features`와 `_load_model`이 private 함수(`_` prefix)인데 외부 모듈에서 직접 import하고 있었다.

### 변경

| 파일 | 내용 |
|---|---|
| `edupulse/model/predict.py` | `_load_model` → `load_model`, `_build_features` → `build_features` public 전환. `MODEL_VERSION = 1` 상수 추가. `clear_model_cache()` 추가 |
| `edupulse/api/dependencies.py` | 자체 `MODEL_REGISTRY` 제거, `predict.load_model()`에 위임. `get_loaded_model_names()` 추가 |
| `edupulse/api/routers/demand.py` | import 경로 `_build_features` → `build_features` |
| `edupulse/api/routers/health.py` | `MODEL_REGISTRY` → `get_loaded_model_names()` |
| `tests/conftest.py` | `MODEL_REGISTRY` → `_model_cache` 직접 참조 |
| `tests/test_demand.py` | 동일 변경 |

### 영향

- 모델 캐시가 `predict._model_cache` 한 곳으로 통합되어 버전 불일치 불가
- `MODEL_VERSION` 상수로 버전 관리 단일화
- API와 직접 호출 경로가 동일한 캐시를 공유

---

## 4. LSTM 평가 메서드 중복 코드 추출

**커밋**: `77bf150` — `refactor: LSTM 평가 메서드 중복 코드 추출`

### 문제

`LSTMForecaster._evaluate_single()` (약 75줄)과 `_evaluate_per_field()` (약 75줄)의
K-Fold 학습/평가 루프가 거의 동일한 코드를 복사-붙여넣기하고 있었다.
한쪽을 수정하면 다른 쪽도 동일하게 수정해야 하는 유지보수 리스크가 있었다.

### 변경

| 파일 | 내용 |
|---|---|
| `edupulse/model/lstm_model.py` | `_evaluate_fold(X_raw, y_raw, n_splits)` 헬퍼 추출. `_evaluate_single`과 `_evaluate_per_field`를 각 5줄 이하로 단순화. 총 81줄 제거, 28줄 추가 |

### 영향

- 평가 로직 변경 시 한 곳만 수정하면 됨
- 동작은 완전히 동일 (동일 결과 보장)

---

## 5. course_name 필드 미사용 상태 문서화

**커밋**: `58f26de` — `docs: course_name 필드 미사용 상태 문서화`

### 문제

`DemandRequest.course_name`과 `build_features(course_name, ...)`의 `course_name` 파라미터가
실제 모델 예측에 전혀 사용되지 않는데, 이 사실이 코드에서 드러나지 않았다.
API 사용자나 새 개발자가 이 필드가 예측에 영향을 준다고 오해할 수 있었다.

### 변경

| 파일 | 내용 |
|---|---|
| `edupulse/api/schemas/demand.py` | `course_name` 필드에 미사용 상태 주석 추가 |
| `edupulse/model/predict.py` | `build_features()` docstring에 미사용 상태 명시 |

### 영향

- 코드 변경 없음 (주석만 추가)
- 향후 과정별 세분화 시 활용 예정임을 명시

---

## 범위 밖 (별도 브랜치 대상)

아래 항목은 이번 작업에서 제외했으며, 별도 브랜치에서 진행해야 한다:

- `FEATURE_COLUMNS`를 `constants.py`로 이동 — 영향 파일이 많아 별도 리팩토링 필요
- Prophet `stan_backend` 호환성 수정 — 의존성 업그레이드 필요
- 모델 버전 자동 감지 (`saved/` 디렉토리 스캔) — 설계 결정 필요

---

## 테스트 결과

```
22 passed, 2 failed (Prophet stan_backend 기존 버그)
```

- 기존 10개 테스트 + 새 테스트 2개 (`test_missing_columns_warns`, `test_ensemble_uses_public_predict`) = 12개 모델 테스트
- API/health 테스트 10개 전부 통과
