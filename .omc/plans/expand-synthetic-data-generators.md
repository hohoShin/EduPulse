# Plan: Expand Synthetic Data Generators for All README Data Types

> **Created:** 2026-04-09
> **Revised:** 2026-04-09 (v2 -- addresses Architect/Critic review)
> **Status:** Draft -- awaiting confirmation
> **Complexity:** MEDIUM-HIGH
> **Scope:** ~12 files modified/created across generators, preprocessing, model, tests, docs

---

## Context

EduPulse's README describes 9 data sources that feed the prediction model, but only 3 are implemented:
- `enrollment_history.csv` (internal, synthetic)
- `search_trends.csv` (external, real Naver API + synthetic fallback)
- `job_postings.csv` (external, synthetic)

Six data types mentioned in the README have no generators and are not integrated into the pipeline. This plan adds synthetic generators for all missing types, integrates them into the merge/feature pipeline, updates documentation, migrates saved models, and adds tests.

### Current Feature Pipeline

```
FEATURE_COLUMNS (10 features):
  lag_1w, lag_2w, lag_4w, lag_8w, rolling_mean_4w,
  month_sin, month_cos, search_volume, job_count, field_encoded
```

### Missing Data Types

| # | Category | Data Type | Key Columns | Relationship to Enrollment |
|---|----------|-----------|-------------|---------------------------|
| 1 | Internal | Consultation logs | consultation_count, conversion_rate | Leading 1-2w (inquiries precede enrollment) |
| 2 | Internal | Student profiles | age_group_diversity (derived) | Co-moving (diverse demand = higher enrollment) |
| 3 | Internal | Web/app logs | page_views, cart_abandon_rate | Leading 1-3w (browsing precedes enrollment) |
| 4 | External | Cert exam schedules | has_cert_exam, weeks_to_exam | Leading 4-8w (exam prep drives enrollment) |
| 5 | External | Competitor data | competitor_openings, competitor_avg_price | Inverse/complex (more competitors = split demand) |
| 6 | External | Seasonal events | is_vacation, is_exam_season, is_semester_start | Calendar-based (fixed schedule flags) |

### Feature Count Reconciliation

The original plan incorrectly stated "10 + 7 = 17 features." The correct count is:

| Group | Features | Count |
|-------|----------|-------|
| Existing | lag_1w, lag_2w, lag_4w, lag_8w, rolling_mean_4w, month_sin, month_cos, search_volume, job_count, field_encoded | 10 |
| New Internal | consultation_count, conversion_rate, page_views, cart_abandon_rate, age_group_diversity | 5 |
| New External | has_cert_exam, weeks_to_exam, competitor_openings, competitor_avg_price, is_vacation, is_exam_season, is_semester_start | 7 |
| **Total** | | **22** |

Note: Individual student profile ratios (age_20s_ratio, age_30s_ratio, age_40plus_ratio, purpose_career, purpose_hobby, purpose_cert) are NOT added to FEATURE_COLUMNS directly. They are consumed via the derived `age_group_diversity` entropy feature to avoid multicollinearity (ratios sum to 1.0).

---

## Work Objectives

1. Every data type in the README has a synthetic generator producing a CSV with deterministic seed
2. All new data sources are merged into the training dataset via `merger.py`
3. New features derived from new data sources are added to `FEATURE_COLUMNS` (10 -> 22)
4. `run_all.py` orchestrates all generators
5. Binary flag columns are zero-filled (not forward-filled) after merge
6. AUGMENTABLE_FEATURES and PROTECTED_FEATURES are derived from names (not hardcoded indices)
7. All saved models are version-bumped and retrained for new feature dimensions
8. New tests validate each generator's output schema and value ranges
9. Existing tests are updated to handle dynamic feature count
10. Documentation (README.md + guide) is updated

---

## Guardrails

### Must Have
- All generators use `seed` parameter for reproducibility (including deterministic ones, for API consistency)
- All new CSVs use `[field, date]` as join keys (matching existing pattern); `seasonal_events` uses `[date]` only
- Existing CSV schemas remain unchanged (additive only)
- New features are appended to `FEATURE_COLUMNS` (never reorder existing)
- Drop-in replacement philosophy: real CSV with same schema replaces synthetic
- Binary flag columns (`has_cert_exam`, `is_vacation`, `is_exam_season`, `is_semester_start`) are zero-filled, NOT forward-filled
- `competitor_avg_price` must be clamped with `max(0, ...)` to prevent negative prices
- PEP8, docstrings on all functions

### Must NOT Have
- No changes to existing CSV output formats
- No removal or reordering of existing FEATURE_COLUMNS entries
- No breaking changes to existing test assertions (but tests may be updated for new feature count)
- No hardcoded absolute paths (use relative paths like existing code)
- No architecture redesign of the pipeline
- No hardcoded positional index lists for AUGMENTABLE/PROTECTED features

---

## Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Saved model incompatibility** | HIGH -- all existing .pt/.joblib models will fail to load after FEATURE_COLUMNS changes from 10 to 22 | CERTAIN | Step 6 explicitly bumps model version to v2 and retrains all models. v1 models are preserved but documented as incompatible. |
| **Synthetic correlation inflation** | MEDIUM -- all features are derived from enrollment_df, creating circular dependencies that inflate apparent model accuracy | HIGH | Document this limitation in the synthetic data guide. Real data replacement is the intended fix. Add a warning comment in each generator. |
| **Forward-fill corruption of binary flags** | MEDIUM -- merger.py currently ffills ALL numeric columns, which would propagate binary flags incorrectly | CERTAIN (code exists) | Step 3 explicitly handles binary columns with fillna(0) after merge. |
| **Test regression from feature count change** | MEDIUM -- test_augment_sequences hardcodes n_feat=10 | CERTAIN | Step 7 updates the test to use `len(FEATURE_COLUMNS)`. |
| **Memory pressure on Droplet** | LOW -- 22 features vs 10 increases LSTM input size but Droplet only does inference | LOW | No action needed; inference memory is negligible. |

---

## Task Flow

```
Step 1: Create internal_generator.py (consultation, student profile, web logs)
  |
  v
Step 2: Create events_generator.py (cert exams, competitor data, seasonal events)
  |
  v
Step 3: Update merger.py (LEFT JOIN all 6 new sources + binary fill fix)
  |
  v
Step 4: Update transformer.py + FEATURE_COLUMNS + LSTM index derivation
  |
  v
Step 5: Update predict.py _build_features() with explicit pseudo-code
  |
  v
Step 6: Model migration -- bump version, retrain all models
  |
  v
Step 7: Create and update tests
  |
  v
Step 8: Update run_all.py to orchestrate all generators
  |
  v
Step 9: Update documentation (README.md + guide + synthetic correlation warning)
```

---

## Step 1: Create `edupulse/data/generators/internal_generator.py`

**New file.** Three generator functions for internal data types that reference `enrollment_df` as the source of truth.

### 1a. `generate_consultation_logs(enrollment_df, seed=44) -> DataFrame`

**CSV schema:** `consultation_logs.csv`
```
date, field, consultation_count, conversion_rate, ds, y
```
- **Output path:** `data/raw/internal/consultation_logs.csv`
- **Relationship:** Leading indicator (1-2 weeks). More consultations precede higher enrollment.
- **Generation formula:**
  ```
  # Look 1-2 weeks ahead at future enrollment
  future_idx = min(i + rng.integers(1, 3), len-1)
  future_enrollment = enrollments[future_idx]
  consultation_count = round(max(0, future_enrollment * CONSULT_MULTIPLIER[field] + noise))
  conversion_rate = clip(0.15 + 0.05 * (enrollment / max_enrollment) + noise, 0.05, 0.65)
  ```
- **Constants:**
  ```python
  CONSULT_MULTIPLIER = {"coding": 3.0, "security": 2.5, "game": 2.0, "art": 1.5}
  ```
  Rationale: Each enrolled student is preceded by ~2-3x consultations (not everyone converts).

### 1b. `generate_student_profiles(enrollment_df, seed=45) -> DataFrame`

**CSV schema:** `student_profiles.csv`
```
date, field, age_20s_ratio, age_30s_ratio, age_40plus_ratio, purpose_career, purpose_hobby, purpose_cert, ds, y
```
- **Output path:** `data/raw/internal/student_profiles.csv`
- **Relationship:** Co-moving. Profile distributions shift with enrollment volume and field.
- **Generation formula:**
  ```
  # Dirichlet distribution for age ratios (sums to 1.0)
  age_ratios = rng.dirichlet(FIELD_AGE_ALPHA[field])
  # Purpose ratios also Dirichlet
  purpose_ratios = rng.dirichlet(FIELD_PURPOSE_ALPHA[field])
  ```
- **Constants per field (Dirichlet alpha):**
  ```python
  FIELD_AGE_ALPHA = {
      "coding":   [5, 3, 1],   # skews young
      "security": [3, 4, 2],   # more 30s (career changers)
      "game":     [6, 2, 1],   # very young
      "art":      [3, 3, 3],   # balanced
  }
  FIELD_PURPOSE_ALPHA = {
      "coding":   [5, 2, 2],   # career-focused
      "security": [3, 1, 5],   # cert-focused
      "game":     [3, 4, 1],   # hobby-heavy
      "art":      [2, 5, 1],   # hobby-heavy
  }
  ```
- **Feature derivation:** `age_group_diversity` = Shannon entropy of age ratios (higher entropy = more diverse = stable demand). Computed in transformer.py using **vectorized numpy** (not apply+lambda).

### 1c. `generate_web_logs(enrollment_df, seed=46) -> DataFrame`

**CSV schema:** `web_logs.csv`
```
date, field, page_views, cart_abandon_rate, ds, y
```
- **Output path:** `data/raw/internal/web_logs.csv`
- **Relationship:** Leading 1-3 weeks. Page views spike before enrollment; cart abandonment inversely correlates.
- **Generation formula:**
  ```
  future_idx = min(i + rng.integers(1, 4), len-1)
  future_enrollment = enrollments[future_idx]
  page_views = round(max(1, future_enrollment * PV_MULTIPLIER[field] + noise))
  cart_abandon_rate = clip(0.70 - 0.03 * future_enrollment + noise, 0.20, 0.95)
  ```
- **Constants:**
  ```python
  PV_MULTIPLIER = {"coding": 15.0, "security": 12.0, "game": 18.0, "art": 10.0}
  ```
  Rationale: Each enrollment is preceded by ~10-18 page views (funnel conversion).

### Acceptance Criteria (Step 1)
- [ ] Three functions each return a DataFrame with correct schema
- [ ] All use `enrollment_df` as source, accept `seed` parameter
- [ ] Each generator is independently callable
- [ ] Prophet-compatible `ds` and `y` columns present (y = primary metric)
- [ ] Output values are realistic (no negative counts, rates between 0-1)
- [ ] Each function includes a docstring warning about synthetic correlation inflation

---

## Step 2: Create `edupulse/data/generators/events_generator.py`

**New file.** Three generator functions for external data types. These are calendar/market-based and can be generated independently of enrollment_df (but some reference it for correlation).

### 2a. `generate_cert_exam_schedule(start_year=2018, n_years=8, seed=47) -> DataFrame`

**CSV schema:** `cert_exam_schedule.csv`
```
date, field, has_cert_exam, weeks_to_exam, ds, y
```
- **Output path:** `data/raw/external/cert_exam_schedule.csv`
- **Relationship:** Leading 4-8 weeks. Cert exam dates are fixed; enrollment spikes in prep period.
- **Generation logic:**
  ```
  # Real cert exam months (approximate):
  # 정보처리기사: March, May, August (3회/년)
  # 정보보안기사: March, September (2회/년)
  # For game/art: fewer cert exams, 1-2 per year
  CERT_EXAM_MONTHS = {
      "coding":   [3, 5, 8],
      "security": [3, 9],
      "game":     [6],
      "art":      [5, 11],
  }
  # has_cert_exam = 1 if date falls within exam month, else 0
  # weeks_to_exam: see formula below
  ```
- **`weeks_to_exam` computation formula:**
  ```python
  def _weeks_to_next_exam(current_date: date, field: str) -> int:
      """Find the next cert exam date and return weeks until it.

      For each field, exam dates are placed on the 15th of each exam month.
      Searches forward from current_date up to 12 months.
      If no exam within 12 months, returns 26 (cap).

      Returns:
          int: weeks to next exam, capped at 26.
      """
      exam_months = CERT_EXAM_MONTHS[field]
      for month_offset in range(13):  # 0..12 months ahead
          check_date = current_date + relativedelta(months=month_offset)
          check_month = check_date.month if month_offset == 0 else (current_date + relativedelta(months=month_offset)).month
          # Find next exam month >= current month (or wrap to next year)
          for exam_month in sorted(exam_months):
              exam_date = date(check_date.year, exam_month, 15)
              if exam_date >= current_date:
                  weeks = (exam_date - current_date).days // 7
                  return min(weeks, 26)
      return 26  # cap
  ```
- **No enrollment_df dependency.** This is purely calendar-based.
- **Accepts `seed` parameter** for API consistency even though output is deterministic.

### 2b. `generate_competitor_data(enrollment_df, seed=48) -> DataFrame`

**CSV schema:** `competitor_data.csv`
```
date, field, competitor_openings, competitor_avg_price, ds, y
```
- **Output path:** `data/raw/external/competitor_data.csv`
- **Relationship:** Inverse/split. More competitor openings may split or stimulate demand.
- **Generation formula:**
  ```
  # Competitor openings follow similar seasonality but with noise
  competitor_openings = round(max(0, enrollment * COMP_RATIO[field] + seasonal + noise))
  # Price = base_price * (1 + demand_factor + noise), clamped to non-negative
  raw_price = BASE_PRICE[field] * (1 + 0.1 * norm_enrollment + noise)
  competitor_avg_price = round(max(0, raw_price), -4)  # max(0) guard
  ```
- **Constants:**
  ```python
  COMP_RATIO = {"coding": 1.2, "security": 0.8, "game": 0.6, "art": 0.5}
  BASE_PRICE = {"coding": 500000, "security": 600000, "game": 450000, "art": 400000}
  ```

### 2c. `generate_seasonal_events(start_year=2018, n_years=8, seed=47) -> DataFrame`

**CSV schema:** `seasonal_events.csv`
```
date, is_vacation, is_exam_season, is_semester_start
```
- **Output path:** `data/raw/external/seasonal_events.csv`
- **Relationship:** Calendar-based binary flags. No randomness needed (deterministic).
- **Accepts `seed` parameter** for API consistency even though output is deterministic.
- **Generation logic:**
  ```python
  # Deterministic
  is_vacation:       month in [1, 2, 7, 8]
  is_exam_season:    month in [6, 11, 12]   # 중간/기말/수능
  is_semester_start: month in [3, 9]
  ```
- **Note:** These are NOT field-specific. One row per week (not per field). The merger will broadcast-join on date only.

### Acceptance Criteria (Step 2)
- [ ] Three functions produce DataFrames with correct schema
- [ ] `cert_exam_schedule` and `seasonal_events` are deterministic (no enrollment dependency)
- [ ] All three functions accept a `seed` parameter (even if deterministic)
- [ ] `competitor_data` uses enrollment_df as base signal
- [ ] `competitor_avg_price` is always >= 0 (max(0) guard in place)
- [ ] `weeks_to_exam` correctly computes countdown to next exam date per field
- [ ] `seasonal_events` has no `field` column (global calendar)
- [ ] All date ranges match enrollment_df's range (2018-2025)

---

## Step 3: Update `edupulse/preprocessing/merger.py`

### 3a. `merge_datasets()` signature expansion

Add optional parameters for all 6 new DataFrames:
```python
def merge_datasets(
    enrollment_df,
    search_df=None,
    job_df=None,
    consultation_df=None,     # NEW
    student_profile_df=None,  # NEW
    web_log_df=None,          # NEW
    cert_exam_df=None,        # NEW
    competitor_df=None,        # NEW
    seasonal_df=None,          # NEW
    date_col="date",
) -> pd.DataFrame:
```

**Join strategy:**
- `consultation_df`, `student_profile_df`, `web_log_df`, `competitor_df`, `cert_exam_df`: LEFT JOIN on `[field, date]`
- `seasonal_df`: LEFT JOIN on `[date]` only (no field column)

**Columns to select per source (avoid pulling in `ds`, `y` duplicates):**
| Source | Columns to merge |
|--------|-----------------|
| consultation_df | consultation_count, conversion_rate |
| student_profile_df | age_20s_ratio, age_30s_ratio, age_40plus_ratio, purpose_career, purpose_hobby, purpose_cert |
| web_log_df | page_views, cart_abandon_rate |
| cert_exam_df | has_cert_exam, weeks_to_exam |
| competitor_df | competitor_openings, competitor_avg_price |
| seasonal_df | is_vacation, is_exam_season, is_semester_start |

### 3b. Binary flag fill fix (CRITICAL)

After all merges, handle binary flag columns separately from the general forward-fill:

```python
# Identify binary flag columns that must be zero-filled, NOT forward-filled
BINARY_FLAG_COLUMNS = ["has_cert_exam", "is_vacation", "is_exam_season", "is_semester_start"]

# Forward fill continuous numeric columns
numeric_cols = merged.select_dtypes(include="number").columns
continuous_cols = [c for c in numeric_cols if c not in BINARY_FLAG_COLUMNS]
merged[continuous_cols] = merged[continuous_cols].ffill()

# Zero-fill binary flags (missing = event not occurring)
binary_present = [c for c in BINARY_FLAG_COLUMNS if c in merged.columns]
merged[binary_present] = merged[binary_present].fillna(0).astype(int)
```

### 3c. `build_training_dataset()` update

Load all new CSVs with `_load_csv_safe()` and pass them to `merge_datasets()`:
```python
consultation_df = _load_csv_safe(os.path.join(raw_internal_dir, "consultation_logs.csv"))
student_profile_df = _load_csv_safe(os.path.join(raw_internal_dir, "student_profiles.csv"))
web_log_df = _load_csv_safe(os.path.join(raw_internal_dir, "web_logs.csv"))
cert_exam_df = _load_csv_safe(os.path.join(raw_external_dir, "cert_exam_schedule.csv"))
competitor_df = _load_csv_safe(os.path.join(raw_external_dir, "competitor_data.csv"))
seasonal_df = _load_csv_safe(os.path.join(raw_external_dir, "seasonal_events.csv"))
```

### Acceptance Criteria (Step 3)
- [ ] `merge_datasets()` accepts all new optional DataFrames without breaking existing calls (backward compatible)
- [ ] `build_training_dataset()` loads all available CSVs (graceful if missing)
- [ ] Binary flag columns (`has_cert_exam`, `is_vacation`, `is_exam_season`, `is_semester_start`) are filled with 0, NOT forward-filled
- [ ] Continuous numeric columns are still forward-filled as before
- [ ] Existing test `test_merge_datasets` still passes unchanged
- [ ] Duplicate `ds`/`y` columns from source DataFrames are excluded during merge

---

## Step 4: Update `edupulse/preprocessing/transformer.py` and `edupulse/model/xgboost_model.py` and `edupulse/model/lstm_model.py`

### 4a. `transformer.py` -- `add_lag_features()` additions

Add after existing feature generation, using **vectorized numpy** (not apply+lambda):
```python
# Shannon entropy for age group diversity (if profile columns present)
if all(c in df.columns for c in ["age_20s_ratio", "age_30s_ratio", "age_40plus_ratio"]):
    age_cols = df[["age_20s_ratio", "age_30s_ratio", "age_40plus_ratio"]].values
    # Vectorized Shannon entropy: -sum(p * log(p + eps))
    eps = 1e-10
    df["age_group_diversity"] = -np.sum(age_cols * np.log(age_cols + eps), axis=1)
```

No additional derived features needed for other sources -- their raw columns are directly usable as features.

### 4b. `xgboost_model.py` -- FEATURE_COLUMNS expansion

```python
FEATURE_COLUMNS = [
    # --- Existing (10) ---
    "lag_1w", "lag_2w", "lag_4w", "lag_8w",
    "rolling_mean_4w", "month_sin", "month_cos",
    "search_volume", "job_count", "field_encoded",
    # --- New: Internal data (5) ---
    "consultation_count",
    "conversion_rate",
    "page_views",
    "cart_abandon_rate",
    "age_group_diversity",
    # --- New: External data (7) ---
    "has_cert_exam",
    "weeks_to_exam",
    "competitor_openings",
    "competitor_avg_price",
    "is_vacation",
    "is_exam_season",
    "is_semester_start",
]
```

**Total: 10 existing + 5 new internal + 7 new external = 22 features.**

### 4c. `lstm_model.py` -- Name-based feature index derivation (CRITICAL)

Replace the hardcoded positional index lists with name-based derivation:

```python
# BEFORE (fragile, breaks when FEATURE_COLUMNS changes):
# AUGMENTABLE_FEATURES = [0, 1, 2, 3, 4, 7, 8]
# PROTECTED_FEATURES = [5, 6, 9]

# AFTER (robust, automatically adapts to FEATURE_COLUMNS changes):
_PROTECTED_NAMES = {
    "month_sin", "month_cos", "field_encoded",
    "has_cert_exam", "is_vacation", "is_exam_season", "is_semester_start",
}
PROTECTED_FEATURES = [i for i, c in enumerate(FEATURE_COLUMNS) if c in _PROTECTED_NAMES]
AUGMENTABLE_FEATURES = [i for i, c in enumerate(FEATURE_COLUMNS) if c not in _PROTECTED_NAMES]
```

This automatically produces the correct indices regardless of FEATURE_COLUMNS order or length.

### Acceptance Criteria (Step 4)
- [ ] FEATURE_COLUMNS has exactly 22 entries (10 existing + 5 new internal + 7 new external)
- [ ] Existing 10 features are in the same order (indices 0-9 unchanged)
- [ ] `age_group_diversity` is derived in transformer.py using vectorized numpy (no `apply(lambda)`)
- [ ] LSTM's AUGMENTABLE_FEATURES and PROTECTED_FEATURES are derived from `_PROTECTED_NAMES` set (not hardcoded indices)
- [ ] `_PROTECTED_NAMES` includes all binary/cyclical features: month_sin, month_cos, field_encoded, has_cert_exam, is_vacation, is_exam_season, is_semester_start
- [ ] `INPUT_SIZE = len(FEATURE_COLUMNS)` continues to be computed dynamically (already the case)
- [ ] Model gracefully handles missing columns via `available = [c for c in FEATURE_COLUMNS if c in df.columns]`

---

## Step 5: Update `edupulse/model/predict.py` -- `_build_features()` with explicit logic

### 5a. New CSV path constants

```python
_CONSULTATION_PATH = "edupulse/data/raw/internal/consultation_logs.csv"
_STUDENT_PROFILES_PATH = "edupulse/data/raw/internal/student_profiles.csv"
_WEB_LOGS_PATH = "edupulse/data/raw/internal/web_logs.csv"
_CERT_EXAM_PATH = "edupulse/data/raw/external/cert_exam_schedule.csv"
_COMPETITOR_PATH = "edupulse/data/raw/external/competitor_data.csv"
_SEASONAL_PATH = "edupulse/data/raw/external/seasonal_events.csv"
```

### 5b. Feature loading pseudo-code for each new source

Each follows the same pattern as existing search_volume/job_count loading: load CSV, filter to field (if applicable) and dates before target_date, take the most recent row.

```python
# --- 6) consultation_count, conversion_rate ---
consultation_count, conversion_rate = 0.0, 0.0
if os.path.exists(_CONSULTATION_PATH):
    try:
        consult_df = pd.read_csv(_CONSULTATION_PATH)
        consult_df["date"] = pd.to_datetime(consult_df["date"])
        field_consult = consult_df[consult_df["field"] == field].sort_values("date")
        prior = field_consult[field_consult["date"] < target_date]
        if len(prior) >= 1:
            consultation_count = float(prior.iloc[-1]["consultation_count"])
            conversion_rate = float(prior.iloc[-1]["conversion_rate"])
    except Exception as e:
        logger.warning("상담 로그 로딩 실패: %s", e)

# --- 7) page_views, cart_abandon_rate ---
page_views, cart_abandon_rate = 0.0, 0.0
if os.path.exists(_WEB_LOGS_PATH):
    try:
        web_df = pd.read_csv(_WEB_LOGS_PATH)
        web_df["date"] = pd.to_datetime(web_df["date"])
        field_web = web_df[web_df["field"] == field].sort_values("date")
        prior = field_web[field_web["date"] < target_date]
        if len(prior) >= 1:
            page_views = float(prior.iloc[-1]["page_views"])
            cart_abandon_rate = float(prior.iloc[-1]["cart_abandon_rate"])
    except Exception as e:
        logger.warning("웹 로그 로딩 실패: %s", e)

# --- 8) age_group_diversity (from student_profiles.csv) ---
age_group_diversity = 0.0
if os.path.exists(_STUDENT_PROFILES_PATH):
    try:
        profile_df = pd.read_csv(_STUDENT_PROFILES_PATH)
        profile_df["date"] = pd.to_datetime(profile_df["date"])
        field_profile = profile_df[profile_df["field"] == field].sort_values("date")
        prior = field_profile[field_profile["date"] < target_date]
        if len(prior) >= 1:
            row = prior.iloc[-1]
            age_ratios = [
                float(row["age_20s_ratio"]),
                float(row["age_30s_ratio"]),
                float(row["age_40plus_ratio"]),
            ]
            # Shannon entropy
            import math as _math
            age_group_diversity = -sum(
                p * _math.log(p + 1e-10) for p in age_ratios
            )
    except Exception as e:
        logger.warning("학생 프로필 로딩 실패: %s", e)

# --- 9) has_cert_exam, weeks_to_exam ---
has_cert_exam, weeks_to_exam = 0.0, 26.0  # default: no exam, max distance
if os.path.exists(_CERT_EXAM_PATH):
    try:
        cert_df = pd.read_csv(_CERT_EXAM_PATH)
        cert_df["date"] = pd.to_datetime(cert_df["date"])
        field_cert = cert_df[cert_df["field"] == field].sort_values("date")
        # Find the row closest to (but not after) the target_date
        prior = field_cert[field_cert["date"] <= target_date]
        if len(prior) >= 1:
            has_cert_exam = float(prior.iloc[-1]["has_cert_exam"])
            weeks_to_exam = float(prior.iloc[-1]["weeks_to_exam"])
    except Exception as e:
        logger.warning("자격증 일정 로딩 실패: %s", e)

# --- 10) competitor_openings, competitor_avg_price ---
competitor_openings, competitor_avg_price = 0.0, 0.0
if os.path.exists(_COMPETITOR_PATH):
    try:
        comp_df = pd.read_csv(_COMPETITOR_PATH)
        comp_df["date"] = pd.to_datetime(comp_df["date"])
        field_comp = comp_df[comp_df["field"] == field].sort_values("date")
        prior = field_comp[field_comp["date"] < target_date]
        if len(prior) >= 1:
            competitor_openings = float(prior.iloc[-1]["competitor_openings"])
            competitor_avg_price = float(prior.iloc[-1]["competitor_avg_price"])
    except Exception as e:
        logger.warning("경쟁 학원 데이터 로딩 실패: %s", e)

# --- 11) is_vacation, is_exam_season, is_semester_start ---
# seasonal_events has no field column -- lookup by date only
is_vacation, is_exam_season, is_semester_start = 0.0, 0.0, 0.0
if os.path.exists(_SEASONAL_PATH):
    try:
        seasonal_df = pd.read_csv(_SEASONAL_PATH)
        seasonal_df["date"] = pd.to_datetime(seasonal_df["date"])
        prior = seasonal_df[seasonal_df["date"] <= target_date].sort_values("date")
        if len(prior) >= 1:
            is_vacation = float(prior.iloc[-1]["is_vacation"])
            is_exam_season = float(prior.iloc[-1]["is_exam_season"])
            is_semester_start = float(prior.iloc[-1]["is_semester_start"])
    except Exception as e:
        logger.warning("계절 이벤트 로딩 실패: %s", e)
```

### 5c. Assemble all features into the row dict

```python
row = {
    # existing features (unchanged)
    "date": start_date,
    "lag_1w": lag_1w, "lag_2w": lag_2w, "lag_4w": lag_4w, "lag_8w": lag_8w,
    "rolling_mean_4w": rolling_mean_4w,
    "month_sin": month_sin, "month_cos": month_cos,
    "search_volume": search_volume, "job_count": job_count,
    "field_encoded": field_encoded,
    # new internal features
    "consultation_count": consultation_count,
    "conversion_rate": conversion_rate,
    "page_views": page_views,
    "cart_abandon_rate": cart_abandon_rate,
    "age_group_diversity": age_group_diversity,
    # new external features
    "has_cert_exam": has_cert_exam,
    "weeks_to_exam": weeks_to_exam,
    "competitor_openings": competitor_openings,
    "competitor_avg_price": competitor_avg_price,
    "is_vacation": is_vacation,
    "is_exam_season": is_exam_season,
    "is_semester_start": is_semester_start,
}
```

### Acceptance Criteria (Step 5)
- [ ] `_build_features()` populates all 22 features (default 0.0 if CSV missing)
- [ ] `seasonal_events` is loaded by date only (no field filter)
- [ ] `age_group_diversity` is computed from student profile ratios using Shannon entropy at inference time
- [ ] All new CSV loads follow the existing try/except + logger.warning pattern
- [ ] `weeks_to_exam` defaults to 26.0 (max cap) when no data available

---

## Step 6: Model Migration -- Version Bump and Retraining

### Why this step is necessary

Changing FEATURE_COLUMNS from 10 to 22 makes ALL existing saved models incompatible:
- **LSTM:** `INPUT_SIZE` changes from 10 to 22. Existing `.pt` files have weight matrices shaped for 10 features and will fail to load with `size mismatch` error.
- **XGBoost:** Existing `.joblib` models were fitted on 10 features. Predicting with 22 features will raise `feature_names mismatch` error.
- **Prophet:** Uses `ds`/`y` columns directly (not FEATURE_COLUMNS), so Prophet models are NOT affected. However, for consistency, they should be retrained with the enriched dataset.

### Migration procedure

```
1. Preserve existing models:
   model/saved/xgboost/v1/  -- keep as-is (archived)
   model/saved/lstm/v1/     -- keep as-is (archived)
   model/saved/prophet/v1/  -- keep as-is (archived)

2. Generate all synthetic data:
   python -m edupulse.data.generators.run_all

3. Build new training dataset with all 22 features:
   python -m edupulse.preprocessing.merger  (or call build_training_dataset())

4. Retrain all models and save as v2:
   python -m edupulse.model.train --version 2
   This saves to model/saved/{model_name}/v2/

5. Update default version in predict.py:
   Change version default from 1 to 2 in predict_demand() signature
```

### Acceptance Criteria (Step 6)
- [ ] v1 model files are preserved (not deleted)
- [ ] v2 models are trained on the full 22-feature dataset
- [ ] `predict_demand()` default version parameter is updated to `version=2`
- [ ] LSTM v2 model.pt has weight matrices shaped for 22 input features
- [ ] XGBoost v2 model.joblib is fitted on 22 features
- [ ] A brief incompatibility note is added as a comment in `predict.py` near the version default

---

## Step 7: Create and Update Tests

### 7a. Fix `test_augment_sequences` in `tests/test_model.py` (CRITICAL)

The current test at line 196 hardcodes `n_feat=10`:
```python
# BEFORE (breaks when FEATURE_COLUMNS grows):
n_seq, seq_len, n_feat = 20, 12, 10

# AFTER (dynamically adapts):
from edupulse.model.xgboost_model import FEATURE_COLUMNS
n_seq, seq_len, n_feat = 20, 12, len(FEATURE_COLUMNS)
```

Also update the shape assertion at line 203:
```python
assert aug_xs.shape == (n_seq * 3, seq_len, n_feat)
```
This already uses `n_feat` so it will work once the variable is derived from `FEATURE_COLUMNS`.

### 7b. Create `tests/test_generators.py` (NEW)

New test file with the following test functions:

```python
def test_generate_consultation_logs_schema():
    """consultation_logs has correct columns and value ranges."""
    # Verify: date, field, consultation_count >= 0, 0 < conversion_rate < 1, ds, y

def test_generate_student_profiles_ratios_sum_to_one():
    """age ratios and purpose ratios each sum to ~1.0 for every row."""

def test_generate_web_logs_schema():
    """web_logs has correct columns, page_views >= 1, 0 < cart_abandon_rate < 1."""

def test_generate_cert_exam_deterministic():
    """cert_exam_schedule produces identical output across multiple calls (no seed dependency)."""

def test_generate_cert_exam_weeks_to_exam_range():
    """weeks_to_exam is between 0 and 26 inclusive."""

def test_generate_competitor_price_non_negative():
    """competitor_avg_price is always >= 0."""

def test_generate_seasonal_events_no_field_column():
    """seasonal_events has no 'field' column."""

def test_generate_seasonal_events_deterministic():
    """seasonal_events produces identical output across multiple calls."""

def test_all_generators_accept_seed():
    """Every generator function accepts a seed parameter."""

def test_run_all_produces_nine_csvs(tmp_path):
    """run_all() generates 9 CSV files in the correct directories."""
```

### 7c. Update existing tests that may reference FEATURE_COLUMNS length

Search for any other hardcoded `10` or `n_feat` assumptions in the test suite and update them.

### Acceptance Criteria (Step 7)
- [ ] `test_augment_sequences` uses `n_feat = len(FEATURE_COLUMNS)` instead of hardcoded 10
- [ ] `tests/test_generators.py` exists with at least 10 test functions covering all 6 new generators
- [ ] Each generator test validates: schema (columns present), value ranges, determinism where expected
- [ ] `test_generate_competitor_price_non_negative` specifically validates the max(0) guard
- [ ] `test_all_generators_accept_seed` validates API consistency
- [ ] All existing tests in `tests/test_model.py` still pass after FEATURE_COLUMNS expansion
- [ ] `pytest tests/` runs green with zero failures

---

## Step 8: Update `edupulse/data/generators/run_all.py`

Add steps 4-9 to the orchestrator:

```python
# 4. Consultation logs
consultation_df = generate_consultation_logs(enrollment_df)
# save to INTERNAL_DIR / "consultation_logs.csv"

# 5. Student profiles
student_profile_df = generate_student_profiles(enrollment_df)
# save to INTERNAL_DIR / "student_profiles.csv"

# 6. Web logs
web_log_df = generate_web_logs(enrollment_df)
# save to INTERNAL_DIR / "web_logs.csv"

# 7. Cert exam schedule
cert_exam_df = generate_cert_exam_schedule(start_year, n_years)
# save to EXTERNAL_DIR / "cert_exam_schedule.csv"

# 8. Competitor data
competitor_df = generate_competitor_data(enrollment_df)
# save to EXTERNAL_DIR / "competitor_data.csv"

# 9. Seasonal events
seasonal_df = generate_seasonal_events(start_year, n_years)
# save to EXTERNAL_DIR / "seasonal_events.csv"
```

Each step prints row count and summary stats, following the existing pattern.

### Acceptance Criteria (Step 8)
- [ ] `python -m edupulse.data.generators.run_all` generates all 9 CSVs without error
- [ ] All CSVs land in correct directories (internal vs external)
- [ ] Console output shows row counts and summary stats for each
- [ ] Existing 3 CSVs are unchanged in content (same seed = same output)

---

## Step 9: Update Documentation

### 9a. `README.md` -- Data Pipeline section

Update the data collection section to indicate which data types now have synthetic generators vs. real collection:

```markdown
**Internal data** -- synthetic generators implemented
- Enrollment history: per-cohort enrollment counts, early closure history
- Consultation logs: inquiry counts, conversion rates
- Student profiles: age group, occupation, enrollment purpose
- Web/app logs: page views, cart abandonment rates

**External data** -- synthetic generators implemented
- Naver DataLab / Google Trends: keyword search volume trends
- Job posting crawling: per-field job posting counts
- Cert exam schedules: exam dates and countdown
- Competitor monitoring: opening schedules and pricing
- Seasonal events: vacation, exam season, semester start cycles
```

### 9b. `docs/합성_데이터_생성_가이드.md`

Add sections 10-15 covering each new generator with:
- Design intent (why this data matters)
- CSV schema
- Generation formula with constants
- Example calculation
- Real data replacement notes

Update section 2 (data generation structure) diagram to include all 9 generators.
Update section 7 (data relationship diagram) to show new data flows.
Update section 8 (real data transition guide) with new CSV format specifications.
Update section 9 (file map) with new files.

### 9c. Synthetic correlation inflation warning

Add a new section to the guide documenting this limitation:

```markdown
## Synthetic Data Limitations

**Correlation inflation warning:** All synthetic data sources derive their values
from `enrollment_df`. This means synthetic features have artificially high
correlation with the target variable (enrollment_count). Model accuracy metrics
computed on synthetic data will be optimistically biased.

This is by design -- synthetic data validates the pipeline architecture, not
model accuracy. When real data replaces synthetic generators, expect:
- Lower apparent accuracy initially (genuine signal vs. artificial correlation)
- Feature importance rankings to shift significantly
- Some features may become non-predictive and can be dropped
```

### Acceptance Criteria (Step 9)
- [ ] README shows all 9 data types with completion indicators
- [ ] Guide has a section for each of the 6 new generators
- [ ] All CSV schemas are documented with example rows
- [ ] Updated relationship diagram shows all 9 data sources flowing into merger
- [ ] Synthetic correlation inflation warning is documented in the guide
- [ ] Model version migration (v1 -> v2) is mentioned in relevant docs

---

## Success Criteria

1. `python -m edupulse.data.generators.run_all` produces 9 CSV files (3 existing + 6 new)
2. `python -m edupulse.preprocessing.merger` builds a training dataset with 22 features
3. All existing tests pass (`pytest tests/` green) after `test_augment_sequences` fix
4. New `tests/test_generators.py` has >= 10 tests, all passing
5. FEATURE_COLUMNS has exactly 22 entries: 10 existing + 5 internal + 7 external
6. AUGMENTABLE_FEATURES and PROTECTED_FEATURES are derived from `_PROTECTED_NAMES` (no hardcoded indices)
7. Binary flags are zero-filled (not forward-filled) in merger.py
8. v2 models are trained and saved; `predict_demand()` defaults to version=2
9. `competitor_avg_price` is clamped to non-negative values
10. Documentation fully covers all data types, model migration, and synthetic data limitations

---

## New Files Summary

| File | Type | Description |
|------|------|-------------|
| `edupulse/data/generators/internal_generator.py` | New | Consultation, student profile, web log generators |
| `edupulse/data/generators/events_generator.py` | New | Cert exam, competitor, seasonal event generators |
| `tests/test_generators.py` | New | Tests for all 6 new generators + run_all integration |

## Modified Files Summary

| File | Change |
|------|--------|
| `edupulse/data/generators/run_all.py` | Add steps 4-9 for new generators |
| `edupulse/preprocessing/merger.py` | Expand merge_datasets() + binary flag fill fix + build_training_dataset() |
| `edupulse/preprocessing/transformer.py` | Add vectorized age_group_diversity derivation |
| `edupulse/model/xgboost_model.py` | Expand FEATURE_COLUMNS (10 -> 22) |
| `edupulse/model/lstm_model.py` | Replace hardcoded indices with name-based derivation |
| `edupulse/model/predict.py` | Load new CSVs in _build_features(), bump default version to 2 |
| `tests/test_model.py` | Fix test_augment_sequences to use len(FEATURE_COLUMNS) |
| `README.md` | Update data collection section |
| `docs/합성_데이터_생성_가이드.md` | Add 6 new generator docs + correlation warning + update diagrams |

---

## RALPLAN-DR Summary

### Principles (5)

1. **Additive-only changes** -- Never modify existing output formats or reorder FEATURE_COLUMNS. New features are appended.
2. **Drop-in replacement** -- Every synthetic CSV defines the exact schema that real data must match. Generators are placeholders.
3. **Enrollment as source of truth** -- All correlated generators derive from enrollment_df, maintaining realistic cross-variable relationships. This creates known correlation inflation (documented as a limitation).
4. **Deterministic reproducibility** -- Every generator accepts a `seed` parameter. Same seed = same output, always.
5. **Graceful degradation** -- Missing CSVs produce 0.0 feature values (not crashes). The model works with any subset of features via `available = [c for c in FEATURE_COLUMNS if c in df.columns]`.

### Decision Drivers (Top 3)

1. **Pipeline compatibility** -- New data must flow through existing merger -> cleaner -> transformer -> model chain without breaking any step.
2. **Realistic correlations** -- Synthetic data must encode plausible real-world relationships (leading/lagging/co-moving indicators) so the model architecture is validated even before real data arrives.
3. **Minimal model disruption** -- The existing `available = [c for c in FEATURE_COLUMNS if c in df.columns]` pattern means adding features is safe; models use what exists and ignore what's missing.

### Viable Options

#### Option A: Two New Generator Files (RECOMMENDED)

Split new generators into `internal_generator.py` (3 functions) and `events_generator.py` (3 functions).

| Pros | Cons |
|------|------|
| Clean separation: internal vs external data | Two new files to maintain |
| Follows existing pattern (enrollment_generator = internal, external_generator = external) | events_generator mixes calendar + market data |
| Each file stays under 200 lines | -- |
| Parallel development possible | -- |

#### Option B: Single `additional_generator.py` File

All 6 new generators in one file.

| Pros | Cons |
|------|------|
| One file to find everything new | 400+ line file, harder to navigate |
| Simple import | Mixes internal/external concerns |
| -- | Breaks the existing naming convention (internal vs external separation) |

#### Option C: Extend Existing Generator Files

Add consultation/student/web to `enrollment_generator.py`, add cert/competitor/seasonal to `external_generator.py`.

| Pros | Cons |
|------|------|
| No new files | Existing files grow significantly (300+ lines each) |
| -- | Violates single-responsibility (enrollment_generator becomes "all internal data") |
| -- | Harder to review/test individual generators |
| -- | Risk of accidentally changing existing function behavior |

**Decision:** Option A. It mirrors the existing `enrollment_generator.py` (internal) / `external_generator.py` (external) split, keeps files focused, and avoids touching existing generator files.

Option B invalidated because it violates the internal/external directory structure convention already established. Option C invalidated because it risks modifying existing tested functions and creates overly large files.

### ADR (Architectural Decision Record)

**Decision:** Expand FEATURE_COLUMNS from 10 to 22 with 6 new synthetic generators, name-based feature index derivation, binary flag zero-fill, and model version migration.

**Drivers:** Pipeline compatibility (no breaking changes to existing merge/transform/model chain), realistic synthetic correlations, model dimension safety.

**Alternatives considered:**
- Option B (single file) -- rejected: violates internal/external convention
- Option C (extend existing files) -- rejected: risk to existing tested code, SRP violation

**Why chosen:** Option A maintains the established file organization pattern, allows parallel development, and minimizes risk to existing code.

**Consequences:**
- All saved models (v1) become incompatible and must be retrained as v2
- Synthetic data has artificially inflated correlations (documented limitation)
- Test suite must be updated for dynamic feature count
- 12 features are derived from enrollment_df, creating circular dependency in synthetic mode

**Follow-ups:**
- Replace synthetic generators with real data collection as it becomes available
- Re-evaluate feature importance after real data integration (some synthetic features may be dropped)
- Consider feature selection/PCA if 22 features causes overfitting with small datasets
- Monitor Droplet memory usage with larger LSTM input size during inference
