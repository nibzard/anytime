# Stopping Rules and Optional Stopping

This guide explains optional stopping, why classical methods fail under peeking, and how anytime-valid methods solve this problem.

## The Problem with Optional Stopping

### Classical Intervals Fail Under Peeking

With classical (fixed-horizon) confidence intervals, repeated checking invalidates the coverage guarantee.

**Example:**
```python
# WRONG: Classical CI with optional stopping
import numpy as np
from scipy import stats

def peeking_test(data_stream, true_mean=0.5, alpha=0.05):
    """Incorrectly stop when CI excludes null."""
    for n, x in enumerate(data_stream, 1):
        sample = data_stream[:n]
        ci = stats.t.interval(1-alpha, len(sample)-1,
                             loc=np.mean(sample),
                             scale=stats.sem(sample))
        # Stop when CI excludes 0.5
        if ci[0] > 0.5 or ci[1] < 0.5:
            return n, np.mean(sample)
    return len(data_stream), np.mean(data_stream)

# This will have much higher than 5% Type I error!
```

**Why it fails:** The CI assumes a fixed sample size. When you condition on stopping early, you're cherry-picking a favorable sample, breaking the guarantee.

### P-values Under Optional Stopping

Similarly, classical p-values inflated false positives under repeated testing:

```python
# WRONG: P-value with optional stopping
def peeking_pvalue(data_stream, true_mean=0.5, alpha=0.05):
    for n, x in enumerate(data_stream, 1):
        sample = data_stream[:n]
        _, p = stats.ttest_1samp(sample, popmean=true_mean)
        if p < alpha:
            return n, p
    return len(data_stream), p

# False positive rate >> alpha
```

## The Solution: Time-Uniform Confidence Sequences

### What is a Confidence Sequence?

A **confidence sequence (CS)** is a sequence of confidence intervals `{C_t}` such that:

```
P(θ ∈ C_t for all t) ≥ 1 - α
```

This is **uniform in time**: the probability that the true parameter is in **all** intervals is at least `1-alpha`.

**Key implication:** You can stop at any time, for any reason, and the interval is still valid.

### Anytime-Valid Methods

Anytime provides two types of optional-stopping-safe inference:

1. **Confidence Sequences**: Always-valid intervals
2. **E-values**: Always-valid evidence measures

Both are designed for streaming data with optional stopping.

## Practical Stopping Rules

### 1. Exclusion Threshold (Significance)

Stop when the CI excludes a null value:

```python
from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS

spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded")
cs = EmpiricalBernsteinCS(spec)

null_hypothesis = 0.5

for x in data_stream:
    cs.update(x)
    iv = cs.interval()

    # Stop when CI excludes null (two-sided)
    if iv.hi < null_hypothesis:
        print(f"Significant decrease at t={iv.t}: lift={iv.estimate:.3f}")
        break
    elif iv.lo > null_hypothesis:
        print(f"Significant increase at t={iv.t}: lift={iv.estimate:.3f}")
        break
```

### 2. Width Threshold (Precision)

Stop when the interval is sufficiently narrow:

```python
target_width = 0.01  # 1% precision

for x in data_stream:
    cs.update(x)
    iv = cs.interval()

    if iv.width <= target_width:
        print(f"Target precision reached at t={iv.t}: {iv.estimate:.3f} ±{iv.width/2:.3f}")
        break
```

### 3. Fixed Horizon

Stop at a predetermined sample size:

```python
n_max = 1000

for i, x in enumerate(data_stream):
    cs.update(x)
    if i >= n_max:
        iv = cs.interval()
        print(f"Final estimate at t={iv.t}: {iv.estimate:.3f}")
        break
```

### 4. Combined Rules

Combine multiple criteria:

```python
n_max = 1000
target_width = 0.01
null_value = 0.5

for i, x in enumerate(data_stream):
    cs.update(x)
    iv = cs.interval()

    # Stop if significant
    if iv.hi < null_value or iv.lo > null_value:
        print(f"Significant at t={iv.t}")
        break

    # Stop if precise enough
    if iv.width <= target_width:
        print(f"Precision reached at t={iv.t}")
        break

    # Stop at max sample size
    if i >= n_max:
        print(f"Reached max sample size at t={iv.t}")
        break
```

### 5. E-value Stopping

Stop when the e-value exceeds the decision threshold:

```python
from anytime import StreamSpec
from anytime.evalues import BernoulliMixtureE

spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli")
etest = BernoulliMixtureE(spec, p0=0.5, side="ge")

for x in data_stream:
    etest.update(x)
    ev = etest.evalue()

    # Decision threshold: 1/alpha
    if ev.decision:
        print(f"Reject H0 at t={ev.t}: e={ev.e:.2f}")
        break
```

## A/B Testing Stopping Rules

### Two-Sample Significance

```python
from anytime import ABSpec
from anytime.twosample import TwoSampleEmpiricalBernsteinCS

spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded")
cs = TwoSampleEmpiricalBernsteinCS(spec)

min_obs_per_arm = 50

for arm, x in ab_stream:
    cs.update((arm, x))
    iv = cs.interval()

    # Only check after sufficient data
    if iv.t < 2 * min_obs_per_arm:
        continue

    # Stop if CI excludes 0 (no lift)
    if iv.lo > 0:
        print(f"Significant positive lift at t={iv.t}: {iv.estimate:.3f}")
        break
    elif iv.hi < 0:
        print(f"Significant negative lift at t={iv.t}: {iv.estimate:.3f}")
        break

    # Could also stop on precision
    if iv.width <= 0.01:
        print(f"Precision reached at t={iv.t}")
        break
```

## Stopping Rule Comparison

| Rule | Use Case | Pros | Cons |
|------|----------|------|------|
| Exclusion | Detect effect | Fast detection | May stop early on noise |
| Width | Precision guarantee | Direct control | May take very long |
| Fixed horizon | Resource planning | Predictable cost | May stop too early/late |
| E-value | Evidence accumulation | Valid under optional stopping | Less intuitive than CIs |

## Atlas Stopping Rules

The atlas runner supports three stopping rule types:

### Fixed Horizon

```python
from anytime.atlas.runner import AtlasRunner, fixed_horizon_rule

runner = AtlasRunner(n_sim=1000)
stopping_rule = fixed_horizon_rule(n_max=500)
```

### Exclude Threshold

```python
from anytime.atlas.runner import exclude_threshold_rule

# Stop when CI excludes 0.5
stopping_rule = exclude_threshold_rule(null_value=0.5)
```

### Periodic Looks

```python
from anytime.atlas.runner import periodic_looks_rule

# Check every 100 observations
stopping_rule = periodic_looks_rule(check_interval=100)
```

## Common Pitfalls

### 1. Stopping Too Early

Even with valid CS, stopping on tiny samples gives wide intervals:

```python
# May stop after 10 observations with very wide CI
for x in data_stream:
    cs.update(x)
    iv = cs.interval()
    if iv.lo > 0.5:
        break
# iv.width might be 0.5+ - not practically useful!
```

**Fix:** Add a minimum sample size requirement.

### 2. Ignoring Practical Significance

Statistical significance ≠ practical significance:

```python
min_sample = 1000
min_effect = 0.01  # 1% minimum lift

for i, x in enumerate(data_stream):
    cs.update(x)
    iv = cs.interval()

    if i < min_sample:
        continue

    # Stop only if practically significant
    if iv.lo > min_effect:
        print(f"Practically significant lift detected")
        break
```

### 3. Forgetting Diagnostics

If the tier degrades to `DIAGNOSTIC`, stopping rules may not be valid:

```python
for x in data_stream:
    cs.update(x)
    iv = cs.interval()

    # Check tier before making decisions
    if iv.tier.value == "diagnostic":
        print("Warning: Tier degraded")
        # Don't stop - investigate instead
        continue

    if iv.lo > 0.5:
        break
```

## Summary

- **Classical methods fail** under optional stopping (peeking)
- **Confidence sequences** remain valid at all times
- **E-values** provide optional-stopping-safe decision rules
- **Combine stopping rules** for practical experimentation
- **Check diagnostics** to ensure assumptions hold
- **Consider practical significance** alongside statistical significance

With anytime-valid methods, you can monitor continuously and stop whenever you want—without inflating false positives.
