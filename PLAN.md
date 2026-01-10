# Development Plan

This plan turns the concept in `idea.md` into a shippable v1. It is written for a small team (2 to 5 engineers) but scales down to a solo build.

## Objectives

- Deliver a small Python library for anytime-valid inference on means and mean differences.
- Provide a CLI and an atlas benchmark that validates guarantees under peeking.
- Include a local demo that visualizes why optional stopping matters.
- Ship reproducible artifacts with configs, seeds, and manifests.

## Scope (v1)

In-scope:
- One-sample and two-sample mean inference
- Bounded or Bernoulli outcomes
- Confidence sequences and e-values
- Diagnostics (range checks, missingness, drift heuristics)
- Atlas benchmark and report
- CLI and demo app

Out-of-scope:
- Unbounded heavy-tail guarantees without user-provided bounds
- Change point detection or drift correction
- General regression or GLM inference
- Production streaming connectors (Kafka, Flink, etc.)

## Team roles (suggested)

- Tech lead: API design, integration, overall quality bar
- Math owner: method correctness, derivations, unit tests
- Infra owner: packaging, CI, artifacts, reproducibility
- Atlas owner: scenario design, simulations, report
- Demo and docs owner: CLI UX, demo app, README and guides

## Deliverables (v1)

1) Core library package (specs, CS, e-values, diagnostics, recommender)
2) CLI for data ingestion, simulation, and A/B analysis
3) Atlas benchmark and report generator
4) Interactive demo app
5) Documentation and release checklist

## Milestones and acceptance criteria

Phase 0 - Repo and foundations
Deliverables:
- Packaging scaffold and test runner
- Base types: StreamSpec, ABSpec, Interval, EValue, errors
Acceptance:
- `python -c "import anytime"` works
- `pytest` runs an empty or minimal suite

Phase 1 - Core estimators and one-sample CS
Deliverables:
- Online mean/variance estimators
- Hoeffding and Empirical Bernstein CS
Acceptance:
- Unit tests match batch mean/variance
- CS endpoints stay within bounds
- Alpha monotonicity tests pass

Phase 2 - Two-sample CS and e-values
Deliverables:
- Two-sample Hoeffding and Empirical Bernstein CS
- One-sample and two-sample e-values
Acceptance:
- Swap-arm symmetry tests pass
- Monte Carlo smoke tests for Type I error under peeking

Phase 3 - Diagnostics and recommender
Deliverables:
- Range, missingness, and drift checks
- Guarantee tiering and method recommendations
Acceptance:
- Out-of-range inputs error by default (or clip with disclosure)
- Drift scenario triggers warning and downgrades tier
- Recommender produces deterministic choices with reasons

Phase 4 - Atlas engine and report
Deliverables:
- Scenario definitions and deterministic runner
- Metrics aggregation and plotting utilities
- Report builder (HTML or Markdown)
Acceptance:
- "Smoke atlas" runs in a short time budget
- Report includes coverage, Type I error, power, runtime plots

Phase 5 - CLI, demo, docs, release
Deliverables:
- CLI commands for mean, abtest, and atlas
- Streamlit demo app with side-by-side naive baseline
- README, guides, cookbook, and release checklist
Acceptance:
- Demo launches locally and renders main views
- README quickstart commands work end to end

## Workstreams and dependencies

Core math:
- Depends on base specs and estimators
- Unblocks e-values and two-sample methods

Diagnostics and recommender:
- Depends on specs and data validation
- Feeds metadata to CLI and report

Atlas and reporting:
- Depends on methods and plotting
- Feeds QA and regression testing

CLI and demo:
- Depends on specs, methods, and diagnostics
- Uses plotting outputs for visuals

Docs and release:
- Depends on CLI and demo paths
- Reuses atlas outputs and screenshots

## Testing strategy

- Unit tests: estimators, validation, alpha monotonicity
- Property tests: interval widths nonnegative, no NaNs, symmetry
- Simulation tests: coverage and Type I error under peeking
- Regression tests: small atlas snapshot with fixed seeds
- Performance tests: update throughput regression guard

## Reproducibility and artifacts

Every run should write a manifest that includes:
- Config used (exact)
- Random seeds
- Package version and git hash (if available)
- Python and dependency versions

## Risks and mitigations

- Subtle math bugs: independent derivation notes plus Monte Carlo falsification
- Scope creep: v1 focuses on bounded or Bernoulli means only
- Misuse under drift: detect and downgrade tier with warnings
- Performance complaints: O(1) updates and honest benchmarks

## Definition of done (v1)

- Core library functions pass unit, property, and simulation tests
- Smoke atlas runs and report is generated
- Demo app launches and shows key comparisons
- README quickstart works locally
- Release checklist completed

