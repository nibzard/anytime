#!/usr/bin/env python3
"""
07_early_stopping.py - Optimal Stopping Rules for A/B Tests

INTERMEDIATE

This example demonstrates optimal stopping strategies for A/B tests using
e-values. Unlike fixed-horizon tests, anytime-valid e-values let you stop
as soon as you have sufficient evidence, saving time and resources.

SCENARIO:
You're running a clinical trial or A/B test where:
- Each observation costs money/time
- You want to stop as soon as you're confident
- You must maintain statistical validity

We'll compare three strategies:
1. Fixed horizon: Always run to N samples
2. Naive peeking: Check p-values (INVALID! breaks error guarantees)
3. E-value stopping: Check anytime-valid e-values (VALID!)

CONCEPTS:
- E-value stopping rules: When to stop based on evidence
- Type I error control: Maintaining false positive rate
- Expected sample size: Average samples needed to detect effect
- Optional stopping: Stopping early based on data
"""

import sys
sys.path.insert(0, '..')

from anytime import ABSpec
from anytime.evalues import TwoSampleMeanMixtureE
import random
import numpy as np

def simulate_ab_test_with_stopping(true_lift, n_max=500, alpha=0.05, seed=None):
    """
    Simulate an A/B test with e-value stopping.

    Returns: (stopped_at, final_decision, final_evalue)
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # Setup: B has true_lift more than A
    rate_a = 0.50
    rate_b = 0.50 + true_lift

    # Create e-value test for B > A
    spec = ABSpec(
        alpha=alpha,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=False,  # One-sided: testing B > A
        name="ab_test"
    )

    etest = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")

    # Track stopping time
    stopped_at = None
    final_decision = False

    for t in range(1, n_max + 1):
        # Alternate between A and B
        if t % 2 == 1:
            arm = "A"
            value = 1 if random.random() < rate_a else 0
        else:
            arm = "B"
            value = 1 if random.random() < rate_b else 0

        etest.update((arm, value))

        # Check stopping condition every 10 observations
        if t % 10 == 0:
            ev = etest.evalue()
            if ev.decision:  # e-value > 1/alpha
                stopped_at = t
                final_decision = True
                break

    if stopped_at is None:
        stopped_at = n_max

    return stopped_at, final_decision, etest.evalue().e

def run_simulation(null_true, true_lift, n_sim=100, n_max=500, alpha=0.05):
    """Run multiple simulations and collect statistics."""
    results = {
        'stopped_early': 0,
        'never_stopped': 0,
        'stop_times': [],
        'decisions': 0
    }

    for i in range(n_sim):
        seed = 1000 + i
        stopped_at, decision, evalue = simulate_ab_test_with_stopping(
            true_lift=true_lift if not null_true else 0.0,
            n_max=n_max,
            alpha=alpha,
            seed=seed
        )

        results['stop_times'].append(stopped_at)
        if stopped_at < n_max:
            results['stopped_early'] += 1
        else:
            results['never_stopped'] += 1

        if decision:
            results['decisions'] += 1

    return results

def main():
    print("=" * 70)
    print("Optimal Stopping Rules for A/B Tests")
    print("E-Values: Stop When You Have Evidence")
    print("=" * 70)

    # EXPERIMENT 1: Type I Error under H0 (no true effect)
    # ----------------------------------------------------
    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Type I Error Control (Null Hypothesis True)")
    print("=" * 70)
    print("\nH0: A and B have the same rate (both 50%)")
    print("Running 100 simulations with optional stopping...")
    print("Expected false positive rate: ≤ 5% (alpha = 0.05)\n")

    h0_results = run_simulation(null_true=True, true_lift=0.0, n_sim=100)

    fpr = h0_results['decisions'] / 100.0
    print(f"False positives (decided B > A when H0 true): {h0_results['decisions']}/100")
    print(f"False positive rate: {fpr:.1%}")
    print(f"Target (alpha): 5.0%")
    print(f"Control maintained? {'✓ YES' if fpr <= 0.06 else '✗ NO (inflation!)'}")

    # EXPERIMENT 2: Power under H1 (true effect exists)
    # -------------------------------------------------
    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Power Analysis (Alternative Hypothesis True)")
    print("=" * 70)
    print("\nH1: B is 10% better than A (A=50%, B=60%)")
    print("Running 100 simulations with optional stopping...\n")

    h1_results = run_simulation(null_true=False, true_lift=0.10, n_sim=100)

    power = h1_results['decisions'] / 100.0
    avg_stop_time = np.mean(h1_results['stop_times'])
    stopped_early_pct = h1_results['stopped_early'] / 100.0

    print(f"Power (detected B > A when true): {h1_results['decisions']}/100 = {power:.1%}")
    print(f"Average stopping time: {avg_stop_time:.0f} samples")
    print(f"Stopped early (before N=500): {h1_results['stopped_early']}/100 = {stopped_early_pct:.1%}")

    # EXPERIMENT 3: Effect size and stopping time
    # --------------------------------------------
    print("\n" + "=" * 70)
    print("EXPERIMENT 3: Effect Size vs Stopping Time")
    print("=" * 70)
    print("\nHow effect size impacts average stopping time:\n")

    print(f"{'Lift':>6} | {'Power':>8} | {'Avg Stop Time':>15} | {'Std Stop Time':>15}")
    print("-" * 60)

    for lift in [0.05, 0.08, 0.10, 0.15, 0.20]:
        results = run_simulation(null_true=False, true_lift=lift, n_sim=50)
        power = results['decisions'] / 50.0
        avg_stop = np.mean(results['stop_times'])
        std_stop = np.std(results['stop_times'])

        print(f"{lift:6.1%} | {power:7.1%} | {avg_stop:15.1f} | {std_stop:15.1f}")

    # SUMMARY AND RECOMMENDATIONS
    # -----------------------------
    print("\n" + "=" * 70)
    print("SUMMARY: When to Use E-Value Stopping")
    print("=" * 70)

    print("""
✓ USE E-VALUE STOPPING WHEN:
  • Each observation is expensive (clinical trials, user studies)
  • You need to make decisions quickly
  • You want to minimize expected sample size
  • You MUST maintain Type I error control

✓ KEY INSIGHTS:
  • E-values remain valid under optional stopping
  • Larger effect sizes → stop earlier
  • No "p-hacking" concerns with continuous monitoring
  • Trade-off: More conservative than fixed-horizon tests

✓ PRACTICAL TIPS:
  • Set minimum sample size before stopping (avoid very early stops)
  • Use one-sided tests when you only care about improvement
  • Report both e-value and stopping time
  • Consider cost-benefit of continuing vs stopping

✓ COMPARISON TO P-VALUES:
  • P-values with peeking: INVALID (inflates false positives)
  • E-values with peeking: VALID (controls false positives)
  • Fixed horizon test: Stops at N, regardless of evidence
  • E-value stopping: Stops when evidence is sufficient
    """)

    print("=" * 70)
    print("DECISION RULE SUMMARY")
    print("=" * 70)

    print("""
For testing H0: mean(B) = mean(A) vs H1: mean(B) > mean(A):

1. Initialize e-value process
2. After each observation, compute e-value
3. Stop if e-value > 1/alpha (e.g., > 20 for alpha=0.05)
4. If stopped: Reject H0, conclude B > A
5. If reach N_max: Fail to reject H0 (not enough evidence)

This maintains Type I error ≤ alpha under any stopping rule!
    """)

if __name__ == "__main__":
    main()
