# Anytime

Peeking-safe streaming inference for A/B tests and online metrics.

Status: pre-alpha. This repo is for bounded/Bernoulli means and mean differences only.

## Why this exists

If you repeatedly peek at experiment results and stop early, classical p-values
are no longer valid. Anytime gives you confidence sequences and e-values that
remain valid under optional stopping, so you can monitor continuously without
silently inflating false positives.

## What you get (short version)

- Confidence sequences for streaming means and A/B mean differences.
- E-values for optional-stopping-safe decisions.
- Diagnostics and tiers to surface assumption violations.
- An atlas runner that checks anytime coverage and Type I error.
- A small demo that contrasts anytime-valid methods with naive peeking.

If you just want to try it quickly, jump to Quickstart.

## Core ideas (intuitive)

- Confidence sequence (CS): a confidence interval that is valid at every time.
  You can stop whenever you want, and the interval still has the stated coverage.
- E-value: a measure of evidence you can keep updating. Reject when e >= 1/alpha.

Both are designed for streaming data with optional stopping.

## Quickstart

Install for local development:

```bash
pip install -e ".[dev,plot,demo]"
```

One-sample confidence sequence for a bounded KPI:

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

Two-sample A/B confidence sequence:

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

E-value example (Bernoulli one-sample):

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

## CLI (low friction)

The CLI reads CSVs and prints progress plus diagnostics.

One-sample:

```bash
anytime mean --config tests/fixtures/mean_config.yaml
```

Two-sample A/B:

```bash
anytime abtest --config tests/fixtures/ab_config.yaml
```

Atlas smoke run:

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

The atlas generates `report_one_sample.md` and `report_two_sample.md` plus a
`manifest.json` when `--output` is provided.

## Demo (optional but useful)

Run the demo app:

```bash
streamlit run demos/app.py
```

It shows a peeking-safe CS alongside a naive p-value baseline.

## Assumptions and guarantee tiers

Anytime only guarantees validity when assumptions hold. Every interval/e-value
includes a tier:

- guaranteed: assumptions satisfied
- clipped: out-of-range values clipped to declared bounds
- diagnostic: assumptions violated or drift detected

Behavior:
- Out-of-range values: error by default, or clip if `clip_mode="clip"`.
- Missing/NaN values: flagged and tier downgraded.
- Drift detection: heuristic; if triggered, tier becomes diagnostic.

## Methods included

One-sample CS:
- Hoeffding (time-uniform, bounded)
- Empirical Bernstein (time-uniform, bounded)
- Bernoulli mixture CS (time-uniform, 0/1 only)

Two-sample CS:
- Union of one-sample CS with alpha split (two-sided only)

E-values:
- Bernoulli beta-binomial mixture (one-sample)
- Two-sample bounded mean via paired differences and mixture e-process

## Reproducibility

Atlas and CLI runs can write a `manifest.json` that captures config, seed, and
environment metadata. Use `--output` to create a run directory.

## Testing

```bash
pytest -q
```

## Non-goals (v1)

- Unbounded heavy-tailed guarantees without user-provided bounds
- Change point detection or drift correction
- General regression/GLM inference

## Limitations and roadmap

- Two-sample CS is two-sided only (one-sided support not implemented yet).
- Subgaussian methods are not implemented (bounded/Bernoulli only).
- Atlas scenarios are still a small smoke set; larger suites are planned.
