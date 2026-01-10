# Sample Datasets for Anytime Examples

This directory contains sample datasets used by the examples.

## Files

| File | Description | Used By |
|------|-------------|---------|
| `conversions.csv` | A/B test conversion data (variants A and B) | Example 10 |
| `ab_test_results.csv` | Larger A/B test dataset (1000 users) | General use |
| `coin_flips.csv` | Coin flip sequences (500 flips) | Example 2 |
| `metrics_stream.csv` | Time-series metrics with degradation | Example 4 |

## Format

All CSV files use standard formatting with headers:
- `conversions.csv`: `timestamp,user_id,converted,variant`
- `ab_test_results.csv`: `user_id,variant,converted,timestamp`
- `coin_flips.csv`: `flip_number,result`
- `metrics_stream.csv`: `timestamp,metric_name,value`

## Generating New Data

The examples include built-in data generation using Python's `random` module.
You can also modify the seed values to create different random variations.

## Data Characteristics

- **Conversion data**: Binary (0/1), representing success/failure
- **Coin flips**: 'H' (heads) or 'T' (tails)
- **Metrics**: Continuous values in [0, 1], often with trends or drift
