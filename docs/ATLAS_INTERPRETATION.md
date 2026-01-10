# Atlas Interpretation Guide

This guide explains how to interpret atlas benchmark results and understand the performance characteristics of confidence sequence methods.

## What is the Atlas?

The **atlas** is a benchmarking framework that:
- Runs Monte Carlo simulations across scenarios
- Computes anytime-valid coverage, Type I error, and power
- Compares methods (Hoeffding, Empirical Bernstein, Bernoulli)
- Generates reports with tables and plots

## Key Metrics

### Coverage (Anytime)

**Definition:** Proportion of simulations where the true parameter was in the confidence interval at **all** times.

**Target:** `≥ 0.95` for `alpha = 0.05`

**Interpretation:**
- Coverage < 0.95: Method is **anti-conservative** (too optimistic)
- Coverage ≥ 0.95: Method is **valid** (guarantee holds)
- Coverage >> 0.95: Method is **conservative** (wider intervals than necessary)

**Example:**
```
| Scenario        | Hoeffding | EmpiricalBernstein |
|-----------------|-----------|-------------------|
| bernoulli_p05   | **0.982** | 0.951             |
```

Bold indicates nominal coverage (≥ 0.95). Both methods are valid.

### Final Coverage

**Definition:** Proportion of simulations where the true parameter was in the confidence interval at the **final** time point only.

**Target:** `≥ 0.95` for `alpha = 0.05`

**Note:** Final coverage can be higher than anytime coverage because it only checks one time point, not all times.

### Type I Error

**Definition:** Proportion of null scenarios (true_effect = 0) where the confidence interval **excluded** the null value.

**Target:** `≤ alpha` (≤ 0.05 for alpha=0.05)

**Interpretation:**
- Type I error > alpha: False positive rate too high (method is anti-conservative)
- Type I error ≤ alpha: False positive rate controlled (method is valid)

**Example:**
```
| Scenario        | Type I Error |
|-----------------|--------------|
| null_bernoulli  | **0.043**    |  # Good: ≤ 0.05
| null_bounded    | 0.067        |  # Bad: > 0.05
```

### Power

**Definition:** Proportion of alternative scenarios (true_effect ≠ 0) where the confidence interval **excluded** the null value.

**Interpretation:**
- Higher power = better detection of true effects
- Power depends on effect size, sample size, and method

**Trade-off:** Conservative methods (high coverage) tend to have lower power.

**Example:**
```
| Scenario    | Power  |
|-------------|--------|
| lift_01     | 0.23   |  # Small effect, hard to detect
| lift_05     | 0.87   |  # Larger effect, easier to detect
```

### Average Width

**Definition:** Average width of confidence intervals across simulations and time points.

**Interpretation:**
- Smaller width = more precise estimates
- Width typically decreases with more data
- Variance-adaptive methods (Empirical Bernstein) have smaller width when variance is low

**Example:**
```
| Scenario    | Avg Width |
|-------------|-----------|
| hoeffding   | 0.124     |
| empirical_bernstein | 0.087  |  # Tighter (variance-adaptive)
```

### Median Stop Time

**Definition:** Median time (sample size) when the stopping rule was triggered.

**Interpretation:**
- Shorter stop time = faster decisions
- Depends on stopping rule and effect size

**Example:**
```
| Scenario    | Median Stop Time |
|-------------|------------------|
| lift_10     | 52               |  # Large effect, stops early
| lift_02     | 487              |  # Small effect, takes longer
```

## Method Comparison

### Hoeffding CS

**Characteristics:**
- Always valid for bounded data
- Conservative (wider intervals)
- No variance adaptation
- Fast computation

**When to use:**
- You want guaranteed validity
- Data has high variance
- Computation speed is critical

**Atlas signature:**
- High coverage (often > 0.98)
- Lower power (wider intervals)
- Consistent performance across scenarios

### Empirical Bernstein CS

**Characteristics:**
- Variance-adaptive
- Tighter intervals when variance is low
- Early-time guard for small samples
- Slightly more computation

**When to use:**
- Data may have low variance
- You want tighter intervals
- Willing to trade some safety for precision

**Atlas signature:**
- Coverage closer to nominal (0.95-0.97)
- Higher power (narrower intervals)
- Better on low-variance scenarios

### Bernoulli Mixture CS

**Characteristics:**
- Optimized for 0/1 data
- Exact for Bernoulli distribution
- Tightest intervals for Bernoulli
- Only works for `kind="bernoulli"`

**When to use:**
- Conversion rates, click-through rates
- Binary outcomes
- You want the tightest valid intervals

**Atlas signature:**
- Best performance on Bernoulli scenarios
- Coverage near nominal (0.95-0.96)
- Highest power for Bernoulli data

## Scenario Types

### Null Scenarios (true_lift = 0)

**Purpose:** Test Type I error control

**What to check:**
- Type I error ≤ alpha
- Coverage ≥ 1 - alpha
- Method doesn't falsely detect effects

**Example:**
```
null_bernoulli_p05: true_mean = 0.5, true_lift = 0
```

### Alternative Scenarios (true_lift ≠ 0)

**Purpose:** Test power and detection ability

**What to check:**
- Power increases with effect size
- Coverage still ≥ 1 - alpha
- Stop time decreases with larger effects

**Example:**
```
alt_bernoulli_lift_05: true_mean = 0.5, true_lift = 0.05
```

### Distribution Variants

**Bernoulli:** Binary 0/1 data
- Test conversion rates, proportions

**Bounded:** Continuous in [0, 1]
- Test metrics like rates, percentages

**Beta:** Skewed distributions
- Test robustness to non-uniform data

## Interpreting Report Tables

### Coverage Comparison Table

```
| Scenario        | Hoeffding | EmpiricalBernstein | Bernoulli |
|-----------------|-----------|-------------------|-----------|
| bernoulli_p01   | **0.991** | **0.965**         | **0.951** |
| bernoulli_p05   | **0.982** | **0.951**         | **0.948** |
| beta_2_8        | **0.979** | **0.953**         | N/A       |
```

- **Bold** = meets nominal coverage (≥ 0.95)
- N/A = method not applicable (e.g., Bernoulli on continuous data)

### Type I Error Table

```
| Scenario        | Hoeffding | EmpiricalBernstein |
|-----------------|-----------|-------------------|
| null_bernoulli  | **0.031** | **0.043**         |
| null_bounded    | **0.029** | 0.067             |
```

- **Bold** = Type I error ≤ alpha (good)
- Regular = exceeds alpha (bad, method is anti-conservative)

### Power Table

```
| Scenario    | Hoeffding | EmpiricalBernstein |
|-------------|-----------|-------------------|
| lift_01     | 0.23      | 0.31              |
| lift_05     | 0.87      | 0.92              |
| lift_10     | 0.99      | 1.00              |
```

- Higher = better (detects true effects more often)
- Power increases with effect size
- Tighter methods (EB) have higher power

## Recommender Audit

The atlas includes a "Recommender Audit" section showing which method the auto-recommender would choose for each spec type:

```
| Spec Type  | Data Kind | Recommended Method    | Reason                          |
|------------|-----------|----------------------|----------------------------------|
| one_sample | bernoulli | BernoulliCS          | Exact for Bernoulli data        |
| one_sample | bounded   | EmpiricalBernsteinCS | Variance-adaptive, tight bounds |
| two_sample | bernoulli | TwoSampleHoeffdingCS | Valid union of one-sample CS    |
```

## Practical Usage

### Running a Custom Atlas

```python
from anytime.atlas.runner import AtlasRunner, Scenario
from anytime.spec import StreamSpec, ABSpec
from anytime.cs import HoeffdingCS, EmpiricalBernsteinCS
from anytime.twosample import TwoSampleHoeffdingCS

# Create scenarios
scenarios = [
    Scenario(
        name="custom_bernoulli",
        true_mean=0.5,
        distribution="bernoulli",
        support=(0.0, 1.0),
        n_max=500,
        seed=42,
        is_null=False,
    )
]

# Create spec
spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli")

# Run atlas
runner = AtlasRunner(n_sim=1000)
results = runner.run_one_sample_scenarios(
    scenarios, spec, [HoeffdingCS, EmpiricalBernsteinCS]
)

# Generate report
from anytime.atlas.report import generate_comparison_report
generate_comparison_report(results, "report.md", specs={"one_sample": spec})
```

### Checking Results

```python
# Access specific results
hoeffding_metrics = results["HoeffdingCS"]["custom_bernoulli"]
print(f"Coverage: {hoeffding_metrics.coverage:.3f}")
print(f"Type I Error: {hoeffding_metrics.type_i_error:.3f}")
print(f"Power: {hoeffding_metrics.power:.3f}")
print(f"Avg Width: {hoeffding_metrics.avg_width:.4f}")
```

## Common Questions

### Q: Why is coverage > 0.99? Isn't that too high?

A: High coverage means the method is **conservative**. It's still valid, just with wider intervals. This is common for Hoeffding which doesn't adapt to variance.

### Q: When should I prefer Empirical Bernstein over Hoeffding?

A: Use Empirical Bernstein when:
- You expect low variance in your data
- You want tighter intervals
- You're willing to accept slightly higher risk for better precision

Use Hoeffding when:
- You want guaranteed validity
- Variance is high or unknown
- Computation speed is critical

### Q: Why is power so low for small effects?

A: Small effects are hard to detect. You need:
- More data (larger n_max)
- Tighter intervals (use variance-adaptive methods)
- Larger effect size (practical significance threshold)

### Q: What does "N/A" mean in the tables?

A: The method isn't applicable for that scenario:
- Bernoulli methods only work for 0/1 data
- Some methods may not support one-sided intervals

### Q: How do I choose a stopping rule?

A:
- **Fixed horizon:** Predictable cost, good for planning
- **Exclude threshold:** Detect effects quickly
- **Periodic looks:** Balance between monitoring and cost

## Summary

- **Coverage ≥ 0.95**: Method is valid
- **Type I error ≤ alpha**: False positives controlled
- **Power**: Higher is better (detects true effects)
- **Width**: Lower is better (more precise)
- **Stop time**: Lower is faster (depends on rule)

Use atlas results to:
1. Verify methods are valid (coverage, Type I error)
2. Compare precision (width, power)
3. Choose the best method for your use case
4. Set appropriate sample sizes and stopping rules
