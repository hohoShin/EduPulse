# Plan: LSTM Data Improvement — Period Extension + Augmentation

**Created:** 2026-04-08
**Status:** PENDING CONFIRMATION
**Estimated Complexity:** MEDIUM
**Scope:** 3 files modified, 1 new utility function added

---

## RALPLAN-DR Summary

### Principles

1. **Data-first improvement** — More and better training data yields more reliable gains than architecture tweaks for small-data LSTM problems.
2. **Minimal blast radius** — Changes stay within the data generator and LSTM training path; XGBoost, Prophet, API, and preprocessing remain untouched.
3. **Reproducibility** — All generators use deterministic seeds; augmentation uses a separate seed so original data is unchanged.
4. **Realistic synthetic data** — Extended history must reflect real-world macro events (COVID, online education boom) rather than naive extrapolation.
5. **Augmentation at training time only** — Augmentation must never leak into evaluation, prediction, or other models.

### Decision Drivers (Top 3)

1. **Sequence count** — LSTM needs significantly more sequences for early stopping + LR scheduler to be effective. Current ~996 is too few.
2. **Signal variety** — Jittering and scaling expose the model to variations it would see in real data, reducing overfitting.
3. **Backward compatibility** — Other models (XGBoost, Prophet), the preprocessing pipeline, and all existing tests must continue to pass without modification.

### Viable Options

#### Option A: Period Extension (10 years) + Training-Time Augmentation (RECOMMENDED)

**Pros:**
- Doubles base sequence count (~996 to ~2040) via realistic historical extension
- Augmentation further multiplies to ~4000-6000 effective sequences
- Augmentation is isolated to LSTM training — zero risk to other models
- Extended history includes structural trend changes (COVID dip, recovery surge) that teach the LSTM about regime shifts

**Cons:**
- Synthetic trend transitions (especially the COVID dip) are approximations — not based on real academy data
- Augmented samples are correlated with originals — effective sample size gain is less than the raw multiplier suggests
- Slight increase in data generation time (~2x), though still under 1 second

#### Option B: Period Extension Only (No Augmentation)

**Pros:**
- Simpler change — only the generator is modified
- No risk of augmentation artifacts

**Cons:**
- Only ~2040 sequences — may still be marginal for LSTM with early stopping
- Misses the opportunity for easy variance injection that reduces overfitting
- If 2040 sequences is not enough, a follow-up augmentation task would be needed anyway

**Decision:** Option A. The augmentation adds minimal code complexity (one self-contained function in `lstm_model.py`) while providing a meaningful data multiplier. Option B is a subset of Option A and would likely require follow-up work.

---

## Context

- **Current state:** LSTM MAPE ~30-32%. Data is 5 years (2021-2025), weekly, 4 fields.
  - 1044 total rows -> ~996 sequences (SEQUENCE_LENGTH=12 sliding window)
  - Per-field: 261 weeks -> ~249 sequences
- **Root cause:** Insufficient data for LSTM to learn generalizable patterns. Early stopping triggers too early or not at all.
- **Target:** Provide enough data for LSTM early stopping + LR scheduler to be effective, targeting MAPE improvement below 30%.

---

## Work Objectives

1. Extend enrollment data generation from 5 years to 10 years with period-specific trend multipliers
2. Add jittering + scaling augmentation applied only during LSTM training
3. Update `run_all.py` defaults to use 10 years
4. Ensure all 21 existing tests continue to pass

---

## Guardrails

### Must Have
- Deterministic seed for reproducibility in both generator and augmentation
- Period-specific trend factors matching the agreed table (2016-2019, 2020, 2021-2022, 2023-2025)
- Augmentation applied ONLY inside `LSTMForecaster.train()`, after sequence building, before tensor creation
- All existing tests pass without modification
- External generator (`external_generator.py`) continues to work automatically (it derives from enrollment data)

### Must NOT Have
- No changes to XGBoost, Prophet, ensemble, or preprocessing modules
- No changes to API routers or schemas
- No augmentation applied during `evaluate()` or `predict()`
- No new dependencies added to `requirements.txt`
- No changes to FEATURE_COLUMNS, TARGET_COLUMN, or SEQUENCE_LENGTH

---

## Task Flow

```
[Step 1: Enrollment Generator] --> [Step 2: run_all.py defaults]
                                         |
                                         v
                               [Step 3: LSTM Augmentation]
                                         |
                                         v
                               [Step 4: Test Verification]
```

---

## Detailed TODOs

### Step 1: Modify `enrollment_generator.py` — Multi-Period Trend Formula

**File:** `/Users/arinhusband/PycharmProjects/EduPulse/edupulse/data/generators/enrollment_generator.py`

**What changes:**

1. Replace the simple linear trend formula with a period-aware trend function.

**Current formula (line 63):**
```python
year_offset = (week_date.year - start_year)
trend = 1.0 + 0.05 * year_offset
```

**New formula — add a helper function:**
```python
def _compute_trend(year: int) -> float:
    """Compute year-specific trend multiplier reflecting macro events.

    Period breakdown:
        2016-2019: ~3% annual growth (stable pre-COVID growth)
        2020:      -15% dip (COVID initial shock)
        2021-2022: +10% surge (online education boom)
        2023-2025: ~5% growth (normalization)
    """
    if year <= 2019:
        # Base year 2016 = 1.0, then 3% compounding
        return 1.0 * (1.03 ** (year - 2016))
    elif year == 2020:
        # 2019 level with -15% shock
        base_2019 = 1.0 * (1.03 ** 3)  # ~1.0927
        return base_2019 * 0.85
    elif year <= 2022:
        # Recovery from COVID dip with 10% annual surge
        base_2020 = 1.0 * (1.03 ** 3) * 0.85  # ~0.9288
        return base_2020 * (1.10 ** (year - 2020))
    else:
        # Normalization: 5% growth from 2022 level
        base_2022 = 1.0 * (1.03 ** 3) * 0.85 * (1.10 ** 2)  # ~1.1238
        return base_2022 * (1.05 ** (year - 2022))
```

2. Update `generate_enrollment_history()` default parameters:
   - Change `n_years: int = 5` to `n_years: int = 10`
   - Change `start_year: int = 2021` to `start_year: int = 2016`

3. Replace the inline trend calculation (line 62-63) with a call to `_compute_trend(week_date.year)`.

**Computed trend values for verification:**
| Year | Trend Multiplier |
|------|-----------------|
| 2016 | 1.000 |
| 2017 | 1.030 |
| 2018 | 1.061 |
| 2019 | 1.093 |
| 2020 | 0.929 (COVID dip) |
| 2021 | 1.022 |
| 2022 | 1.124 |
| 2023 | 1.180 |
| 2024 | 1.239 |
| 2025 | 1.301 |

**Acceptance criteria:**
- `generate_enrollment_history()` with defaults produces ~2088 rows (522 weeks x 4 fields)
- Enrollment values for year 2020 are visibly lower than 2019
- Enrollment values for 2021-2022 show recovery surge
- Calling with `n_years=5, start_year=2021` still works (backward compatible)
- Seed=42 produces identical results on repeated runs

---

### Step 2: Update `run_all.py` Defaults

**File:** `/Users/arinhusband/PycharmProjects/EduPulse/edupulse/data/generators/run_all.py`

**What changes:**

1. Update `run()` function signature (line 22):
   - Change `def run(n_years: int = 5, start_year: int = 2021)` to `def run(n_years: int = 10, start_year: int = 2016)`

That is the only change needed. The external generators (`generate_search_trends`, `generate_job_postings`) take `enrollment_df` as input, so they automatically scale to the longer period.

**Acceptance criteria:**
- Running `python -m edupulse.data.generators.run_all` produces ~2088 enrollment rows, ~2088 search trend rows, ~2088 job posting rows
- All three CSV files are saved correctly under `edupulse/data/raw/`

---

### Step 3: Add Augmentation to LSTM Training

**File:** `/Users/arinhusband/PycharmProjects/EduPulse/edupulse/model/lstm_model.py`

**What changes:**

1. Add a module-level augmentation function after `_build_sequences_per_field`:

```python
def _augment_sequences(
    xs: np.ndarray,
    ys: np.ndarray,
    *,
    jitter_std: float = 0.02,
    scale_range: tuple[float, float] = (0.95, 1.05),
    n_augments: int = 2,
    seed: int = 123,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply jittering and scaling augmentation to training sequences.

    Jittering: Add Gaussian noise (mean=0, std=jitter_std) to each feature value.
    Scaling: Multiply each sequence by a random factor in [scale_range[0], scale_range[1]].

    Args:
        xs: Original sequences, shape (n_windows, seq_len, n_features)
        ys: Original targets, shape (n_windows,)
        jitter_std: Standard deviation for Gaussian jitter noise
        scale_range: (min_scale, max_scale) for random scaling factor
        n_augments: Number of augmented copies to generate
        seed: Random seed for reproducibility

    Returns:
        Combined (original + augmented) xs and ys arrays.
    """
    if len(xs) == 0:
        return xs, ys

    rng = np.random.default_rng(seed)
    aug_xs, aug_ys = [xs], [ys]

    for _ in range(n_augments):
        # Jittering: add small Gaussian noise to features
        noise = rng.normal(0, jitter_std, size=xs.shape).astype(np.float32)
        jittered = xs + noise

        # Scaling: multiply by a per-sequence random factor
        scales = rng.uniform(
            scale_range[0], scale_range[1], size=(len(xs), 1, 1)
        ).astype(np.float32)
        scaled = jittered * scales

        # Scale targets by the same factor (squeezed to 1D)
        y_scales = scales.squeeze()
        scaled_ys = ys * y_scales

        aug_xs.append(scaled)
        aug_ys.append(scaled_ys)

    return np.concatenate(aug_xs), np.concatenate(aug_ys)
```

**Key design decisions:**
- `n_augments=2` produces 3x total data (1 original + 2 augmented) -> ~6000 sequences
- Jitter std of 0.02 is conservative — data is already MinMaxScaled to [0,1], so this adds noise in the range of ~+/-0.04 (2 sigma)
- Scaling range [0.95, 1.05] preserves relative patterns while adding mild amplitude variation
- Targets (`ys`) are scaled by the same factor as their sequences to maintain consistency
- Separate seed (123) ensures augmentation is deterministic but independent of data generation seed (42)

2. Modify `LSTMForecaster.train()` to apply augmentation after sequence building and before the train/val split:

**Current code (lines 287-299):**
```python
# 분야별 시퀀스 생성 (스케일러 fit 포함)
xs, ys = _build_sequences_per_field(
    df, FEATURE_COLUMNS, TARGET_COLUMN, SEQUENCE_LENGTH,
    self._scaler_X, self._scaler_y, fit_scalers=True,
)
if len(xs) == 0:
    raise ValueError(...)

# Train/Val 분할 (시간 순서 유지)
val_size = max(1, int(len(xs) * VAL_RATIO))
xs_train, xs_val = xs[:-val_size], xs[-val_size:]
ys_train, ys_val = ys[:-val_size], ys[-val_size:]
```

**New code:**
```python
# 분야별 시퀀스 생성 (스케일러 fit 포함)
xs, ys = _build_sequences_per_field(
    df, FEATURE_COLUMNS, TARGET_COLUMN, SEQUENCE_LENGTH,
    self._scaler_X, self._scaler_y, fit_scalers=True,
)
if len(xs) == 0:
    raise ValueError(...)

# Train/Val 분할 (시간 순서 유지) — 분할 BEFORE augmentation
val_size = max(1, int(len(xs) * VAL_RATIO))
xs_train, xs_val = xs[:-val_size], xs[-val_size:]
ys_train, ys_val = ys[:-val_size], ys[-val_size:]

# Augmentation: training data only (validation stays clean)
xs_train, ys_train = _augment_sequences(xs_train, ys_train)
```

**CRITICAL:** The train/val split happens BEFORE augmentation. This ensures:
- Validation data is never augmented (clean evaluation signal)
- No data leakage from augmented copies crossing the split boundary

3. Add `augment` parameter to `train()` signature for controllability:

```python
def train(
    self,
    df: pd.DataFrame,
    epochs: int = 100,
    learning_rate: float = 1e-3,
    patience: int = PATIENCE,
    augment: bool = True,
) -> None:
```

When `augment=False`, skip the `_augment_sequences` call. This allows tests and evaluation to bypass augmentation.

**Acceptance criteria:**
- `_augment_sequences` with default params produces 3x the input sequence count
- Augmented xs have the same shape[1:] as originals (seq_len, n_features)
- Augmentation is only applied to training split, not validation
- `train(df, augment=False)` skips augmentation (for tests)
- `evaluate()` does NOT use augmentation (no changes needed — it has its own training loops)
- `predict()` does NOT use augmentation (no changes needed — it only does inference)

---

### Step 4: Test Verification

**No test file modifications required.** All 21 existing tests should pass because:

1. `test_lstm_train_predict` calls `model.train(df, epochs=5)` — the `augment` parameter defaults to `True`, which is fine since the test uses 100-row data and augmentation just adds more sequences.
2. `test_model_comparison` calls `lstm.evaluate(df, n_splits=3)` — `evaluate()` is unchanged.
3. `test_preprocessing.py` tests are completely unaffected — no preprocessing changes.
4. Generator tests (if any) would pass since the function signature is backward-compatible.

**Verification approach:**
```bash
# 1. Regenerate data
python -m edupulse.data.generators.run_all

# 2. Verify data sizes
python -c "
import pandas as pd
df = pd.read_csv('edupulse/data/raw/internal/enrollment_history.csv')
print(f'Total rows: {len(df)}')
print(f'Fields: {df[\"field\"].nunique()}')
print(f'Weeks per field: {len(df) // df[\"field\"].nunique()}')
print(f'Year range: {pd.to_datetime(df[\"date\"]).dt.year.min()}-{pd.to_datetime(df[\"date\"]).dt.year.max()}')
print(f'Mean enrollment by year:')
df['date'] = pd.to_datetime(df['date'])
print(df.groupby(df['date'].dt.year)['enrollment_count'].mean().to_string())
"

# 3. Run full test suite
pytest tests/ -v

# 4. (Optional) Quick MAPE check
python -c "
from edupulse.preprocessing.merger import build_training_dataset
from edupulse.model.lstm_model import LSTMForecaster
df = build_training_dataset()
model = LSTMForecaster()
result = model.evaluate(df, n_splits=3)
print(f'LSTM MAPE: {result[\"mape\"]:.2f}%')
"
```

**Acceptance criteria:**
- All 21 existing tests pass (pytest returns 0 exit code)
- Data generation produces ~2088 rows across 4 fields
- Year 2020 mean enrollment is visibly lower than 2019
- LSTM evaluation completes without errors (MAPE value is secondary — the goal is that the pipeline works)

---

## Expected Data Sizes After Changes

| Metric | Before | After |
|--------|--------|-------|
| Years | 5 (2021-2025) | 10 (2016-2025) |
| Weeks per field | ~261 | ~522 |
| Total rows | ~1044 | ~2088 |
| Sequences per field (SEQUENCE_LENGTH=12) | ~249 | ~510 |
| Total sequences | ~996 | ~2040 |
| After augmentation (3x, train only) | N/A | ~5500 training + ~200 validation |
| Effective training sequences | ~896 | ~5500 |

---

## ADR (Architecture Decision Record)

**Decision:** Extend data generation to 10 years with period-specific trends and add jittering+scaling augmentation to LSTM training.

**Drivers:**
1. LSTM MAPE of 30-32% is unacceptable; root cause is insufficient training data (~996 sequences)
2. Early stopping + LR scheduler (already implemented) need more data to be effective
3. Solution must not disrupt XGBoost/Prophet which already perform well

**Alternatives considered:**
- **Option B (Extension only, no augmentation):** Rejected because ~2040 sequences may still be marginal. Augmentation provides cheap additional variance.
- **Architecture changes (deeper LSTM, attention):** Not considered — data quantity is the bottleneck, not model capacity. Revisit if MAPE remains high after data improvement.
- **Real data collection:** Not feasible — this is synthetic data for development. The generator improvement mirrors what real data collection would provide.

**Why chosen:** Option A provides the maximum data improvement with minimal code changes (3 files, ~60 lines of new code). The augmentation function is self-contained and easily tunable.

**Consequences:**
- Data regeneration required after deployment (`python -m edupulse.data.generators.run_all`)
- Existing saved model weights become stale (retrain needed)
- Slight increase in LSTM training time (~3x from augmentation) — still well within M4 MacBook capacity
- The warehouse training dataset will also be larger (~2088 vs ~1044 rows)

**Follow-ups:**
- Measure LSTM MAPE after changes. If still >25%, consider: increasing `n_augments`, adding time-warping augmentation, or architectural improvements.
- Consider adding a `--quick` flag to `run_all.py` that generates 5-year data for fast iteration.
- The trend function `_compute_trend()` could eventually be replaced with real historical data when available.

---

## Files Changed Summary

| File | Change Type | Lines Changed (est.) |
|------|-------------|---------------------|
| `edupulse/data/generators/enrollment_generator.py` | Modified | ~25 lines (new trend function + default param change) |
| `edupulse/data/generators/run_all.py` | Modified | 1 line (default params) |
| `edupulse/model/lstm_model.py` | Modified | ~45 lines (new augmentation function + train() integration) |
| `tests/*` | No changes | 0 |
