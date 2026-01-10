# Anytime Examples

This directory contains runnable examples demonstrating the `anytime` library for peeking-safe streaming inference.

## Beginner Examples

| File | Description |
|------|-------------|
| `01_hello_anytime.py` | Your first confidence sequence - monitoring conversion rates |
| `02_bernoulli_exact.py` | Exact confidence sequences for binary data (coin flips) |
| `03_ab_test_simple.py` | Simple A/B test with e-values (when to stop your experiment) |
| `04_streaming_monitor.py` | Real-time monitoring dashboard with live confidence intervals |

## Intermediate Examples

| File | Description |
|------|-------------|
| `05_variance_adaptive.py` | Empirical Bernstein: narrower intervals when variance is low |
| `06_two_sample_cs.py` | Confidence intervals for the difference between two groups |
| `07_early_stopping.py` | Optimal stopping rules for A/B tests with e-values |

## Advanced Examples

| File | Description |
|------|-------------|
| `08_multiple_comparisons.py` | Testing multiple variants with proper error control |
| `09_diagnostic_checks.py` | Using assumption diagnostics for production systems |
| `10_custom_datasets.py` | Working with real datasets (CSV, API, streaming) |

## Running Examples

Each example is self-contained. Run with:

```bash
cd examples
python 01_hello_anytime.py
```

## Datasets

The `datasets/` folder contains sample data used by examples:

- `conversions.csv` - Synthetic conversion rate data
- `ab_test_results.csv` - A/B test simulation results
- `coin_flips.csv` - Coin flip sequences
- `metrics_stream.csv` - Time-series metrics data

## Difficulty Guide

- **Beginner**: New to anytime inference? Start here. Basic concepts, minimal code.
- **Intermediate**: Comfortable with the basics? Explore variance-adaptive methods and two-sample tests.
- **Advanced**: Production use cases. Diagnostics, multiple comparisons, real data pipelines.
