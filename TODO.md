# TODO

Atomic tasks for the v1 build. Each item should be independently completable and reviewable.

## Repo and tooling

- [x] Add `pyproject.toml` with build metadata and minimal runtime deps
- [x] Add `pytest` config (pytest.ini or pyproject section)
- [x] Add `anytime/__init__.py` with version placeholder and public exports
- [x] Add `tests/` scaffold with a placeholder test

## Core API and types

- [x] Define `GuaranteeTier` enum in `anytime/types.py`
- [x] Define `StreamSpec` dataclass with validation in `anytime/spec.py`
- [x] Define `ABSpec` dataclass with validation in `anytime/spec.py`
- [x] Define `Interval` dataclass in `anytime/types.py`
- [x] Define `EValue` dataclass in `anytime/types.py`
- [x] Add `AssumptionViolationError` in `anytime/errors.py`
- [x] Add `ConfigError` in `anytime/errors.py`
- [x] Add unit tests for spec validation (alpha, support, kind)
- [x] Fix `anytime/__init__.py` exports (import `GuaranteeTier` from `anytime/types.py`)
- [x] Enforce `spec.kind` compatibility in method constructors (error for unsupported kinds)
- [x] Implement one-sided two-sample CS support (or document two-sided-only)

## Online estimators

- [x] Implement online mean estimator in `anytime/core/estimators.py`
- [x] Implement online variance estimator in `anytime/core/estimators.py`
- [x] Add unit tests comparing online vs batch mean and variance
- [x] Add stability test for variance at small t

## One-sample confidence sequences

- [x] Add Hoeffding CS class skeleton in `anytime/cs/hoeffding.py`
- [x] Implement Hoeffding CS interval formula
- [x] Add Hoeffding CS tests for bounds and alpha monotonicity
- [x] Add Empirical Bernstein CS class skeleton in `anytime/cs/empirical_bernstein.py`
- [x] Implement Empirical Bernstein CS interval formula with early-time guard
- [x] Add Empirical Bernstein CS tests for no NaNs and narrower widths in low variance
- [x] Add Bernoulli CS class skeleton in `anytime/cs/bernoulli_exact.py`
- [x] Replace Clopper-Pearson placeholder with a time-uniform Bernoulli CS (mixture/betting)
- [x] Add Bernoulli CS optional-stopping coverage test
- [x] Respect `spec.two_sided` for Bernoulli CS (or document two-sided-only behavior)
- [x] Add citations/derivation notes for Hoeffding/EB constants to prevent silent math drift

## Two-sample confidence sequences

- [x] Implement valid two-sample Hoeffding CS (union of one-sample CS with alpha split)
- [x] Implement valid two-sample Empirical Bernstein CS (union of one-sample CS with alpha split)
- [x] Add symmetry tests for swapping A and B
- [x] Add null simulation smoke test for optional stopping and anytime coverage
- [x] Propagate diagnostics tier when one arm is empty (avoid default guaranteed tier)

## E-values

- [x] Replace one-sample Bernoulli e-value with a valid e-process (mixture or betting martingale)
- [x] Add optional-stopping tests for e-values (decision rate under null)
- [x] Add null simulation smoke test for one-sample e-values
- [x] Replace two-sample mean-difference e-value with a valid bounded e-process
- [x] Add null and power smoke tests for two-sample e-values
- [x] Prevent e-value overflow via log-space computation or clamped exponentials

## Diagnostics and tiering

- [x] Implement range checker with strict and clip modes
- [x] Implement missingness tracker and summary stats
- [x] Implement drift heuristic (rolling mean change or CUSUM-lite)
- [x] Wire diagnostics into CS/EValue update paths (range/missingness/drift)
- [x] Use `AssumptionViolationError` for hard failures and propagate `GuaranteeTier`
- [x] Attach diagnostics metadata to `Interval` and `EValue` outputs
- [x] Add tests for out-of-range error and clip disclosure
- [x] Add tests that drift detection flips tier to `DIAGNOSTIC`
- [x] Reset diagnostics state on `reset()` and snapshot diagnostics in outputs (avoid mutation)

## Recommender

- [x] Define `Recommendation` dataclass in `anytime/recommend.py`
- [x] Implement `recommend_cs` for StreamSpec
- [x] Implement `recommend_ab` for ABSpec
- [x] Add deterministic recommender tests
- [x] Update recommender to avoid invalid Bernoulli/subgaussian defaults until methods are fixed

## Configs, logging, and reproducibility

- [x] Add YAML config loader
- [x] Add config schema validation (required fields, type checks)
- [x] Implement run directory creation (timestamp + slug)
- [x] Write manifest.json with config, seed, package + dependency versions, git hash
- [x] Add JSONL logger for metrics and diagnostics
- [x] Add tests for manifest content

## Plotting

- [x] Add interval band plotting helper
- [x] Add e-value time series plotting helper
- [x] Add stopping time histogram helper
- [x] Add headless plotting test using Agg backend

## CLI and IO

- [x] Implement CSV reader with schema validation
- [x] Implement `anytime.cli mean` command
- [x] Implement `anytime.cli abtest` command
- [x] Implement `anytime.atlas` command
- [x] Add CLI smoke tests on tiny CSV fixtures
- [x] Emit diagnostics and tier info in CLI outputs
- [x] Handle missing/invalid numeric values and missing columns with clear errors or skip-with-diagnostics

## Atlas

- [x] Implement one-sample scenario generator (16 scenarios from idea.md)
- [x] Implement two-sample scenario generator
- [x] Implement stopping rules (fixed horizon, exclude-threshold, periodic looks)
- [x] Upgrade runner to compute anytime coverage, Type I error under stopping, power, width, runtime
- [x] Add e-value decision tracking and naive-peeking baseline
- [x] Add smoke atlas config and expected output checks
- [x] Validate Bernoulli A/B scenarios (p_a/p_b bounds) and fail fast on invalid parameters

## Report

- [x] Create report template (Markdown or HTML)
- [x] Implement method comparison tables with coverage/Type I/power
- [x] Include final coverage in report tables
- [x] Implement plot embedding and captions
- [x] Add recommender audit table
- [x] Add report build smoke test

## Demo

- [x] Create Streamlit app skeleton in `demos/app.py`
- [x] Implement live Bernoulli A/B simulation using two-sample CS (not delta-method)
- [x] Add naive p-value baseline visualization
- [x] Add controls for alpha, effect size, and stopping rule
- [x] Add `python -m anytime.demo` launcher

## Tests and QA

- [x] Add Hypothesis property tests for interval invariants
- [x] Add regression test for a small atlas snapshot
- [x] Add performance micro-benchmark for update throughput
- [x] Add release checklist in docs
- [x] Add tests for e-value overflow handling and diagnostics reset/snapshot behavior

## Docs

- [x] Expand README quickstart with CLI examples
- [x] Write "Assumptions and tiers" guide
- [x] Write "Stopping rules and optional stopping" guide
- [x] Write "Atlas interpretation" guide
- [x] Add cookbook examples (bounded KPI, A/B conversion)
- [x] Add contributor guide with local dev steps
