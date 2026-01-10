#!/usr/bin/env python3
"""
03_ab_test_simple.py - Simple A/B Test with E-Values

BEGINNER

This example introduces e-values for A/B testing with optional stopping.
E-values are the anytime-valid alternative to p-values. You can check them
continuously and stop as soon as you have evidence.

SCENARIO:
You're running an A/B test on a website:
- Control (A): Current design, conversion rate ~50%
- Treatment (B): New design, hopefully better!

Users are randomly assigned to A or B. You want to know if B is better
than A, and you want to stop the test as soon as you're confident.

CONCEPTS:
- ABSpec: Specification for A/B tests
- TwoSampleMeanMixtureE: E-value for mean difference (B vs A)
- side="ge": Testing if B > A (greater than or equal)
- e-value decision: When e-value > 1/alpha, we can reject H0
"""

import sys
sys.path.insert(0, '..')

from anytime import ABSpec
from anytime.evalues import TwoSampleMeanMixtureE
import random

def generate_ab_stream(rate_a, rate_b, n_per_arm=500):
    """
    Generate A/B test data.

    Yields: ("A", 0/1) or ("B", 0/1)
    """
    random.seed(42)
    for _ in range(n_per_arm):
        # Arm A
        yield ("A", 1 if random.random() < rate_a else 0)
        # Arm B
        yield ("B", 1 if random.random() < rate_b else 0)

def main():
    print("=" * 60)
    print("A/B Testing with E-Values")
    print("=" * 60)

    # STEP 1: Define A/B test specification
    # --------------------------------------
    # Testing if conversion rate of B > A
    # H0: mean(B) - mean(A) = 0
    # H1: mean(B) - mean(A) > 0 (B is better)
    spec = ABSpec(
        alpha=0.05,           # 95% confidence
        support=(0.0, 1.0),   # Conversion in [0, 1]
        kind="bounded",
        two_sided=False,      # One-sided: B > A
        name="ab_lift"
    )

    # STEP 2: Create e-value process
    # -------------------------------
    # delta0 = 0.0: Null hypothesis is no difference
    # side = "ge": Testing if B - A > 0 (B greater than or equal to A)
    etest = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")

    print("\nTesting: New design (B) vs Current design (A)")
    print("H0: Conversion rate of B = A")
    print("H1: Conversion rate of B > A")
    print("\nTrue rates: A = 50%, B = 55% (B is actually better!)")
    print("\nMonitoring e-value. When e-value > 20 (1/alpha), we reject H0.\n")

    # STEP 3: Run the A/B test
    # -------------------------
    ab_stream = generate_ab_stream(rate_a=0.50, rate_b=0.55, n_per_arm=500)

    # Track evidence over time
    print(f"{'Time':>5} | {'Rate A':>7} | {'Rate B':>7} | {'Lift':>6} | {'E-value':>9} | {'Decision':>10}")
    print("-" * 70)

    rejected_at = None
    counts_a = 0
    counts_b = 0
    sum_a = 0
    sum_b = 0

    for arm, conversion in ab_stream:
        # Update e-value with new observation
        etest.update((arm, conversion))

        # Track running stats
        if arm == "A":
            counts_a += 1
            sum_a += conversion
        else:
            counts_b += 1
            sum_b += conversion

        total_obs = counts_a + counts_b

        # Check progress every 50 observations
        if total_obs % 50 == 0:
            ev = etest.evalue()
            rate_a = sum_a / counts_a if counts_a > 0 else 0
            rate_b = sum_b / counts_b if counts_b > 0 else 0
            lift = rate_b - rate_a

            # Decision: e-value > 1/alpha = 20
            decision = "REJECT H0" if ev.decision else "continue"

            print(f"{total_obs:5d} | {rate_a:7.3f} | {rate_b:7.3f} | {lift:6.3f} | "
                  f"{ev.e:9.2f} | {decision:>10}")

            if ev.decision and rejected_at is None:
                rejected_at = total_obs

        # Stop if we've made a decision
        if rejected_at is not None and total_obs >= rejected_at + 20:
            break

    # STEP 4: Final results
    # ----------------------
    ev = etest.evalue()
    rate_a = sum_a / counts_a
    rate_b = sum_b / counts_b
    lift = rate_b - rate_a

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Control (A) rate:     {rate_a:.3f}")
    print(f"Treatment (B) rate:   {rate_b:.3f}")
    print(f"Lift (B - A):         {lift:+.3f}")
    print(f"Final e-value:        {ev.e:.2f}")
    print(f"Total observations:   {counts_a + counts_b}")
    print(f"Decision made at:     t={rejected_at if rejected_at else 'N/A'}")
    print(f"Final decision:       {'REJECT H0' if ev.decision else 'Cannot reject'}")
    print(f"\nInterpretation: {'B is significantly better than A!' if ev.decision else 'Not enough evidence'}")

    print("\n" + "=" * 60)
    print("KEY INSIGHT")
    print("=" * 60)
    print(f"E-values let you peek continuously and stop as soon as")
    print(f"you have evidence. The decision at t={rejected_at} is")
    print(f"statistically valid - no p-value inflation!")

if __name__ == "__main__":
    main()
