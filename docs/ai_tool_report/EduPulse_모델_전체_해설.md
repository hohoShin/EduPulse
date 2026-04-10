# EduPulse 모델 전체 해설 — 데이터부터 예측까지

> **작성일:** 2026-04-08 | **최종 수정:** 2026-04-10
> **목적:** EduPulse의 데이터 파이프라인, 전처리, 모델 구조, 평가 방법을 개인 학습용으로 정리

---

## 1. 전체 구조 한눈에 보기

```
[1. 데이터 생성 (9종)]     [2. 전처리]           [3. 모델 학습]        [4. API 서빙]

enrollment_generator        cleaner               XGBoost ──┐
  ↓ enrollment.csv           ↓ 결측치 보간          Prophet ──┼─ Ensemble → FastAPI
external_generator          merger                LSTM ─────┘
  ↓ search_trends.csv        ↓ [field,date] 병합                  /api/v1/demand (2)
  ↓ job_postings.csv        transformer                           /api/v1/schedule (1)
internal_generator           ↓ lag/rolling/인코딩                  /api/v1/marketing (2)
  ↓ consultation_logs.csv                                         /api/v1/simulation (4)
  ↓ student_profiles.csv   training_dataset.csv                   /api/v1/health (1)
  ↓ web_logs.csv             (1668행 × 19피처)
schedule_generator
  ↓ cert_exam_schedule.csv
  ↓ competitor_data.csv
  ↓ seasonal_events.csv
```

**실행 커맨드:**
```bash
# 전체 파이프라인 (생성 → 전처리 → 학습)
.venv/bin/python scripts/run_pipeline.py

# 개별 단계
.venv/bin/python -m edupulse.data.generators.run_all     # 데이터 생성만
.venv/bin/python -m edupulse.model.train --model all     # 학습만
.venv/bin/python -m edupulse.model.evaluate --model all  # 평가만
```

> **중요:** 반드시 `.venv/bin/python` (Python 3.12) 사용. 시스템 python3 (3.11)은 torch MPS segfault 발생.

---

## 2. 데이터 구조

### 2.1 데이터 규격

| 항목 | 값 |
|------|-----|
| 해상도 | **주간** (매주 월요일 기준) |
| 기간 | 2018-01-04 ~ 2025-12-29 (8년) |
| 분야 | coding, security, game, art (4개) |
| 총 행수 | **1668행** (4분야 × 417주) |
| 타겟 변수 | `enrollment_count` (주간 등록 인원) |
| CSV 소스 | **9종** (내부 3 + 외부 2 + 일정/경쟁/계절 3 + 수강이력 1) |

### 2.2 수강 이력 (enrollment_history.csv)

```
date,        field,    cohort, enrollment_count, ds,         y
2021-01-04,  coding,   1,      5,                2021-01-04, 5
2021-01-11,  coding,   1,      4,                2021-01-11, 4
...
```

| 컬럼 | 설명 |
|------|------|
| `date` | 주 시작일 (월요일), `pd.date_range(freq="W-MON")` |
| `field` | 분야 — coding, security, game, art |
| `cohort` | 기수 번호 (8주 단위로 파생: `week_index // 8 + 1`) |
| `enrollment_count` | 해당 주의 등록 인원 (정수) |
| `ds`, `y` | Prophet 호환용 컬럼 (date와 enrollment_count의 복사) |

**등록 인원 생성 공식:**

```python
enrollment = round(max(0, base * trend + seasonal + noise))
```

- `base`: 분야별 주간 기본 수요 — coding=4, security=3, game=3, art=2
- `trend`: 기간별 트렌드 승수 (`_compute_trend(year)`)
  - 2018~2019: 연 3% 복리 성장 (안정적 성장기)
  - 2020: -15% 급감 (코로나 초기 충격)
  - 2021~2022: 연 10% 급증 (온라인 교육 붐)
  - 2023~2025: 연 5% 성장 (정상화)
- `seasonal`: 월별 계절성 보정 — 방학(1,7,8월) +1.5~2.0 / 학기중(3~5,9~11월) -0.8~-1.2
- `noise`: 랜덤 노이즈 — `normal(0, 0.6)`

### 2.3 외부 데이터 (external_generator.py)

**검색 트렌드 (search_trends.csv)**
```
date, field, search_volume, ds, y
```
- enrollment_count와 같은 `[field, date]` 그리드 사용
- 검색량 = 2~4주 후의 등록 인원 × 분야별 상관계수 + 노이즈
- 상관계수: coding=1.8, security=1.5, game=1.6, art=1.2
- **의미:** "등록이 늘기 2~4주 전에 검색이 먼저 증가한다"는 선행 지표

**채용 공고 (job_postings.csv)**
```
date, field, job_count, ds, y
```
- 채용 공고 수 = 등록 인원 × 분야별 상관계수 + 노이즈
- 상관계수: coding=2.5, security=3.0, game=1.8, art=1.0
- **의미:** "IT 채용이 활발하면 관련 교육 수요도 높다"는 동행 지표

### 2.4 내부 데이터 (internal_generator.py)

**상담 로그 (consultation_logs.csv)**
```
date, field, consultation_count, conversion_rate, ds, y
```
- 상담 건수 = 1~3주 후 등록 인원 × 분야별 배율 + 노이즈
- 배율: coding=3.0, security=2.5, game=2.0, art=1.5
- **의미:** 개강 전 학원에 접수되는 상담 건수 (실제 선행지표)

**학생 프로필 (student_profiles.csv)**
```
date, field, enrollment_count, age_20s_ratio, age_30s_ratio, age_40plus_ratio, purpose, ds, y
```
- 연령 비율: 분야별 Dirichlet 분포로 생성 (coding=20대 집중, security=30대 중심 등)
- 수강 목적: 취업/취미/자격증 비율 (분야별 상이)
- demographics API에서 활용 (모델 피처에는 미사용)

**웹 로그 (web_logs.csv)**
```
date, field, page_views, cart_abandon_rate, ds, y
```
- 페이지뷰 = 1~3주 후 등록 인원 × 분야별 배율 + 노이즈
- 배율: coding=15.0, security=12.0, game=18.0, art=10.0
- `cart_abandon_rate`는 모델 피처에서 제거됨 (학원에 장바구니 개념 없음)

### 2.5 일정/경쟁/계절 데이터 (schedule_generator.py)

**자격증 시험 일정 (cert_exam_schedule.csv)**
```
date, field, has_cert_exam, weeks_to_exam
```
- 분야별 연 1~4회 시험 일정을 고정 배치 (coding: 3회, security: 4회 등)
- `weeks_to_exam`: 다음 시험까지 남은 주 수 (0~52)

**경쟁사 데이터 (competitor_data.csv)**
```
date, field, competitor_openings, competitor_avg_price
```
- 경쟁 학원 개강 수: 등록 인원과 상관관계 + 3~6주 지연
- 평균 수강료: 분야별 기준가 ± 노이즈 (coding=120만, security=150만 등)

**계절 이벤트 (seasonal_events.csv)**
```
date, is_vacation, is_exam_season, is_semester_start
```
- 분야 무관 (날짜 기반): 방학(1,2,7,8월), 시험 시즌(4,6,10,12월), 학기 시작(3,9월)
- 바이너리 플래그 (0 또는 1)

### 2.6 수요 등급 기준

```python
DEMAND_THRESHOLDS = {"high": 6, "mid": 3}

# 주간 등록 6명 이상 → HIGH
# 주간 등록 3~5명   → MID
# 주간 등록 0~2명   → LOW
```

산정 근거: 기수 단위 25명(HIGH) ÷ 8주 ≈ 3명/주 → MID 기준. HIGH는 MID의 2배 = 6명.

---

## 3. 전처리 파이프라인

### 3.1 처리 순서

```
9개 CSV 소스
├── enrollment_history.csv (기준 테이블)
├── search_trends.csv
├── job_postings.csv
├── consultation_logs.csv
├── student_profiles.csv
├── web_logs.csv
├── cert_exam_schedule.csv
├── competitor_data.csv
└── seasonal_events.csv
            │
    ┌───────▼────────┐
    │   merger.py    │  [field, date] 기준 left join (9개 → 1개)
    │   주간 정렬     │  seasonal은 field 없음 → date만으로 join
    └───────┬────────┘
            │
    ┌───────▼────────┐
    │  cleaner.py    │  결측치: linear interpolation
    │                │  이상치: IQR 방식 clip
    └───────┬────────┘
            │
    ┌───────▼────────┐
    │ transformer.py │  lag feature + rolling mean
    │                │  순환 인코딩 + field 인코딩
    │                │  age_group_diversity (Shannon entropy)
    └───────┬────────┘
            │
    training_dataset.csv (1668행 × 34컬럼, 이 중 19개가 FEATURE_COLUMNS)
```

### 3.2 merger.py — 데이터 병합

```python
# 병합 키
join_keys = ["field", "date"]

# 날짜를 주 시작일(월요일)로 정규화
merged["date"] = merged["date"].dt.to_period("W").dt.start_time
```

- enrollment(내부)을 기준으로 나머지 8개 소스를 `LEFT JOIN`
- seasonal_events는 `field` 컬럼이 없으므로 `date`만으로 조인
- 병합 후 결측치는 `forward fill`

### 3.3 cleaner.py — 정제

**결측치 처리:**
```python
df[numeric_cols].interpolate(method="linear", limit_direction="both")
```
- 시계열 데이터이므로 `linear interpolation` 사용 (앞뒤 값의 평균)

**이상치 처리:**
```python
lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR
df[col].clip(lower, upper)
```
- IQR(사분위범위) 방식으로 극단값을 경계값으로 대체
- 삭제가 아니라 **클리핑** — 시계열의 연속성을 유지

### 3.4 transformer.py — 피처 생성

**lag features (시차 특성):**
```python
# 분야별로 독립 shift — 분야 경계 오염 방지
df.groupby("field")["enrollment_count"].shift(lag)
```

| 피처 | 의미 |
|------|------|
| `lag_1w` | 1주 전 등록 인원 |
| `lag_2w` | 2주 전 등록 인원 |
| `lag_4w` | 4주 전 등록 인원 |
| `lag_8w` | 8주 전 등록 인원 |
| `rolling_mean_4w` | 최근 4주 이동평균 |

**순환 인코딩 (월 정보):**
```python
month_sin = sin(2π × month / 12)
month_cos = cos(2π × month / 12)
```
- 12월(12)과 1월(1)이 가까운 값이 되도록 삼각함수로 인코딩
- 단순 정수(1~12)로 하면 12→1 사이에 비연속적 점프가 생김

**분야 label encoding:**
```python
field_encoded = {"art": 0, "coding": 1, "game": 2, "security": 3}
```

**age_group_diversity (Shannon entropy):**
```python
# 연령대 비율의 정보 엔트로피 — 분포가 균등할수록 높은 값
entropy = -Σ(ratio × log(ratio))
```
- `age_20s_ratio`, `age_30s_ratio`, `age_40plus_ratio`에서 계산
- 학습 데이터에는 생성되지만, 모델 피처에서는 제거됨 (예측 시점에 알 수 없는 사후 지표)

### 3.5 FEATURE_COLUMNS (모델 입력 19개)

```python
FEATURE_COLUMNS = [
    # --- 시계열 (5) ---
    "lag_1w", "lag_2w", "lag_4w", "lag_8w",
    "rolling_mean_4w",
    # --- 날짜/분야 인코딩 (3) ---
    "month_sin", "month_cos", "field_encoded",
    # --- 외부 지표 (2) ---
    "search_volume", "job_count",
    # --- 내부 선행지표 (2) ---
    "consultation_count", "page_views",
    # --- 자격증 일정 (2) ---
    "has_cert_exam", "weeks_to_exam",
    # --- 경쟁사 (2) ---
    "competitor_openings", "competitor_avg_price",
    # --- 계절 이벤트 (3) ---
    "is_vacation", "is_exam_season", "is_semester_start",
]
```

**제거된 피처 3개 (2026-04-10):**

| 피처 | 제거 사유 |
|------|-----------|
| `cart_abandon_rate` | 학원에 장바구니 개념 없음 (도메인 부적합) |
| `conversion_rate` | `enrollment / (consultation + 1)` — 타겟 순환 의존 (data leakage) |
| `age_group_diversity` | 수강 후 사후 집계 지표 — 예측 시점에 알 수 없음 |

---

## 4. 모델 아키텍처

### 4.1 공통 구조 (base.py)

```python
class BaseForecaster(ABC):
    def train(df)        # 학습
    def predict(features) # 예측 (스레드 안전 — Lock)
    def evaluate(df)      # TimeSeriesSplit K-Fold → MAPE
    def save(path, ver)   # 저장 + metadata.json 생성
    def load(path, ver)   # 로딩 + 피처 불일치 경고
```

모든 모델은 `BaseForecaster`를 상속하고, 동일한 인터페이스로 동작한다.

**PredictionResult (예측 결과):**
```python
@dataclass
class PredictionResult:
    predicted_enrollment: int     # 예측 등록 인원
    demand_tier: DemandTier       # HIGH / MID / LOW
    confidence_lower: float       # 신뢰구간 하한
    confidence_upper: float       # 신뢰구간 상한
    model_used: str               # "xgboost" / "prophet" / "lstm" / "ensemble(...)"
    mape: float | None            # 모델의 MAPE (평가 후 설정)
```

**피처 안전장치 (base.py):**
- `validate_feature_columns()`: 학습/예측 시 누락 피처가 있으면 `warnings.warn()` 출력
- `warn_feature_mismatch()`: 모델 로딩 시 학습 당시 피처와 현재 FEATURE_COLUMNS 불일치 경고
- `ensure_feature_columns()`: 누락 컬럼을 0으로 채워 shape 보장 (원본 DataFrame 변경 없음)

---

### 4.2 XGBoost — 트리 기반 앙상블

**한 줄 요약:** 각 행을 독립적인 피처 벡터로 보고, 결정 트리를 순차적으로 쌓아 오차를 줄여나가는 모델.

```
입력 피처 (19개)                         출력
┌──────────────────────────┐
│ lag_1w~8w, rolling_mean, │
│ month_sin/cos,           │
│ search_volume, job_count,│ ──→ XGBRegressor ──→ enrollment_count (실수)
│ consultation_count,      │                       ↓
│ page_views,              │                    round() → 정수
│ has_cert_exam, weeks_to, │                       ↓
│ competitor_*, seasonal,  │                   classify_demand() → HIGH/MID/LOW
│ field_encoded            │
└──────────────────────────┘
```

**하이퍼파라미터:**
```python
XGBRegressor(
    n_estimators=300,      # 결정 트리 300개를 순차적으로 학습
    max_depth=4,           # 각 트리의 최대 깊이 (과적합 방지)
    learning_rate=0.03,    # 각 트리의 기여도 (작을수록 정교, 느림)
    subsample=0.8,         # 각 트리에 전체 데이터의 80%만 사용
    colsample_bytree=0.8,  # 각 트리에 전체 피처의 80%만 사용
)
```

**XGBoost가 학습하는 방식:**
1. 첫 번째 트리: 전체 데이터의 평균으로 시작
2. 두 번째 트리: 첫 번째 트리의 **잔차(오차)**를 예측
3. 세 번째 트리: 누적 오차의 잔차를 예측
4. ... 300번 반복
5. 최종 예측 = 모든 트리 예측의 합

**왜 XGBoost가 잘 작동하는가:**
- 각 행을 독립적으로 처리하므로 분야 혼합 데이터도 문제없음
- `field_encoded` 피처로 "이 행은 coding이고, coding의 패턴은 이렇다"를 학습
- lag 피처가 시계열 정보를 담고 있어 시간적 패턴도 간접적으로 학습

**피처 중요도 (Feature Importance, 2026-04-10 기준):**

| 피처 | Importance | 해석 |
|------|-----------|------|
| is_vacation | 0.2278 | 방학 여부가 가장 강력한 예측 인자 |
| rolling_mean_4w | 0.2139 | 최근 4주 추세 |
| competitor_openings | 0.1801 | 경쟁 학원 개강 수 |
| is_semester_start | 0.1186 | 학기 시작 여부 |
| job_count | 0.1092 | 채용 공고 수 |
| 나머지 14개 | 각 0.003~0.027 | 보조 역할 |

**MAPE: 16.20%**

---

### 4.3 Prophet — 시계열 분해 모델

**한 줄 요약:** 시계열을 트렌드(장기 추세) + 계절성(반복 패턴) + 회귀자(외부 요인)로 분해하여 예측하는 Facebook 개발 모델.

```
y(t) = trend(t) + seasonality(t) + regressors(t) + error(t)

trend:        ───────────/───────── (연간 5% 성장 같은 장기 추세)
                        ↗ changepoint (변화점)

seasonality:  ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿ (방학=증가, 학기중=감소 반복)

regressors:   search_volume, job_count (추가 외부 정보)
```

**핵심 개념:**

| 개념 | 설명 |
|------|------|
| **트렌드 (trend)** | 시간이 지남에 따른 장기적 변화. 연 5% 성장 같은 것 |
| **변화점 (changepoint)** | 트렌드가 급변하는 시점. Prophet이 자동 감지 |
| **계절성 (seasonality)** | 매년 반복되는 패턴. 푸리에 급수로 모델링 |
| **회귀자 (regressor)** | search_volume, job_count 같은 추가 설명 변수 |

**하이퍼파라미터:**
```python
Prophet(
    seasonality_mode="multiplicative",   # 계절성 효과가 트렌드에 비례
    yearly_seasonality=True,             # 연간 패턴 학습
    weekly_seasonality=False,            # 주간 패턴은 불필요 (데이터 자체가 주간)
    changepoint_prior_scale=0.15,        # 변화점 민감도 (높을수록 유연)
)
```

**분야별 분리 학습:**
```python
# 4개 분야 각각에 독립 Prophet 모델을 학습
self._field_models = {
    "coding":   Prophet().fit(coding_data),    # 261행
    "security": Prophet().fit(security_data),  # 261행
    "game":     Prophet().fit(game_data),      # 261행
    "art":      Prophet().fit(art_data),       # 261행
}
```

Prophet은 **단일 시계열 모델**이다. 4분야를 섞으면 coding→security 경계에서 "급락"으로 오해석한다. 분야별 분리가 필수.

**Prophet이 요구하는 데이터 형식:**
```
ds (datetime): 날짜
y (float):     예측 대상 값
+ 선택적 회귀자 컬럼
```

**MAPE: 45.44%** — 다른 모델보다 높은 이유:
- 주간 등록이 0~8명 정도의 작은 정수 → MAPE가 구조적으로 불리
- multiplicative 모드에서 0에 가까운 값은 계절성 효과가 왜곡됨

---

### 4.4 LSTM — 순환 신경망

**한 줄 요약:** 과거 12주의 시퀀스 패턴을 학습하여 다음 주 등록 인원을 예측하는 딥러닝 모델.

```
입력 시퀀스 (12주 × 19피처)              LSTM 셀                    출력

주 t-12: [lag_1w, lag_2w, ...]  → ┌──────────┐
주 t-11: [lag_1w, lag_2w, ...]  → │          │
주 t-10: [lag_1w, lag_2w, ...]  → │   LSTM   │
    ...                           │  2 layers │ → h(마지막) → Linear → enrollment
주 t-2:  [lag_1w, lag_2w, ...]  → │  hidden=64│                        (1개 값)
주 t-1:  [lag_1w, lag_2w, ...]  → │ dropout=0.3│
                                  └──────────┘
```

**LSTM이 학습하는 방식:**

1. **시퀀스 생성 (슬라이딩 윈도우):**
   ```
   데이터: [w1, w2, w3, w4, w5, w6, ..., w13, w14, ...]

   시퀀스 1: [w1~w12]  → 정답: w13
   시퀀스 2: [w2~w13]  → 정답: w14
   시퀀스 3: [w3~w14]  → 정답: w15
   ...
   ```
   12주 분량의 데이터를 입력으로, 바로 다음 주 값을 예측

2. **LSTM 셀 내부 (직관적 이해):**
   - **잊기 게이트:** "2달 전의 정보는 잊어도 되나?" → sigmoid로 판단
   - **입력 게이트:** "이번 주 정보 중 뭘 기억해야 하나?" → sigmoid로 판단
   - **셀 상태:** 장기 기억 (계절성 같은 느린 패턴)
   - **은닉 상태:** 단기 기억 (최근 몇 주의 추세)

3. **2층 구조:** 첫 번째 LSTM이 추출한 패턴을 두 번째 LSTM이 더 추상적으로 학습

**하이퍼파라미터:**
```python
SEQUENCE_LENGTH = 12   # 입력 시퀀스 길이 (12주 = 1분기)
HIDDEN_SIZE = 64       # LSTM 은닉 상태 크기 (기억 용량)
NUM_LAYERS = 2         # LSTM 층 수 (깊을수록 복잡한 패턴)
DROPOUT = 0.3          # 학습 시 30% 뉴런 비활성화 (과적합 방지)
BATCH_SIZE = 32        # 한 번에 학습하는 시퀀스 수
INPUT_SIZE = 19        # 피처 수 (= len(FEATURE_COLUMNS))
```

**학습 안정화 (Early Stopping + LR Scheduler):**
```python
PATIENCE = 7              # 검증 손실이 7 에포크 연속 미개선 시 학습 종료
SCHEDULER_FACTOR = 0.5    # 학습률을 절반으로 감소
SCHEDULER_PATIENCE = 3    # 3 에포크 미개선 시 학습률 감소 트리거
MIN_LR = 1e-6             # 학습률 하한
VAL_RATIO = 0.1           # 학습 데이터의 10%를 검증용으로 분리
```

- **Early Stopping:** 검증 손실이 개선되지 않으면 조기 종료하여 과적합 방지
- **ReduceLROnPlateau:** 검증 손실 정체 시 학습률을 자동 감소하여 미세 조정
- 최대 에포크 100으로 설정, 실제로는 Early Stopping이 불필요한 학습을 자동 차단

**Feature-aware 데이터 증강:**
```python
# 이름 기반 동적 분류 (하드코딩 인덱스 사용 금지)
_PROTECTED_NAMES = {
    "month_sin", "month_cos", "field_encoded",
    "has_cert_exam", "is_vacation", "is_exam_season", "is_semester_start",
}

# 보호 피처: 이산값/바이너리 → 원본 유지 (7개)
PROTECTED_FEATURES = [i for i, c in enumerate(FEATURE_COLUMNS) if c in _PROTECTED_NAMES]

# 증강 대상: 연속값 → jittering + scaling 적용 (12개)
AUGMENTABLE_FEATURES = [i for i, c in enumerate(FEATURE_COLUMNS) if c not in _PROTECTED_NAMES]
```

증강 방식:
- **Jittering:** 연속값 피처에 가우시안 노이즈(σ=0.02) 추가
- **Scaling:** 시퀀스별 동일 배율(0.95~1.05)로 연속값 피처 스케일링
- 타겟(y)도 같은 비율로 스케일링 (lag 피처가 과거 타겟의 시차이므로 일관성 유지)
- 결과: 원본의 3배 시퀀스 (원본 + 2개 증강본)

**왜 보호 피처를 증강하면 안 되는가:**
- `month_sin/cos`를 jittering하면 "3.5월" 같은 존재하지 않는 시점이 생성
- `field_encoded`를 스케일링하면 "coding과 security 사이" 같은 의미 없는 분야가 됨
- `is_vacation`, `has_cert_exam` 등 바이너리 플래그에 노이즈를 더하면 0/1이 아닌 값이 됨

**데이터 정규화:**
```python
# MinMaxScaler: 모든 값을 0~1 범위로 변환
scaler_X.fit_transform(X)  # 피처
scaler_y.fit_transform(y)  # 타겟

# 예측 후 역변환
scaler_y.inverse_transform(prediction)  # 0~1 → 원래 스케일
```

신경망은 0~1 범위의 입력에서 가장 잘 학습한다. 원래 스케일(0~8명)과 lag(0~8) + search_volume(0~15) 같은 스케일이 다른 피처들을 통일.

**분야별 시퀀스 생성:**
```python
# 변경 전: 전체 데이터에서 시퀀스 생성 → 분야 경계 오염
[...coding w416, coding w417, security w1, security w2...]
                              ↑ 경계: coding 끝 → security 시작이 하나의 시퀀스에 섞임

# 변경 후: 분야별로 독립 시퀀스 생성
coding:   [w1~w12]→w13, [w2~w13]→w14, ...  (405개 시퀀스)
security: [w1~w12]→w13, [w2~w13]→w14, ...  (405개 시퀀스)
game:     ...
art:      ...
→ 총 ~1620개 시퀀스 (원본)
→ 증강 후 ~4860개 시퀀스 (원본 × 3)로 학습
```

**MAPE: 33.81%** (8년 데이터 기준, 증강 적용)

---

### 4.5 앙상블 (Ensemble)

```python
class EnsembleForecaster:
    # 여러 모델의 예측을 가중 평균
    예측 = w1 × XGBoost예측 + w2 × Prophet예측 + w3 × LSTM예측
```

**가중치 자동 설정:**
```python
# MAPE 역수 비례 — MAPE가 낮을수록 높은 가중치
auto_weight():
    XGBoost MAPE=16.20% → weight = 1/16.20 = 0.062 → 정규화 후 ~52%
    LSTM    MAPE=33.81% → weight = 1/33.81 = 0.030 → 정규화 후 ~25%
    Prophet MAPE=45.44% → weight = 1/45.44 = 0.022 → 정규화 후 ~18%
```

**신뢰구간:** 보수적으로 설정
- 하한 = 모든 모델 중 `min(confidence_lower)`
- 상한 = 모든 모델 중 `max(confidence_upper)`

---

## 5. 모델 평가 — TimeSeriesSplit K-Fold

### 5.1 왜 일반 K-Fold를 쓰면 안 되는가

```
일반 K-Fold (랜덤 섞기):
  Train: [1월, 5월, 9월, 3월]  ← 미래(9월) 데이터로 학습
  Test:  [7월]                 ← 과거(7월)을 예측?? → 데이터 누수!

시계열 K-Fold (TimeSeriesSplit):
  Fold 1 Train: [1월~6월]   Test: [7월~8월]     ✓ 과거→미래
  Fold 2 Train: [1월~8월]   Test: [9월~10월]    ✓ 과거→미래
  Fold 3 Train: [1월~10월]  Test: [11월~12월]   ✓ 과거→미래
```

시계열 데이터에서 랜덤 셔플은 **미래 정보가 학습에 포함**되는 데이터 누수를 일으킨다. 항상 과거 데이터로 학습하고 미래를 예측해야 한다.

### 5.2 MAPE (Mean Absolute Percentage Error)

```
MAPE = mean( |실제 - 예측| / 실제 ) × 100%
```

| MAPE | 해석 |
|------|------|
| < 10% | 매우 정확 |
| 10~20% | 양호 |
| 20~30% | 합리적 |
| 30~50% | 부정확 |
| > 50% | 비실용적 |

**MAPE의 한계:** 실제값이 작을수록 분모가 작아져 MAPE가 과대 평가된다.
- 실제=20, 예측=19 → MAPE 5%
- 실제=2, 예측=1 → MAPE 50% (같은 1명 오차인데 10배)

### 5.3 현재 MAPE 결과

| 모델 | MAPE | 데이터 | 평가 |
|------|------|--------|------|
| **XGBoost** | **16.20%** | 1668행 (8년), 19피처 | 양호 — 계절 이벤트+경쟁사 피처 효과 |
| **LSTM** | **33.81%** | 1668행 (8년), 증강 적용 | 합리적 — Early Stopping 적용 |
| **Prophet** | **45.44%** | 분야별 분리, 회귀자 2개 | 부정확 — 소수값에서 MAPE 불리 |

> 합성 데이터 특성상 MAPE는 실데이터 대비 낙관적으로 편향됨 (synthetic correlation inflation). 실데이터 전환 시 MAPE 상승 예상.

---

## 6. 디바이스 전략 (MacBook vs Droplet)

```python
def get_device():
    if torch.cuda.is_available():   return "cuda"    # GPU 서버 (향후)
    elif torch.backends.mps.is_available(): return "mps"  # M4 MacBook
    else:                           return "cpu"      # Droplet
```

| | M4 MacBook (로컬) | Droplet (서버) |
|---|---|---|
| **역할** | LSTM 학습, 실험 | XGBoost/Prophet 자동 재학습, API 서빙 |
| **가속기** | MPS (Apple Silicon GPU) | CPU only |
| **사양** | M4, 통합메모리 | 1 vCPU / 2GB RAM |

**LSTM 학습 워크플로우:**
```
M4 MacBook에서 학습
    ↓
model/saved/lstm/v1/model.pt 생성
    ↓
scp로 Droplet 전송
    ↓
Droplet에서 load() → predict() 만 사용
```

Droplet(2GB RAM)은 LSTM 학습 불가. 추론만 가능.

---

## 7. API 예측 흐름

### 7.1 엔드포인트 목록

| 라우터 | 엔드포인트 | 기능 |
|--------|-----------|------|
| demand | `POST /demand/predict` | 수요 예측 (모델 선택 가능) |
| demand | `POST /demand/closure-risk` | 폐강 위험도 평가 |
| schedule | `POST /schedule/suggest` | 강사/강의실 배정 계획 |
| marketing | `POST /marketing/timing` | 광고 타이밍 + 얼리버드 제안 |
| marketing | `POST /marketing/lead-conversion` | 잠재 수강생 전환 예측 |
| simulation | `POST /simulation/optimal-start` | 최적 개강일 추천 (최대 16주) |
| simulation | `POST /simulation/simulate` | 신규 강좌 시나리오 시뮬레이션 |
| simulation | `POST /simulation/demographics` | 수강생 연령/목적 세분화 |
| simulation | `POST /simulation/competitors` | 경쟁 학원 동향 분석 |
| health | `GET /health` | 서버 상태 + 로딩된 모델 목록 |

### 7.2 수요 예측 흐름 상세

```
POST /api/v1/demand/predict
{
  "course_name": "웹 개발 부트캠프",
  "start_date": "2026-05-01",
  "field": "coding",
  "model_name": "ensemble"    ← 선택 (xgboost/prophet/lstm/ensemble)
}
```

```
내부 처리 (predict.py → build_features):
1. field="coding", start_date → 19개 피처 조립
   - enrollment_history.csv → lag_1w~8w, rolling_mean_4w
   - search_trends.csv → search_volume
   - job_postings.csv → job_count
   - consultation_logs.csv → consultation_count
   - web_logs.csv → page_views
   - cert_exam_schedule.csv → has_cert_exam, weeks_to_exam
   - competitor_data.csv → competitor_openings, competitor_avg_price
   - seasonal_events.csv → is_vacation, is_exam_season, is_semester_start
   - 날짜 → month_sin, month_cos
   - 분야 → field_encoded

2. model.predict(features) 호출
   - 캐시된 모델 사용 (model/saved/{model_name}/v1/)
   - mtime 기반 자동 리로딩 (retrain 후 반영)

3. PredictionResult 반환
```

```json
{
  "course_name": "웹 개발 부트캠프",
  "field": "coding",
  "predicted_enrollment": 5,
  "demand_tier": "Mid",
  "confidence_interval": {"lower": 3.2, "upper": 6.8},
  "model_used": "xgboost",
  "prediction_date": "2026-04-10T12:00:00Z"
}
```

### 7.3 모델 선택과 캐싱

```python
# predict.py — 모델 캐시 (스레드 안전)
_model_cache: dict[str, BaseForecaster] = {}
_model_mtime: dict[str, float] = {}

def load_model(model_name, version=MODEL_VERSION):
    # 1. 캐시에 있으면 mtime 비교 → 변경 없으면 캐시 반환
    # 2. mtime 변경됨 → 리로딩 (retrain으로 모델 갱신 시)
    # 3. 캐시에 없으면 디스크에서 로딩
    # I/O는 잠금 바깥에서 수행 (동시성 보장)
```

CSV 데이터도 `load_csv_cached()`로 캐싱하며, `.copy()` 반환으로 캐시 오염 방지.

---

## 8. 주요 용어 정리

| 용어 | 설명 |
|------|------|
| **lag feature** | 과거 시점의 값을 현재 행의 피처로 사용. lag_1w = 1주 전 값 |
| **rolling mean** | 이동평균. 최근 N개 값의 평균으로 노이즈를 평활화 |
| **순환 인코딩** | 월(1~12)을 sin/cos로 변환. 12월→1월의 연속성 보장 |
| **changepoint** | Prophet에서 트렌드가 급변하는 시점 |
| **시퀀스 (LSTM)** | 연속된 N주의 데이터를 하나의 입력으로 묶은 것 |
| **MinMaxScaler** | 값을 0~1 범위로 정규화. 신경망 학습에 필수 |
| **TimeSeriesSplit** | 시간 순서를 유지한 K-Fold. 과거→미래 방향으로만 분할 |
| **MAPE** | 평균 절대 백분율 오차. 예측 정확도의 퍼센트 지표 |
| **IQR** | 사분위범위(Q3-Q1). 이상치 탐지의 기준 |
| **forward fill** | 결측치를 직전 유효값으로 채우는 방법 |
| **앙상블** | 여러 모델의 예측을 조합하여 더 안정적인 결과를 얻는 기법 |
| **Dropout** | 학습 시 일부 뉴런을 랜덤 비활성화하여 과적합 방지 |
| **Early Stopping** | 검증 손실이 개선되지 않으면 학습을 조기 종료하여 과적합 방지 |
| **ReduceLROnPlateau** | 검증 손실 정체 시 학습률을 자동 감소시키는 스케줄러 |
| **데이터 증강** | 원본 데이터에 노이즈/스케일링을 적용하여 학습 데이터를 인위적으로 확대 |
| **Gradient Boosting** | XGBoost의 핵심 원리. 이전 트리의 오차를 다음 트리가 보정 |
| **Feature Importance** | 트리 모델에서 각 피처가 예측에 기여하는 정도 (gain 기준) |
| **data leakage** | 예측 시점에 알 수 없는 정보가 피처에 포함되어 낙관적 편향 유발 |
| **synthetic correlation** | 합성 데이터가 동일 소스에서 파생되어 인위적으로 높은 상관 발생 |

---

## 9. 파일 맵

```
edupulse/
├── constants.py                    # 수요 등급 기준 + CSV 경로 상수 9개
├── data/generators/
│   ├── enrollment_generator.py     # 주간 수강 이력 합성
│   ├── external_generator.py       # 검색 트렌드 + 채용 공고 합성
│   ├── internal_generator.py       # 상담 로그 + 학생 프로필 + 웹 로그 합성
│   ├── schedule_generator.py       # 자격증 일정 + 경쟁사 + 계절 이벤트 합성
│   └── run_all.py                  # 전체 데이터 생성 오케스트레이션 (9개 CSV)
├── preprocessing/
│   ├── cleaner.py                  # 결측치 보간 + 이상치 클리핑
│   ├── merger.py                   # [field, date] 기준 9-way 병합 + warehouse 저장
│   └── transformer.py              # lag, rolling, 순환인코딩, field인코딩, age entropy
├── model/
│   ├── base.py                     # BaseForecaster ABC + PredictionResult + 피처 검증
│   ├── utils.py                    # get_device() (MPS/CUDA/CPU 감지)
│   ├── xgboost_model.py            # XGBRegressor 래퍼 + FEATURE_COLUMNS 정의 (19개)
│   ├── prophet_model.py            # Prophet 래퍼, 분야별 개별 학습
│   ├── lstm_model.py               # LSTM 래퍼, 분야별 시퀀스 + 증강 + Early Stopping
│   ├── ensemble.py                 # MAPE 역수 가중 앙상블
│   ├── predict.py                  # build_features() + predict_demand() + 모델 캐시
│   ├── train.py                    # 학습 CLI
│   ├── evaluate.py                 # 평가 CLI (MAPE 비교)
│   ├── retrain.py                  # 자동 재학습 스케줄러
│   └── saved/                      # 저장된 모델 (xgboost/v1/, prophet/v1/, lstm/v1/)
└── api/
    ├── main.py                     # FastAPI 진입점 (5개 라우터 등록)
    ├── dependencies.py             # 모델 DI (get_model)
    ├── middleware.py                # CORS 설정
    ├── routers/
    │   ├── demand.py               # 수요 예측 + 폐강 위험 (2 endpoints)
    │   ├── schedule.py             # 강사/강의실 배정 (1 endpoint)
    │   ├── marketing.py            # 마케팅 타이밍 + 전환 예측 (2 endpoints)
    │   ├── simulation.py           # 시뮬레이션 4종 (4 endpoints)
    │   └── health.py               # 헬스체크 (1 endpoint)
    ├── schemas/
    │   ├── demand.py               # DemandRequest/Response + ClosureRisk
    │   ├── schedule.py             # ScheduleRequest/Response + AssignmentPlan
    │   ├── marketing.py            # MarketingRequest/Response + LeadConversion
    │   └── simulation.py           # OptimalStart, Simulate, Demographics, Competitor
    └── services/
        ├── simulation_service.py   # optimal-start, simulate, demographics, competitors
        ├── marketing_service.py    # lead-conversion 전환 예측
        └── schedule_service.py     # assignment_plan 배정 계획

scripts/
└── run_pipeline.py                 # 생성 → 전처리 → 학습 전체 파이프라인

tests/
├── conftest.py                     # FakeForecaster + make_fake_forecaster 팩토리
├── test_model.py                   # 모델 학습/예측/평가 테스트 (30+)
├── test_preprocessing.py           # 전처리 모듈 테스트
├── test_generators.py              # 합성 데이터 생성기 테스트
├── test_demand.py                  # demand + marketing + schedule API 테스트
├── test_simulation.py              # simulation 4종 API 테스트
├── test_collection.py              # 데이터 수집 테스트
└── test_health.py                  # 헬스체크 테스트
```
