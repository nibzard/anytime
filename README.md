# Anytime

Peeking-safe streaming inference for A/B tests and online metrics.

Status: pre-alpha. This repo is for bounded/Bernoulli means and mean differences only.

---

## Interactive Demo (start here!)

**Try the interactive demo first - it's the fastest way to understand the peeking problem:**

```bash
pip install -e ".[demo]"
streamlit run demos/app.py
```

### The peeking problem (in plain English)

Flip a coin 10 times: you get 7 heads. "Hmm, that's a bit high."

Flip it 20 more times: now you have 12 heads out of 30. "Okay, seems fair."

But what if you had stopped after 10 flips? You might have convinced yourself the coin was rigged.

**This is the peeking problem:** If you can choose WHEN to stop looking, you can almost always find a "significant" result even when nothing special is happening.

#### Real-world consequences

🏢 **Business:** You launch a new website feature and check results daily. After 3 days it looks like a winner, so you stop the test. But was it actually better - or did you just get lucky with timing?

📊 **A/B tests:** Same problem. Traditional statistics break when you peek. You declare winners too early, ship features that don't actually help, and wonder why improvements never materialize.

🏀 **Sports:** A player has a "hot streak" of 5 great games. Is it real skill improvement or just normal variation? If you stop analyzing at the right moment, you can tell any story you want.

#### The solution

Anytime gives you confidence sequences that stay valid even when you check continuously. Stop when you want - the guarantees hold.

**The demo shows you:**
- Why checking your A/B test daily leads to false wins
- How traditional p-values break when you peek
- Why "hot streaks" are often just luck
- How anytime-valid methods maintain their guarantees

---

## Examples (progressive learning)

After trying the demo, dive into runnable scripts that build intuition:

```bash
python examples/01_hello_anytime.py
```

Suggested order:

1) `examples/01_hello_anytime.py` - Hello world
2) `examples/02_bernoulli_exact.py` - Bernoulli exact CS
3) `examples/03_ab_test_simple.py` - Simple A/B test
4) `examples/04_streaming_monitor.py` - Streaming monitor
5) `examples/05_variance_adaptive.py` - Variance adaptive
6) `examples/06_two_sample_cs.py` - Two-sample CS
7) `examples/07_early_stopping.py` - Early stopping
8) `examples/08_multiple_comparisons.py` - Multiple comparisons
9) `examples/09_diagnostic_checks.py` - Diagnostic checks
10) `examples/10_custom_datasets.py` - Custom datasets

11-27) Real-world examples: retail, sports, crypto, weather, gaming, surveys, learning, habits, and more!

See `examples/README.md` for descriptions and datasets.

---

## CLI (low friction)

The CLI reads CSVs and prints progress plus diagnostics.

**One-sample:**
```bash
anytime mean --config tests/fixtures/mean_config.yaml
```

**Two-sample A/B:**
```bash
anytime abtest --config tests/fixtures/ab_config.yaml
```

**Atlas smoke run:**
```bash
anytime atlas --config configs/atlas_smoke.yaml --output runs
```

### CLI config format (minimal)

```yaml
alpha: 0.05
support: [0.0, 1.0]
kind: bounded
two_sided: true
method: empirical_bernstein
input: path/to/data.csv
column: value
```

Two-sample uses `arm_column` and `value_column` instead of `column`.

### Atlas config format (high level)

See `configs/atlas_smoke.yaml` for a complete example.

Key fields:
- `n_sim`: Monte Carlo repetitions.
- `one_sample` / `two_sample`: each has `spec`, `methods`, `scenarios`.
- `stopping_rule`: `fixed`, `exclude_threshold`, or `periodic`.

The atlas generates `report_one_sample.md` and `report_two_sample.md` plus a `manifest.json` when `--output` is provided.

---

## Quickstart (for developers)

Install for local development:

```bash
pip install -e ".[dev,plot,demo]"
```

**One-sample confidence sequence for a bounded KPI:**

```python
from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS

spec = StreamSpec(
    alpha=0.05,
    support=(0.0, 1.0),
    kind="bounded",
    two_sided=True,
    name="kpi",
)
cs = EmpiricalBernsteinCS(spec)

for x in stream_values():  # values in [0,1]
    cs.update(x)
    iv = cs.interval()
    if iv.t % 100 == 0:
        print(iv.t, iv.estimate, (iv.lo, iv.hi), iv.tier.value)
```

**Two-sample A/B confidence sequence:**

```python
from anytime import ABSpec
from anytime.twosample import TwoSampleEmpiricalBernsteinCS

spec = ABSpec(
    alpha=0.05,
    support=(0.0, 1.0),
    kind="bounded",
    two_sided=True,  # two-sided only for two-sample CS
    name="lift",
)
cs = TwoSampleEmpiricalBernsteinCS(spec)

for arm, x in ab_stream():  # arm in {"A","B"}
    cs.update((arm, x))
    iv = cs.interval()
    if iv.t % 100 == 0:
        print(iv.t, iv.estimate, (iv.lo, iv.hi), iv.tier.value)
```

**E-value example (Bernoulli one-sample):**

```python
from anytime import StreamSpec
from anytime.evalues import BernoulliMixtureE

spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli", two_sided=True)
etest = BernoulliMixtureE(spec, p0=0.5, side="ge")

for x in stream_values():
    etest.update(x)
    ev = etest.evalue()
    if ev.decision:
        print("Reject H0 at t=", ev.t, "e=", ev.e)
        break
```

---

## What you get

- Confidence sequences for streaming means and A/B mean differences.
- E-values for optional-stopping-safe decisions.
- Diagnostics and tiers to surface assumption violations.
- An atlas runner that checks anytime coverage and Type I error.

---

## Core ideas (intuitive)

- **Confidence sequence (CS):** a confidence interval that is valid at every time. You can stop whenever you want, and the interval still has the stated coverage.
- **E-value:** a measure of evidence you can keep updating. Reject when e >= 1/alpha.

Both are designed for streaming data with optional stopping.

---

## Why this exists

If you repeatedly peek at experiment results and stop early, classical p-values are no longer valid. Anytime gives you confidence sequences and e-values that remain valid under optional stopping, so you can monitor continuously without silently inflating false positives.

---

## Assumptions and guarantee tiers

Anytime only guarantees validity when assumptions hold. Every interval/e-value includes a tier:

- **guaranteed:** assumptions satisfied
- **clipped:** out-of-range values clipped to declared bounds
- **diagnostic:** assumptions violated or drift detected

Behavior:
- Out-of-range values: error by default, or clip if `clip_mode="clip"`.
- Missing/NaN values: flagged and tier downgraded.
- Drift detection: heuristic; if triggered, tier becomes diagnostic.

---

## Methods included

**One-sample CS:**
- Hoeffding (time-uniform, bounded)
- Empirical Bernstein (time-uniform, bounded)
- Bernoulli mixture CS (time-uniform, 0/1 only)

**Two-sample CS:**
- Union of one-sample CS with alpha split (two-sided only)

**E-values:**
- Bernoulli beta-binomial mixture (one-sample)
- Two-sample bounded mean via paired differences and mixture e-process

---

## Reproducibility

Atlas and CLI runs can write a `manifest.json` that captures config, seed, and environment metadata. Use `--output` to create a run directory.

---

## Testing

```bash
pytest -q
```

---

## Non-goals (v1)

- Unbounded heavy-tailed guarantees without user-provided bounds
- Change point detection or drift correction
- General regression/GLM inference

---

## Limitations and roadmap

- Subgaussian methods are not implemented (bounded/Bernoulli only).
- Atlas scenarios are still a small smoke set; larger suites are planned.
