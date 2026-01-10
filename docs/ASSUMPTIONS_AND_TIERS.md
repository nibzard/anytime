# Assumptions and Guarantee Tiers

This guide explains the assumptions behind anytime-valid inference and the tier system used to communicate assumption satisfaction.

## Overview

Anytime-valid methods (confidence sequences and e-values) provide validity guarantees under optional stopping **only when their assumptions hold**. The tier system helps you understand when these guarantees are reliable.

## Guarantee Tiers

Every `Interval` and `EValue` output includes a `tier` field from the `GuaranteeTier` enum:

### `GUARANTEED`

All assumptions are satisfied. The validity guarantees (coverage, Type I error control) hold under optional stopping.

**What this means for you:**
- Confidence sequences: The true parameter is covered with at least `1-alpha` probability at all times
- E-values: Under the null, `E >= 1/alpha` occurs with probability at most `alpha`

### `CLIPPED`

Some values fell outside the declared support bounds and were clipped to the bounds.

**What this means for you:**
- The guarantees may still hold if clipping is minimal and rare
- Heavy clipping suggests a mismatch between declared support and actual data
- Consider re-specifying `support` or investigating data source issues

**Example:**
```python
# Data in [0, 1], but some values are 1.05
spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", clip_mode="clip")
cs = HoeffdingCS(spec)

cs.update(1.05)  # Gets clipped to 1.0
iv = cs.interval()
print(iv.tier)  # GuaranteeTier.CLIPPED
```

### `DIAGNOSTIC`

Assumptions are potentially violated. Do not rely on validity guarantees.

**What triggers this tier:**
- **Drift detected**: The data distribution appears to have changed (e.g., mean shifted)
- **High missingness**: Too many missing/NaN values relative to total observations
- **Assumption violations**: Specific statistical assumptions not met

**What this means for you:**
- The CS/e-value may no longer be valid
- Use the output for exploratory analysis only
- Consider resetting the CS after a known change point
- Investigate the flagged diagnostic issues

## Core Assumptions

### 1. Bounded Support

**Assumption:** All observations fall within the declared `support` bounds.

**Methods affected:** All methods (Hoeffding, Empirical Bernstein, Bernoulli)

**How to satisfy:**
- Know your data domain (e.g., conversion rates are in `[0, 1]`)
- Use `clip_mode="error"` to catch violations early
- Use `clip_mode="clip"` for automatic clipping (downgrades to `CLIPPED` tier)

### 2. Stationarity

**Assumption:** The data distribution is stationary (no drift or change points).

**Methods affected:** All methods

**How to satisfy:**
- Ensure consistent data collection process
- Use the drift detector as an early warning
- Consider segmenting data by known factors (time, user cohort)

**Note:** The drift detector is a heuristic using CUSUM-lite logic. It may produce false positives or miss subtle drifts.

### 3. Correct Specification

**Assumption:** The `kind` parameter matches the data distribution.

**Methods affected:**
- `kind="bernoulli"` for BernoulliCS, BernoulliMixtureE
- `kind="bounded"` for HoeffdingCS, EmpiricalBernsteinCS

**How to satisfy:**
- Use `kind="bernoulli"` for 0/1 data
- Use `kind="bounded"` for continuous data in `[a, b]`

### 4. Independent Observations

**Assumption:** Observations are independent and identically distributed (i.i.d.).

**Methods affected:** All methods

**How to satisfy:**
- Ensure proper randomization (e.g., in A/B tests)
- Avoid correlated data (time series, spatial data)
- Be careful with user-level metrics if multiple observations per user

## Practical Recommendations

### For Production Monitoring

```python
# Use error mode to catch assumption violations early
spec = StreamSpec(
    alpha=0.05,
    support=(0.0, 1.0),
    kind="bounded",
    two_sided=True,
    name="conversion_rate",
    clip_mode="error",  # Fail fast on bad data
)
cs = EmpiricalBernsteinCS(spec)

# Monitor tier alongside metrics
for x in data_stream:
    try:
        cs.update(x)
        iv = cs.interval()
        if iv.tier != GuaranteeTier.GUARANTEED:
            alert_team(f"Tier degraded to {iv.tier.value}: {iv.diagnostics}")
    except AssumptionViolationError as e:
        alert_team(f"Assumption violated: {e}")
```

### For Exploratory Analysis

```python
# Use clip mode to handle messy data
spec = StreamSpec(
    alpha=0.05,
    support=(0.0, 1.0),
    kind="bounded",
    two_sided=True,
    clip_mode="clip",  # Clip and continue
)
cs = EmpiricalBernsteinCS(spec)

# Check diagnostics after processing
for x in messy_data:
    cs.update(x)

iv = cs.interval()
print(f"Tier: {iv.tier.value}")
print(f"Clipped: {iv.diagnostics.clipped_count}")
print(f"Missing: {iv.diagnostics.missing_count}")
print(f"Drift detected: {iv.diagnostics.drift_detected}")
```

### For A/B Testing

```python
# Two-sample test with diagnostics
spec = ABSpec(
    alpha=0.05,
    support=(0.0, 1.0),
    kind="bernoulli",
    two_sided=True,
    name="lift",
)
cs = TwoSampleHoeffdingCS(spec)

# Check for issues
for arm, x in ab_stream:
    cs.update((arm, x))

iv = cs.interval()
if iv.tier == GuaranteeTier.DIAGNOSTIC:
    print("Warning: Tier degraded, results may not be valid")
    print(f"Diagnostics: {iv.diagnostics}")
```

## Resetting After Changes

If you detect a genuine distribution shift (not a false alarm), reset the CS:

```python
# After a known change point
cs.reset()
# Continue with new data stream
```

The reset clears all state and starts fresh with new data.

## Summary

- **GUARANTEED**: Trust the results
- **CLIPPED**: Verify clipping is minimal, proceed with caution
- **DIAGNOSTIC**: Investigate before trusting results

The tier system is your safety net. Use it to catch data issues early and avoid making decisions on invalid inference.
