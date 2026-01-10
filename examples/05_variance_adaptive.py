#!/usr/bin/env python3
"""
05_variance_adaptive.py - Empirical Bernstein: Variance-Adaptive Intervals

INTERMEDIATE

This example compares Hoeffding (conservative) vs EmpiricalBernstein
(variance-adaptive) confidence sequences. EmpiricalBernstein uses online
variance estimates to produce narrower intervals when variance is low.

SCENARIO:
You're monitoring two different metrics:
1. Low variance metric: Temperature control (very stable around target)
2. High variance metric: Response times (lots of fluctuation)

EmpiricalBernstein will give you much tighter intervals for the low-variance
metric, while Hoeffding remains conservative regardless.

CONCEPTS:
- EmpiricalBernsteinCS: Variance-adaptive confidence sequences
- Online variance estimation using Welford's algorithm
- Comparison: Adaptive vs Conservative methods
- When to use each method
"""

from anytime import StreamSpec
from anytime.cs import HoeffdingCS, EmpiricalBernsteinCS
import random
import numpy as np

def generate_low_variance_stream(n=200, mean=0.5, std=0.02):
    """Generate data with very low variance (tight around mean)."""
    random.seed(42)
    np.random.seed(42)
    # Clip to [0, 1] to satisfy bounded assumption
    for _ in range(n):
        x = np.random.normal(mean, std)
        yield max(0.0, min(1.0, x))

def generate_high_variance_stream(n=200, mean=0.5, std=0.25):
    """Generate data with high variance (lots of spread)."""
    random.seed(43)
    np.random.seed(43)
    # Clip to [0, 1] to satisfy bounded assumption
    for _ in range(n):
        x = np.random.normal(mean, std)
        yield max(0.0, min(1.0, x))

def compare_methods(data_stream, name):
    """Run both methods on the same data and compare interval widths."""
    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)

    hoeffding_cs = HoeffdingCS(spec)
    eb_cs = EmpiricalBernsteinCS(spec)

    data = list(data_stream)

    # Track widths at different time points
    time_points = [10, 25, 50, 100, 200]
    results = {"hoeffding": {}, "eb": {}}

    for t, x in enumerate(data, start=1):
        hoeffding_cs.update(x)
        eb_cs.update(x)

        if t in time_points:
            h_iv = hoeffding_cs.interval()
            eb_iv = eb_cs.interval()

            results["hoeffding"][t] = {
                "width": h_iv.hi - h_iv.lo,
                "interval": (h_iv.lo, h_iv.hi)
            }
            results["eb"][t] = {
                "width": eb_iv.hi - eb_iv.lo,
                "interval": (eb_iv.lo, eb_iv.hi)
            }

    return results

def main():
    print("=" * 70)
    print("Variance-Adaptive Confidence Sequences")
    print("Hoeffding vs EmpiricalBernstein")
    print("=" * 70)

    # EXPERIMENT 1: Low variance data
    # --------------------------------
    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Low Variance Data (Temperature Control)")
    print("True mean: 0.50, Std: 0.02 (very stable)")
    print("=" * 70)

    results_low = compare_methods(
        generate_low_variance_stream(n=200, mean=0.5, std=0.02),
        "Low Variance"
    )

    print(f"\n{'t':>5} | {'Hoeffding Width':>17} | {'EB Width':>17} | {'Improvement':>13}")
    print("-" * 70)

    for t in sorted(results_low["hoeffding"].keys()):
        h_width = results_low["hoeffding"][t]["width"]
        eb_width = results_low["eb"][t]["width"]
        improvement = (1 - eb_width / h_width) * 100 if h_width > 0 else 0

        h_int = results_low["hoeffding"][t]["interval"]
        eb_int = results_low["eb"][t]["interval"]

        print(f"{t:5d} | {h_width:8.4f} {str(h_int):>20} | "
              f"{eb_width:8.4f} {str(eb_int):>20} | {improvement:+11.1f}%")

    # EXPERIMENT 2: High variance data
    # ---------------------------------
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: High Variance Data (Response Times)")
    print("True mean: 0.50, Std: 0.25 (lots of fluctuation)")
    print("=" * 70)

    results_high = compare_methods(
        generate_high_variance_stream(n=200, mean=0.5, std=0.25),
        "High Variance"
    )

    print(f"\n{'t':>5} | {'Hoeffding Width':>17} | {'EB Width':>17} | {'Improvement':>13}")
    print("-" * 70)

    for t in sorted(results_high["hoeffding"].keys()):
        h_width = results_high["hoeffding"][t]["width"]
        eb_width = results_high["eb"][t]["width"]
        improvement = (1 - eb_width / h_width) * 100 if h_width > 0 else 0

        print(f"{t:5d} | {h_width:8.4f} | {eb_width:8.4f} | {improvement:+11.1f}%")

    # SUMMARY AND RECOMMENDATIONS
    # ----------------------------
    print("\n" + "=" * 70)
    print("WHICH METHOD SHOULD YOU USE?")
    print("=" * 70)

    print("""
HoeffdingCS (Conservative):
  ✓ Use when: You want guaranteed coverage with minimal assumptions
  ✓ Use when: Variance is unknown or potentially high
  ✓ Use when: You need simple, fast computations
  ✗ Drawback: Always uses worst-case variance bound

EmpiricalBernsteinCS (Adaptive):
  ✓ Use when: You expect low variance and want tighter intervals
  ✓ Use when: Data is bounded and variance is observable
  ✓ Use when: You want faster detection (narrower intervals)
  ✗ Drawback: Requires enough data to estimate variance reliably

RULE OF THUMB:
  - Binary data (coin flips, conversions): Both work similarly
  - Stable metrics (temperature, error rates): Use EmpiricalBernstein
  - Highly variable metrics: Either works, Hoeffding is simpler
  - Early stopping: EmpiricalBernstein often stops sooner
    """)

    # Visual comparison at t=200
    print("=" * 70)
    print("FINAL COMPARISON AT t=200")
    print("=" * 70)

    h_final = results_low["hoeffding"][200]["width"]
    eb_final = results_low["eb"][200]["width"]

    print(f"\nLow variance data:")
    print(f"  Hoeffding:    {h_final:.4f}")
    print(f"  EmpiricalB:   {eb_final:.4f}")
    print(f"  Reduction:    {(1 - eb_final/h_final)*100:.1f}%")

    h_final_high = results_high["hoeffding"][200]["width"]
    eb_final_high = results_high["eb"][200]["width"]

    print(f"\nHigh variance data:")
    print(f"  Hoeffding:    {h_final_high:.4f}")
    print(f"  EmpiricalB:   {eb_final_high:.4f}")
    print(f"  Reduction:    {(1 - eb_final_high/h_final_high)*100:.1f}%")

if __name__ == "__main__":
    main()
