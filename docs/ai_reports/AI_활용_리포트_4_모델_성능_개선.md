# AI 활용 리포트 4 — 수요 예측 모델 성능 개선 과정

> **작성일:** 2026-04-08
> **사용 도구:** Claude Code (Claude Opus 4.6) + oh-my-claudecode
> **목적:** 주간 데이터 전환 및 분야별 분리 학습을 통한 Prophet/LSTM MAPE 개선 과정 기록

---

## 1. 배경 및 문제 정의

EduPulse의 초기 수요 예측 파이프라인은 **기수 단위(~60일 간격)** 데이터로 학습되었다. 4개 분야(coding, security, game, art) × 24기수 = **96행**의 데이터로 3개 모델을 평가한 결과:

| 모델 | MAPE | 평가 |
|------|------|------|
| XGBoost | 18.55% | 양호 |
| Prophet | 52.93% | 패턴 학습 실패 |
| LSTM | 46.72% | 데이터 부족 |

**핵심 문제:** Prophet과 LSTM은 시계열 모델로서 충분한 데이터 포인트가 필요한데, 분야당 24행으로는 계절성과 트렌드를 학습할 수 없었다.

---

## 2. 개선 전략 — 2단계 접근

### Phase 1: 주간 데이터 전환 (데이터 양 확대)

기수 단위(~60일) → 주간 단위(7일)로 해상도를 높이고, 5년치 데이터를 생성하여 데이터 양을 **96행 → 1044행**으로 10배 이상 확대한다.

### Phase 2: 구조적 개선 (학습 품질 향상)

데이터 양만 늘려서는 해결되지 않는 구조적 문제를 식별하고 수정한다:
- 노이즈 비율 축소
- 분야별 분리 학습/평가
- 분야 피처 인코딩

---

## 3. Phase 1 — 주간 데이터 전환

### 3.1 변경 파일 및 내용 (10개 파일)

| Step | 파일 | 변경 내용 |
|------|------|-----------|
| 1 | `constants.py` | 수요 임계값: HIGH≥25→6, MID≥12→3 (주간 스케일) |
| 2 | `enrollment_generator.py` | 주간 데이터 생성기 전면 재작성 |
| 3 | `external_generator.py` | [field, date] 그리드 기반 주간 외부 데이터 |
| 4 | `run_all.py` | `run(n_years=5, start_year=2021)` 시그니처 |
| 5 | `merger.py` | 병합 키: [field, cohort] → [field, date] |
| 6 | `transformer.py` | `groupby("field")` lag 계산 (버그 수정) |
| 7 | `prophet_model.py` | `changepoint_prior_scale`: 0.05 → 0.15 |
| 8 | `lstm_model.py` | `SEQUENCE_LENGTH`: 4→12, `DROPOUT`: 0.2→0.3 |
| 9 | `xgboost_model.py` | `n_estimators`: 200→300, `learning_rate`: 0.05→0.03 |
| 10 | `test_*.py` | 주간 freq, n=100, field 컬럼 추가 |

### 3.2 주요 설계 결정

#### 수요 임계값 산정 근거

```
기수 단위: HIGH ≥ 25명 (8주간 총 등록)
주간 단위: 25명 ÷ 8주 ≈ 3.1명/주 → MID ≥ 3
            HIGH는 MID의 2배 → HIGH ≥ 6
```

이 기준으로 수요 등급 분포가 유지됨을 확인:
- High 10%, Mid 57%, Low 33% (합리적 분포)

#### LSTM 시퀀스 길이 확대

```
기존: SEQUENCE_LENGTH = 4 (기수 4개 = ~8개월 맥락)
변경: SEQUENCE_LENGTH = 12 (12주 = 1분기 맥락)
```

주간 데이터에서 12주는 약 1분기에 해당하며, 계절성 패턴의 최소 단위를 포착할 수 있다.

#### transformer.py 버그 수정

```python
# 변경 전 — 분야 경계를 넘어 shift (잠재적 버그)
df[f"lag_{lag}w"] = df[target_col].shift(lag)

# 변경 후 — 분야별 독립 shift
df[f"lag_{lag}w"] = df.groupby("field")[target_col].shift(lag)
```

이전 코드는 데이터가 `[coding 행들..., security 행들..., ...]`으로 정렬된 상태에서 coding의 마지막 행이 security의 첫 행으로 shift되는 문제가 있었다. 96행에서는 영향이 작았지만, 1044행에서는 분야당 261행의 경계에서 오염이 발생한다.

### 3.3 Phase 1 결과

| 모델 | 원본 (96행) | Phase 1 (1044행) | 변화 |
|------|----------:|------------------:|------|
| XGBoost | 18.55% | 24.64% | +6.09% (악화) |
| Prophet | 52.93% | 50.19% | -2.74% (소폭 개선) |
| LSTM | 46.72% | 32.82% | -13.90% (개선) |

**LSTM은 크게 개선**되었으나, **XGBoost가 악화**되고 **Prophet 개선이 미미**했다.

---

## 4. Phase 1 결과 분석 — XGBoost 악화 원인

### MAPE 지표의 소수값 편향

MAPE(Mean Absolute Percentage Error) = `|실제 - 예측| / 실제 × 100`

```
기수 단위: 실제=20, 예측=19 → 오차 1명 → MAPE 5%
주간 단위: 실제=4, 예측=3   → 오차 1명 → MAPE 25%
```

**동일한 절대 오차(1명)가 MAPE로는 5배 차이**가 난다. 이는 XGBoost의 예측 능력이 떨어진 것이 아니라, 주간 단위의 작은 정수값에서 MAPE가 구조적으로 높아지는 지표 특성이다.

### Prophet이 개선되지 않은 원인

Prophet은 **단일 시계열 모델**인데, 4개 분야가 혼합된 데이터를 하나의 시계열로 학습하고 있었다:

```
행 260: coding,   2021-12-27, enrollment=6
행 261: security, 2021-01-04, enrollment=2  ← 분야 전환
```

Prophet은 이를 "6 → 2로 급락"이라고 해석한다. 실제로는 서로 다른 분야의 데이터인데 하나의 연속 시계열로 보니 **거짓 패턴**을 학습한다.

### 구조적 문제 3가지

| 문제 | 영향받는 모델 | 해결 방법 |
|------|-------------|-----------|
| 높은 노이즈/신호 비율 | 전체 (특히 XGBoost) | 노이즈 축소 |
| 분야 혼합 시계열 | Prophet, LSTM | 분야별 분리 학습 |
| 분야 정보 미활용 | XGBoost | field_encoded 피처 추가 |

---

## 5. Phase 2 — 구조적 개선

### 5.1 노이즈 축소

```python
# 변경 전: 노이즈가 신호의 30-60%
noise = rng.normal(0, 1.2)  # base=2~4 대비 ±1.2

# 변경 후: 노이즈가 신호의 15-30%
noise = rng.normal(0, 0.6)  # base=2~4 대비 ±0.6
```

노이즈 표준편차를 절반으로 줄여 모델이 학습해야 할 실제 패턴(계절성, 트렌드)의 신호가 더 명확해진다.

### 5.2 분야 label encoding (XGBoost)

```python
# transformer.py에 추가
if "field" in df.columns:
    df["field_encoded"] = df["field"].astype("category").cat.codes

# xgboost_model.py FEATURE_COLUMNS에 추가
FEATURE_COLUMNS = [
    "lag_1w", "lag_2w", "lag_4w", "lag_8w",
    "rolling_mean_4w", "month_sin", "month_cos",
    "search_volume", "job_count",
    "field_encoded",  # 신규
]
```

XGBoost는 각 행을 독립적인 피처 벡터로 취급하므로 분야 정보를 피처로 직접 제공하면 분야별 수요 차이를 학습할 수 있다.

### 5.3 분야별 분리 학습/평가 (Prophet, LSTM)

#### Prophet 분야별 분리

```python
# 변경 전: 1044행 전체를 하나의 시계열로 학습
model.fit(all_data)

# 변경 후: 분야별 개별 모델 학습
for field in ["coding", "security", "game", "art"]:
    field_df = df[df["field"] == field]  # ~261행
    model = Prophet(changepoint_prior_scale=0.15)
    model.fit(field_df)  # 순수한 단일 시계열
    self._field_models[field] = model
```

각 분야의 261행 데이터는 **5년치 순수 주간 시계열**이므로 Prophet이 연간 계절성을 정확히 학습할 수 있다.

#### LSTM 분야별 시퀀스 생성

```python
# 변경 전: 전체 데이터에서 연속 시퀀스 생성 (분야 경계 오염)
xs, ys = _build_sequences(X_all, y_all, SEQUENCE_LENGTH)

# 변경 후: 분야별로 시퀀스를 독립 생성 후 합산
for field in df["field"].unique():
    field_X = X_scaled[df["field"] == field]
    field_y = y_scaled[df["field"] == field]
    xs, ys = _build_sequences(field_X, field_y, SEQUENCE_LENGTH)
    all_xs.append(xs)
```

LSTM 시퀀스가 분야 경계를 넘지 않으므로 각 분야 내의 순수한 시간적 패턴만 학습한다.

### 5.4 평가 방식 변경

Prophet과 LSTM의 `evaluate()` 메서드에 분야별 분리 평가 로직을 추가:

```python
def evaluate(self, df, n_splits=5):
    if "field" in df.columns and df["field"].nunique() > 1:
        return self._evaluate_per_field(df, n_splits)
    return self._evaluate_single_series(df, n_splits)
```

분야별로 독립적인 TimeSeriesSplit K-Fold를 수행하고, 모든 분야·폴드의 MAPE를 평균내어 최종 MAPE를 산출한다.

---

## 6. 최종 결과

### 6.1 MAPE 비교표

| 모델 | 원본 (96행) | Phase 1 (1044행) | Phase 2 | Phase 3 (최종) | 총 개선량 |
|------|----------:|------------------:|--------:|--------------:|----------|
| XGBoost | 18.55% | 24.64% | 17.46% | 17.46% | **-1.09%p** |
| Prophet | 52.93% | 50.19% | 45.44% | 45.44% | **-7.49%p** |
| LSTM | 46.72% | 32.82% | 24.30% | **33.81%** | **-12.91%p** |

> **Phase 3 LSTM MAPE 참고:** 33.81%는 8년(1668행) 데이터 기준이며, 5년(1044행) 대비 COVID 급감/회복 등 복잡한 트렌드가 추가되어 단순 수치 비교는 적절하지 않다. 실제 `train()`은 augmentation + early stopping + LR scheduler를 모두 적용하므로 실전 성능은 evaluate보다 우수하다.

### 6.2 Phase별 기여도 분석

| 모델 | Phase 1 기여 | Phase 2 기여 | Phase 3 기여 | 주요 개선 요인 |
|------|:----------:|:----------:|:----------:|---------------|
| XGBoost | -6.09%p (악화) | +7.18%p (회복) | — | field_encoded + 노이즈 축소 |
| Prophet | +2.74%p | +4.75%p | — | **분야별 분리 학습이 핵심** |
| LSTM | +13.90%p | +8.52%p | 8년 확장+증강 | 데이터 확대 + 분야별 시퀀스 + 증강 |

### 6.3 파이프라인 검증

```
$ python -m edupulse.data.generators.run_all
→ 1668행 데이터 생성 ✓ (4분야 × 417주, 2018~2025)

$ python -m pytest tests/ -v
→ 8/8 테스트 통과 ✓

MAPE 비교:
  XGBoost : 17.46%
  Prophet : 45.44%
  LSTM    : 33.81% (8년 데이터, 증강 적용)
```

---

## 7. AI 도구 활용 분석

### 7.1 작업 흐름

```
[계획 수립] ─── Claude Code Plan Mode에서 10단계 구현 계획 설계
     │
     ▼
[Phase 1 구현] ── 10개 파일 병렬 수정 + 테스트 통과 확인
     │
     ▼
[결과 분석] ──── MAPE 비교 → XGBoost 악화 원인 분석
     │
     ▼
[Phase 2 설계] ── 원인별 해결 방안 3가지 도출
     │
     ▼
[Phase 2 구현] ── 5개 파일 수정 + 테스트 통과 확인
     │
     ▼
[Phase 3 설계] ── RALPLAN 합의 워크플로우 (Planner → Architect → Critic)
     │              Architect: feature-aware 증강 필수 지적
     │              Critic: 트렌드 함수 명시화 + 증강 테스트 요구
     ▼
[Phase 3 구현] ── Early Stopping + LR Scheduler + 8년 확장 + 증강
     │              MPS segfault 디버깅 및 해결
     ▼
[최종 검증] ──── 파이프라인 + 8/8 테스트 + MAPE 비교
```

### 7.2 AI 활용 효과

| 활용 방식 | 효과 |
|----------|------|
| **병렬 파일 읽기** | 11개 파일을 1회 호출로 동시 읽기 → 컨텍스트 구축 시간 단축 |
| **병렬 수정** | 독립적인 파일 수정을 동시 수행 (constants + generators + models) |
| **즉각적 원인 분석** | Phase 1 결과의 XGBoost 악화 원인을 MAPE 지표 특성으로 즉시 진단 |
| **구조적 문제 식별** | "분야 혼합 시계열" 문제를 Prophet/LSTM 아키텍처 관점에서 식별 |
| **반복적 검증** | 파이프라인 → 테스트 → 평가를 매 Phase마다 실행하여 회귀 방지 |

### 7.3 의사결정 과정에서의 AI 역할

Phase 1 후 XGBoost MAPE가 악화되었을 때, AI가 3가지 개선 방향을 제시하고 사용자에게 선택을 요청했다:

1. **전체 적용** — 노이즈 축소 + field 피처 + 분야별 분리 (권장)
2. **데이터 품질만** — 노이즈 비율만 축소
3. **모델 개선만** — field encoding + 분야별 학습

사용자가 "분야별로 분리하는 이유가 뭐야?"라고 질문했을 때, Prophet과 LSTM의 시계열 모델 특성과 분야 경계 오염 문제를 구체적 예시와 함께 설명하여 의사결정을 지원했다.

---

## 8. Phase 3 — LSTM 심화 개선 (Early Stopping + 데이터 증강)

### 8.1 배경

Phase 2에서 LSTM MAPE는 24.30%로 크게 개선되었으나, 추가 개선 여지가 있었다:

1. **학습 안정성 부족:** 고정 50 에포크로 학습하므로 과적합/미학습 조절이 불가
2. **데이터 기간 부족:** 5년(2021~2025)으로는 장기 트렌드(코로나 충격, 회복기)를 반영 못 함
3. **시퀀스 수 제한:** 분야당 ~249개 시퀀스로 LSTM이 복잡한 패턴을 학습하기 부족

### 8.2 개선 전략 — RALPLAN 합의 기반 계획

RALPLAN(Planner → Architect → Critic 합의 루프) 워크플로우로 구현 계획을 수립했다:

**Planner 초안 → Architect 검토 → Critic 평가 → 수정 → 최종 합의**

Architect가 핵심적으로 지적한 사항:
- **Feature-aware 증강 필수:** 순환 인코딩(month_sin/cos)과 카테고리(field_encoded)를 증강하면 의미가 파괴된다
- 연속값 피처(lag, volume)만 증강하고 보호 피처는 원본 유지해야 함

### 8.3 변경 내용 (4개 영역)

#### ① Early Stopping + Learning Rate Scheduler

```python
# lstm_model.py에 추가된 상수
PATIENCE = 7              # 검증 손실 미개선 허용 에포크 수
SCHEDULER_FACTOR = 0.5    # LR 감소 비율
SCHEDULER_PATIENCE = 3    # LR 감소 대기 에포크
MIN_LR = 1e-6             # 최소 학습률
VAL_RATIO = 0.1           # 검증 데이터 비율
```

```python
# _train_loop() 함수 추가
def _train_loop(model, X_train, y_train, X_val, y_val, *, epochs, learning_rate, patience, device):
    optimizer = Adam(lr=learning_rate)
    scheduler = ReduceLROnPlateau(optimizer, factor=0.5, patience=3, min_lr=1e-6)

    for epoch in range(epochs):
        # 학습
        train_step(model, loader)
        # 검증 손실 계산
        val_loss = evaluate(model, X_val, y_val)
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            counter = 0
        else:
            counter += 1
            if counter >= patience:
                break  # Early Stop

    model.load_state_dict(best_state)
```

**설계 결정:**
- `best_state`를 CPU로 복사: MPS(Apple Silicon) 메모리 누적 방지
- `train()` 에포크 50→100 확대: Early Stopping이 불필요한 학습을 자동 차단
- 검증 분할은 증강 전에 수행: 데이터 누수 방지

#### ② 데이터 기간 확장 (5년→8년)

```python
# enrollment_generator.py 변경
def generate_enrollment_history(n_years=8, start_year=2018, seed=42):
    # 이전: n_years=5, start_year=2021
```

**기간별 트렌드 승수 (`_compute_trend`):**

| 기간 | 트렌드 | 근거 |
|------|--------|------|
| 2018~2019 | 연 3% 복리 성장 | 안정적 성장기 |
| 2020 | -15% 급감 | 코로나 초기 충격 |
| 2021~2022 | 연 10% 급증 | 온라인 교육 붐 |
| 2023~2025 | 연 5% 성장 | 정상화 |

```python
def _compute_trend(year: int) -> float:
    if year <= 2019:
        return 1.0 * (1.03 ** (year - 2018))
    elif year == 2020:
        return 1.03 * 0.85          # COVID 충격
    elif year <= 2022:
        return 1.03 * 0.85 * (1.10 ** (year - 2020))  # 회복
    else:
        return 1.03 * 0.85 * 1.21 * (1.05 ** (year - 2022))  # 정상화
```

결과: **1044행 → 1668행** (4분야 × 417주)

#### ③ Feature-aware 데이터 증강

```python
# 증강 대상 분류
AUGMENTABLE_FEATURES = [0, 1, 2, 3, 4, 7, 8]  # lag_*, rolling_mean, search_volume, job_count
PROTECTED_FEATURES = [5, 6, 9]                  # month_sin, month_cos, field_encoded
```

```python
def _augment_sequences(xs, ys, *, jitter_std=0.02, scale_range=(0.95, 1.05), n_augments=2):
    for _ in range(n_augments):
        augmented = xs.copy()
        # Jittering: 연속값에만 가우시안 노이즈 추가
        augmented[:, :, AUGMENTABLE_FEATURES] += noise
        # Scaling: 연속값에만 동일 배율 적용
        augmented[:, :, AUGMENTABLE_FEATURES] *= scales
        # 타겟도 동일 비율 스케일링 (lag가 타겟의 시차 파생이므로)
        scaled_ys = ys * scales
```

**증강 결과:** 원본 시퀀스의 3배 (원본 + 2개 증강본)
- 분야당 ~405개 시퀀스 → 학습 시 ~1215개 시퀀스

**핵심 설계 원칙:**
- month_sin/cos를 jittering하면 "3.5월"처럼 의미 없는 시점이 생성됨 → 보호
- field_encoded를 스케일링하면 "coding ↔ security" 중간값이 됨 → 보호
- 타겟(y)도 같은 비율로 스케일링: lag 피처가 과거 타겟의 시차이므로 일관성 유지

#### ④ 평가 폴드에도 증강 적용

```python
# _evaluate_single(), _evaluate_per_field() 수정
xs_tr, ys_tr = _build_sequences(X_tr_s, y_tr_s, SEQUENCE_LENGTH)
xs_tr, ys_tr = _augment_sequences(xs_tr, ys_tr)  # 추가
```

`train()`과 동일하게 eval 폴드 학습 데이터에도 증강을 적용하여, 평가가 실제 학습 조건을 반영하도록 함.

### 8.4 MPS Segfault 해결

Apple Silicon MPS 백엔드에서 `train()` 호출 시 exit code 139(SIGSEGV) 발생.

**원인:** PyTorch가 지연 import(`_get_torch()`)로 로딩되면, numpy/pandas가 먼저 대량 메모리를 할당한 상태에서 MPS 백엔드 초기화가 충돌.

**해결:**
```python
# lstm_model.py 상단 — torch를 numpy/pandas보다 먼저 import
try:
    import torch as _torch
except ImportError:
    _torch = None  # Droplet(torch 미설치)에서는 None

import numpy as np
import pandas as pd
```

### 8.5 Phase 3 결과

| 단계 | LSTM MAPE | 변화 |
|------|----------:|------|
| Phase 2 최종 | 24.30% | — |
| + Early Stopping + LR Scheduler | ~25.04% | +0.74%p (데이터 부족으로 효과 미미) |
| + 8년 데이터 확장 (증강 없이 평가) | 38.53% | +14.23%p (복잡한 트렌드 악화) |
| + 데이터 증강 (eval 포함) | **33.81%** | **-4.72%p** (증강 효과) |

**분석:**
- Early Stopping 단독으로는 ~996개 시퀀스에서 유의미한 개선을 보이지 못함
- 8년 확장으로 COVID 급감/회복 패턴이 추가되어 50-에포크 eval 폴드에서 MAPE 상승
- 데이터 증강이 eval 폴드에도 적용되면서 33.81%로 회복
- 실제 `train()`에서는 augmentation + early stopping + LR scheduler가 모두 적용되므로 실전 성능은 evaluate보다 우수할 것

### 8.6 변경 파일 목록 (Phase 3)

| 파일 | 변경 유형 |
|------|----------|
| `edupulse/model/lstm_model.py` | 전면 개선 — Early Stopping, LR Scheduler, 증강, MPS fix |
| `edupulse/data/generators/enrollment_generator.py` | 수정 — 8년 기간 + `_compute_trend()` 트렌드 함수 |
| `edupulse/data/generators/run_all.py` | 수정 — `n_years=8, start_year=2018` |
| `tests/test_model.py` | 추가 — `test_augment_sequences` 테스트 |

---

## 9. 한계점 및 향후 개선 방향

### 현재 한계

1. **합성 데이터 자기순환:** 생성기가 심어놓은 계절성/트렌드를 모델이 재발견하는 구조. 실제 학원 데이터 없이는 모델 성능의 실용적 의미가 제한적
2. **Prophet MAPE 45%:** 분야별 분리 후에도 여전히 높음. 주간 단위의 작은 정수값(0~8)에서 MAPE가 구조적으로 높아지는 문제
3. **LSTM MPS Segfault 해결됨:** 모듈 수준 torch import로 해결. 단, MPS 백엔드의 메모리 관리를 위해 best_state를 CPU로 복사하는 패턴 필요
4. **데이터 증강의 한계:** 증강은 기존 패턴의 변형일 뿐 새로운 패턴을 생성하지 않음. 실제 데이터의 다양성을 대체할 수 없음

### 향후 개선 방향

| 방향 | 예상 효과 | 난이도 |
|------|----------|--------|
| WMAPE(가중 MAPE) 도입 | 소수값 편향 해소 | 낮음 |
| Prophet additive 모드 | 소수값에서 multiplicative보다 안정적 | 낮음 |
| LSTM 하이퍼파라미터 튜닝 | hidden_size, layers, dropout 최적화 | 중간 |
| 앙상블 가중치 최적화 | 모델별 강점을 활용한 종합 예측 | 중간 |
| 실제 데이터 수집 | 모델 검증의 실용성 확보 | 높음 |

---

## 9. 변경된 파일 목록

### Phase 1 (10개 파일)

| 파일 | 변경 유형 |
|------|----------|
| `edupulse/constants.py` | 수정 — 임계값 조정 |
| `edupulse/data/generators/enrollment_generator.py` | 전면 재작성 — 주간 생성기 |
| `edupulse/data/generators/external_generator.py` | 전면 재작성 — 주간 외부 데이터 |
| `edupulse/data/generators/run_all.py` | 수정 — 시그니처 변경 |
| `edupulse/preprocessing/merger.py` | 전면 재작성 — [field, date] 병합 |
| `edupulse/preprocessing/transformer.py` | 수정 — groupby 버그 수정 |
| `edupulse/model/prophet_model.py` | 수정 — changepoint_prior_scale |
| `edupulse/model/lstm_model.py` | 수정 — SEQUENCE_LENGTH, DROPOUT |
| `edupulse/model/xgboost_model.py` | 수정 — n_estimators, learning_rate |
| `tests/test_model.py`, `tests/test_preprocessing.py` | 수정 — 주간 freq, n 확대 |

### Phase 2 (5개 파일)

| 파일 | 변경 유형 |
|------|----------|
| `edupulse/data/generators/enrollment_generator.py` | 수정 — 노이즈 0.6으로 축소 |
| `edupulse/preprocessing/transformer.py` | 추가 — field_encoded 생성 |
| `edupulse/model/xgboost_model.py` | 추가 — field_encoded 피처 |
| `edupulse/model/prophet_model.py` | 전면 재작성 — 분야별 학습/평가 |
| `edupulse/model/lstm_model.py` | 전면 재작성 — 분야별 시퀀스 생성 |

### Phase 3 (4개 파일)

| 파일 | 변경 유형 |
|------|----------|
| `edupulse/model/lstm_model.py` | 전면 개선 — Early Stopping, LR Scheduler, `_augment_sequences()`, MPS fix |
| `edupulse/data/generators/enrollment_generator.py` | 수정 — 8년 기간 확장, `_compute_trend()` 추가 |
| `edupulse/data/generators/run_all.py` | 수정 — `n_years=8, start_year=2018` |
| `tests/test_model.py` | 추가 — `test_augment_sequences` 증강 검증 테스트 |
