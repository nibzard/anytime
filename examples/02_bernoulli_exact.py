#!/usr/bin/env python3
"""
02_bernoulli_exact.py - Bernoulli Confidence Sequences for Binary Data

BEGINNER

This example demonstrates BernoulliCS, which provides time-uniform confidence
sequences for binary (0/1) data using a beta-binomial mixture. Unlike Hoeffding
which uses a conservative bound, BernoulliCS is tailored specifically for
Bernoulli data and provides tighter intervals.

SCENARIO:
You're testing a new coin for fairness. Is it a fair coin (p = 0.5)?
You flip it repeatedly and want to track your confidence about the true
probability of heads.

CONCEPTS:
- BernoulliCS: Bernoulli-specific confidence sequence for 0/1 data
- kind="bernoulli": Data must be exactly 0 or 1
- Tighter intervals: More precise than Hoeffding for binary data
"""

from anytime import StreamSpec
from anytime.cs import BernoulliCS

def simulate_coin_flips(true_p, n=500):
    """Simulate coin flips with true probability p."""
    import random
    random.seed(123)
    for _ in range(n):
        yield 1 if random.random() < true_p else 0

def main():
    print("=" * 60)
    print("Bernoulli Exact Confidence Sequences")
    print("Testing Coin Fairness")
    print("=" * 60)

    # STEP 1: Create spec for Bernoulli data
    # ---------------------------------------
    # For Bernoulli data, we MUST use kind="bernoulli"
    # The support must be (0.0, 1.0)
    spec = StreamSpec(
        alpha=0.05,           # 95% confidence
        support=(0.0, 1.0),   # Binary data in [0, 1]
        kind="bernoulli",      # EXACTLY for 0/1 data!
        two_sided=True,
        name="coin_p"
    )

    # STEP 2: Create Bernoulli confidence sequence
    # ---------------------------------------------------
    # Optional: Set Beta prior parameters (default: a=0.5, b=0.5)
    # These give a symmetric prior over p (no directional bias)
    cs = BernoulliCS(spec, a=0.5, b=0.5)

    print("\nTesting fairness of a coin (p = 0.5?)")
    print("True probability of heads: 0.52 (slightly unfair!)")
    print("Using Bernoulli-specific confidence sequences\n")

    # STEP 3: Compare intervals over time
    # ------------------------------------
    fair_coin = 0.5
    coin_flips = list(simulate_coin_flips(true_p=0.52, n=500))

    print(f"{'n':>5} | {'Heads':>6} | {'Rate':>6} | {'95% CI':>18} | {'Fair?':>6}")
    print("-" * 65)

    for n in [10, 25, 50, 100, 200, 500]:
        # Create fresh CS for this sample size
        cs = BernoulliCS(spec, a=0.5, b=0.5)

        # Add observations
        for flip in coin_flips[:n]:
            cs.update(flip)

        # Get interval
        iv = cs.interval()

        # Check if 0.5 is in the interval
        contains_fair = iv.lo <= fair_coin <= iv.hi
        status = "YES" if contains_fair else "NO"

        print(f"{n:5d} | {sum(coin_flips[:n]):6d} | {iv.estimate:6.3f} | "
              f"({iv.lo:.3f}, {iv.hi:.3f}) | {status:>6}")

    # STEP 4: Demonstrate early stopping detection
    # ---------------------------------------------
    print("\n" + "=" * 60)
    print("EARLY STOPPING DEMONSTRATION")
    print("=" * 60)
    print("\nFlipping until we're confident the coin is NOT fair (p ≠ 0.5)...")
    print("or until we reach 500 flips.\n")

    cs = BernoulliCS(spec, a=0.5, b=0.5)
    coin_flips = simulate_coin_flips(true_p=0.52, n=500)

    detected_unfair = None

    for t, flip in enumerate(coin_flips, start=1):
        cs.update(flip)

        # Check every 50 flips
        if t % 50 == 0:
            iv = cs.interval()
            contains_fair = iv.lo <= fair_coin <= iv.hi

            print(f"t={t:3d}: rate={iv.estimate:.3f}, CI=({iv.lo:.3f}, {iv.hi:.3f}) "
                  f"-> {'FAIR' if contains_fair else 'UNFAIR'}")

            if not contains_fair and detected_unfair is None:
                detected_unfair = t
                print(f"\n*** DETECTED UNFAIR COIN AT t={t} ***")
                break

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"True p: 0.52")
    print(f"Final estimate: {cs.interval().estimate:.3f}")
    print(f"Detected unfair: {'Yes (at t=' + str(detected_unfair) + ')' if detected_unfair else 'No'}")
    print(f"\nNOTE: With Bernoulli-specific CS, we get tighter intervals than")
    print(f"Hoeffding, making it easier to detect small deviations from 0.5.")

if __name__ == "__main__":
    main()
