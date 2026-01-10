#!/usr/bin/env python3
"""
06_two_sample_cs.py - Confidence Intervals for Mean Differences

INTERMEDIATE

This example demonstrates two-sample confidence sequences, which give you
confidence intervals for the DIFFERENCE between two groups. Unlike e-values
which only tell you "there's a difference," confidence intervals tell you
HOW BIG the difference is.

SCENARIO:
You're comparing two versions of an algorithm:
- Version A: Baseline (mean = 0.50)
- Version B: Improved version (mean = 0.55)

You want to know not just IF B is better, but also WHAT THE LIFT is.
Confidence intervals for the mean difference give you both.

CONCEPTS:
- TwoSampleHoeffdingCS: Two-sample confidence sequence (conservative)
- TwoSampleEmpiricalBernsteinCS: Two-sample with variance adaptation
- Interpreting mean difference: If CI excludes 0, difference is significant
- Lift estimation: Point estimate and uncertainty for B - A
"""

from anytime import ABSpec
from anytime.twosample import TwoSampleHoeffdingCS, TwoSampleEmpiricalBernsteinCS
import random
import numpy as np

def generate_ab_comparison_data(mean_a=0.50, mean_b=0.55, std=0.20, n_per_arm=300):
    """
    Generate paired observations for A/B comparison.

    Yields alternating ("A", value) and ("B", value) pairs.
    """
    random.seed(456)
    np.random.seed(456)

    for _ in range(n_per_arm):
        # Arm A
        val_a = np.random.normal(mean_a, std)
        yield ("A", max(0.0, min(1.0, val_a)))

        # Arm B
        val_b = np.random.normal(mean_b, std)
        yield ("B", max(0.0, min(1.0, val_b)))

def run_two_sample_cs(spec, ab_data, method_name="Method"):
    """Run a two-sample confidence sequence on A/B data."""
    if "Hoeffding" in method_name:
        cs = TwoSampleHoeffdingCS(spec)
    else:
        cs = TwoSampleEmpiricalBernsteinCS(spec)

    data = list(ab_data)
    results = []

    # Track at different time points
    time_points = [20, 50, 100, 200, 400, 600]

    for t, (arm, value) in enumerate(data, start=1):
        cs.update((arm, value))

        if t in time_points:
            iv = cs.interval()
            results.append({
                't': t,
                'estimate': iv.estimate,  # This is mean(B) - mean(A)
                'lo': iv.lo,
                'hi': iv.hi,
                'width': iv.hi - iv.lo,
                'significant': iv.lo > 0 or iv.hi < 0  # CI excludes 0
            })

    return results

def main():
    print("=" * 70)
    print("Two-Sample Confidence Sequences")
    print("Estimating Mean Difference (B - A)")
    print("=" * 70)

    # STEP 1: Define A/B specification
    # ---------------------------------
    spec = ABSpec(
        alpha=0.05,           # 95% confidence
        support=(0.0, 1.0),   # Data in [0, 1]
        kind="bounded",
        two_sided=True,       # Two-sided: B could be better or worse
        name="mean_difference"
    )

    print("\nScenario: Comparing two algorithm versions")
    print("Version A (baseline):     mean = 0.50")
    print("Version B (improved):     mean = 0.55")
    print("True difference (B - A):  +0.05")
    print("Goal: Estimate the lift with confidence intervals\n")

    # STEP 2: Generate comparison data
    # ---------------------------------
    ab_data = list(generate_ab_comparison_data(
        mean_a=0.50, mean_b=0.55, std=0.20, n_per_arm=300
    ))

    # STEP 3: Run both two-sample methods
    # ------------------------------------
    print("=" * 70)
    print("COMPARISON: Two-Sample Hoeffding vs EmpiricalBernstein")
    print("=" * 70)

    results_hoeffding = run_two_sample_cs(spec, ab_data, "Hoeffding")
    results_eb = run_two_sample_cs(spec, ab_data, "EmpiricalBernstein")

    print(f"\n{'t':>5} | {'Estimate':>10} | {'95% CI':>22} | {'Width':>7} | {'Sig?':>5}")
    print("-" * 70)

    for i, (h, eb) in enumerate(zip(results_hoeffding, results_eb)):
        print(f"\nHoeffding at t={h['t']}:")
        print(f"  Estimate: {h['estimate']:7.3f}  CI: ({h['lo']:.3f}, {h['hi']:.3f})  "
              f"Width: {h['width']:.3f}  Sig: {'YES' if h['significant'] else 'NO'}")

        print(f"EB at t={eb['t']}:")
        print(f"  Estimate: {eb['estimate']:7.3f}  CI: ({eb['lo']:.3f}, {eb['hi']:.3f})  "
              f"Width: {eb['width']:.3f}  Sig: {'YES' if eb['significant'] else 'NO'}")

        improvement = (1 - eb['width'] / h['width']) * 100 if h['width'] > 0 else 0
        print(f"  Width reduction: {improvement:.1f}%")

    # STEP 4: Interpretation guide
    # -----------------------------
    print("\n" + "=" * 70)
    print("HOW TO INTERPRET TWO-SAMPLE CONFIDENCE INTERVALS")
    print("=" * 70)

    print("""
The interval represents: mean(B) - mean(A)

Case 1: Entirely positive (e.g., CI = [0.02, 0.08])
  → B is significantly better than A
  → Lift is between 2% and 8%

Case 2: Entirely negative (e.g., CI = [-0.08, -0.02])
  → B is significantly worse than A
  → Loss is between 2% and 8%

Case 3: Contains zero (e.g., CI = [-0.02, 0.06])
  → Not enough evidence to conclude B differs from A
  → Difference could be anywhere from -2% to +6%

Case 4: Contains zero but very narrow (e.g., CI = [-0.005, 0.005])
  → B and A are practically equivalent
    """)

    # STEP 5: Practical example
    # --------------------------
    print("=" * 70)
    print("PRACTICAL EXAMPLE: When to stop your A/B test")
    print("=" * 70)

    print("\nDecision rule: Stop when lower bound of CI > minimum_lift_threshold")
    print("Let's say minimum_lift_threshold = 0.02 (2% lift)\n")

    spec_one_sided = ABSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True,  # Two-sided CS; still valid for one-sided stopping rules
        name="lift_stopping_rule"
    )

    cs = TwoSampleHoeffdingCS(spec_one_sided)

    min_lift = 0.02
    stopped_at = None

    for t, (arm, value) in enumerate(ab_data, start=1):
        cs.update((arm, value))

        if t % 50 == 0:
            iv = cs.interval()
            confident_above_min = iv.lo > min_lift

            print(f"t={t:3d}: lift = {iv.estimate:+.3f}, 95% CI = ({iv.lo:+.3f}, {iv.hi:+.3f}) "
                  f"→ {'STOP!' if confident_above_min else 'continue'}")

            if confident_above_min and stopped_at is None:
                stopped_at = t

    print(f"\n✓ Could have stopped at t={stopped_at} with confidence that lift > 2%")

if __name__ == "__main__":
    main()
