#!/usr/bin/env python3
"""
01_hello_anytime.py - Your First Confidence Sequence

BEGINNER

This example introduces the core concept of anytime-valid confidence sequences.
Unlike traditional confidence intervals that assume a fixed sample size,
confidence sequences remain valid even if you check them continuously
and stop your experiment early when you see a significant result.

SCENARIO:
You're monitoring a website's conversion rate. Users visit one by one,
and you want to know if the conversion rate meets your target of 50%.
You can check the results after each user and stop as soon as you're confident.

CONCEPTS:
- StreamSpec: Define your analysis parameters (alpha, support, data type)
- HoeffdingCS: Conservative confidence sequence for bounded data
- update(): Add new observations sequentially
- interval(): Get current confidence interval
"""

import sys
sys.path.insert(0, '..')

from anytime import StreamSpec
from anytime.cs import HoeffdingCS

def generate_conversion_stream(true_rate, n=1000):
    """Generate a stream of conversion events (0 or 1)."""
    import random
    random.seed(42)
    for _ in range(n):
        yield 1 if random.random() < true_rate else 0

def main():
    print("=" * 60)
    print("Hello Anytime: Monitoring Conversion Rates")
    print("=" * 60)

    # STEP 1: Define your analysis specification
    # ------------------------------------------
    # alpha = 0.05 means we want 95% confidence (1 - alpha)
    # support = (0.0, 1.0) because conversions are binary (0 or 1)
    # kind = "bounded" for data with known bounds
    # two_sided = True for a two-sided interval (lower and upper bounds)
    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True,
        name="conversion_rate"
    )

    # STEP 2: Create the confidence sequence
    # --------------------------------------
    cs = HoeffdingCS(spec)

    print(f"\nMonitoring conversion rate with 95% confidence sequence")
    print(f"Target rate: 50%")
    print(f"Data: {1000} user visits\n")

    # STEP 3: Stream data and monitor
    # --------------------------------
    # Simulate a website with true conversion rate of 55% (above target!)
    stream = generate_conversion_stream(true_rate=0.55, n=1000)

    print(f"{'Time':>6} | {'Rate':>6} | {'95% CI':>20} | {'Status':>12}")
    print("-" * 60)

    target_rate = 0.50
    decision = None

    for t, conversion in enumerate(stream, start=1):
        # Add new observation to the confidence sequence
        cs.update(conversion)

        # Check confidence interval every 100 observations
        if t % 100 == 0 or t == 1:
            iv = cs.interval()

            # Is the entire interval above our target?
            above_target = iv.lo > target_rate
            status = "ABOVE TARGET" if above_target else "UNCERTAIN"

            print(f"{t:6d} | {iv.estimate:6.3f} | ({iv.lo:.3f}, {iv.hi:.3f}) | {status:>12}")

            # STOPPING RULE: Stop early if we're confident rate > 50%
            if above_target and decision is None:
                decision = t
                print(f"\n*** STOPPED AT t={t}: Confident rate > 50% ***")
                print(f"    Lower bound of CI: {iv.lo:.3f} > {target_rate}")
                break

    # Final summary
    iv = cs.interval()
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Final estimate: {iv.estimate:.3f}")
    print(f"Final 95% CI:   ({iv.lo:.3f}, {iv.hi:.3f})")
    print(f"Total samples:  {iv.t}")
    print(f"Guarantee tier: {iv.tier}")
    print(f"\nKEY INSIGHT: We stopped early (at t={decision}) but our")
    print(f"confidence guarantees remain valid! This is the power of")
    print(f"anytime-valid inference.")

if __name__ == "__main__":
    main()
