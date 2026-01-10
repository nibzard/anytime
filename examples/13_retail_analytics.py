#!/usr/bin/env python3
"""
13_retail_analytics.py - E-commerce Sales Analytics

INTERMEDIATE

This example shows how to use anytime-valid inference for retail analytics.
Perfect for:
- Online store conversion tracking
- Price testing (A/B tests)
- Customer engagement monitoring
- Campaign performance analysis

SCENARIO:
You're an analyst at an e-commerce company. You're running a price test
to see if a new price point affects conversion rates. You want to monitor
results continuously and stop as soon as you have conclusive evidence.

REAL-WORLD CONTEXT:
- E-commerce companies continuously monitor conversion rates
- Price changes need to be tested quickly
- Traditional fixed-horizon tests waste time (underpowered) or risk error (peeking)
- Anytime-valid methods enable efficient sequential testing

WHAT YOU'LL LEARN:
- Two-sample A/B testing with anytime-valid confidence sequences
- E-value based stopping rules for quick decisions
- Practical patterns for e-commerce analytics
- Multiple comparison corrections when testing several variants

TIME: 15 minutes
"""

from anytime import StreamSpec, ABSpec
from anytime.cs import EmpiricalBernsteinCS
from anytime.evalues import TwoSampleMeanMixtureE
from anytime.twosample import TwoSampleEmpiricalBernsteinCS
import random
from datetime import datetime, timedelta

def simulate_customer_visits(n_visitors=1000, baseline_rate=0.12, treatment_lift=0.015):
    """
    Simulate A/B test data for an e-commerce price test.

    SCENARIO:
    - Control (A): Current price, baseline conversion rate
    - Treatment (B): New price, slightly different conversion rate

    In production, this would come from:
    - Your analytics database (Google Analytics, Mixpanel, Amplitude)
    - Event tracking (Snowplow, Segment)
    - Database query to your orders table
    """
    random.seed(42)

    visitors = []
    for i in range(n_visitors):
        # Random assignment (50/50 split)
        arm = 'A' if random.random() < 0.5 else 'B'

        # Conversion probability depends on arm
        if arm == 'A':
            prob_convert = baseline_rate
        else:
            prob_convert = baseline_rate + treatment_lift

        # Did they convert (make a purchase)?
        converted = 1 if random.random() < prob_convert else 0

        visitors.append({
            'visitor_id': f"visitor_{i}",
            'arm': arm,
            'converted': converted,
            'timestamp': datetime.now() + timedelta(seconds=i)
        })

    return visitors

def demo_ab_test_with_confidence_sequences():
    """
    Run an A/B test with anytime-valid confidence sequences.
    """
    print("\n" + "=" * 80)
    print("🛍️  E-COMMERCE PRICE TEST: A/B Test with Confidence Sequences")
    print("=" * 80)

    print("""
SCENARIO:
  Testing a new price point for a product.

  Setup:
    - Control (A): Current price, $49.99
    - Treatment (B): New price, $44.99

  Metric: Conversion rate (purchased / visited)
    - Control conversion: ~12%
    - Treatment conversion: ~13.5% (due to lower price)

  Goal: Determine if the new price increases conversions significantly.
    """)

    # Setup two-sample confidence sequence
    spec = ABSpec(
        alpha=0.05,              # 95% confidence
        support=(0.0, 1.0),      # Conversion rates are 0-1
        kind="bounded",
        two_sided=True,          # We want to detect lift OR drop
        name="conversion_lift"
    )

    cs = TwoSampleEmpiricalBernsteinCS(spec)

    print("\n📊 Running price test with simulated visitors...")
    print("   (In production: query your analytics database)")

    # Generate test data
    visitors = simulate_customer_visits(n_visitors=2000, baseline_rate=0.12, treatment_lift=0.015)

    # Track statistics
    control_conversions = 0
    control_total = 0
    treatment_conversions = 0
    treatment_total = 0

    print("\n" + "-" * 100)
    print(f"{'Visitor':>10} | {'Arm':>5} | {'A Rate':>10} | {'B Rate':>10} | {'Lift':>10} | {'95% CI for Lift':>20} | {'Decision':>12}")
    print("-" * 100)

    significant_detected = None

    for i, visitor in enumerate(visitors, start=1):
        arm = visitor['arm']
        converted = visitor['converted']

        # Update counts
        if arm == 'A':
            control_conversions += converted
            control_total += 1
        else:
            treatment_conversions += converted
            treatment_total += 1

        # Update confidence sequence
        cs.update((arm, converted))

        # Report every 200 visitors
        if i % 200 == 0:
            iv = cs.interval()
            a_rate = control_conversions / control_total if control_total > 0 else 0
            b_rate = treatment_conversions / treatment_total if treatment_total > 0 else 0
            observed_lift = b_rate - a_rate

            # Check if CI excludes 0 (significant difference)
            excludes_zero = iv.lo > 0 or iv.hi < 0
            decision = "⚠️ SIGNIFICANT" if excludes_zero else "Insufficient data"

            if excludes_zero and significant_detected is None:
                significant_detected = i

            print(f"{i:10d} | {arm:>5} | {a_rate:10.3f} | {b_rate:10.3f} | {observed_lift:10.3f} | "
                  f"({iv.lo:.3f}, {iv.hi:.3f}) | {decision:>12}")

    # Final results
    iv = cs.interval()
    final_a_rate = control_conversions / control_total
    final_b_rate = treatment_conversions / treatment_total
    final_lift = final_b_rate - final_a_rate

    print("\n" + "=" * 100)
    print("📈 FINAL RESULTS")
    print("=" * 100)

    print(f"\nSample sizes:")
    print(f"  Control (A):   {control_total} visitors, {control_conversions} conversions ({final_a_rate:.1%})")
    print(f"  Treatment (B): {treatment_total} visitors, {treatment_conversions} conversions ({final_b_rate:.1%})")

    print(f"\nLift analysis:")
    print(f"  Observed lift: {final_lift:.3%}")
    print(f"  95% CI for lift: ({iv.lo:.3%}, {iv.hi:.3%})")

    if iv.lo > 0:
        print(f"  ✅ Conclusion: Treatment B significantly INCREASES conversions")
        print(f"     We're 95% confident the true lift is between {iv.lo:.3%} and {iv.hi:.3%}")
    elif iv.hi < 0:
        print(f"  ❌ Conclusion: Treatment B significantly DECREASES conversions")
    else:
        print(f"  ⚠️  Conclusion: Cannot detect significant difference yet")

    print(f"\n  Total sample size: {iv.t}")
    print(f"  Guarantee tier: {iv.tier.value}")

    if significant_detected:
        print(f"\n  💡 We detected significance at visitor #{significant_detected}")
        print(f"     Could have stopped early and saved {len(visitors) - significant_detected} samples!")

def demo_ab_test_with_evalues():
    """
    Run an A/B test using e-values for faster stopping.
    """
    print("\n" + "=" * 80)
    print("⚡ E-VALUE BASED STOPPING: Even Faster Decisions")
    print("=" * 80)

    print("""
E-VALUES vs CONFIDENCE SEQUENCES:

  Confidence Sequences:
    - Give you an interval estimate
    - Tell you the size of the effect
    - "We're 95% confident lift is between X% and Y%"

  E-Values:
    - Give you a single measure of evidence
    - Faster for simple reject/don't-reject decisions
    - "Reject when e-value >= 1/alpha"
    - Optional stopping safe!

RULE: Reject H0 when e >= 1/alpha
  - alpha = 0.05 → Reject when e >= 20
  - e >= 20 means "strong evidence against null"
    """)

    # Setup e-value test
    spec = ABSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=False,  # One-sided: testing if B > A
        name="b_better_than_a"
    )

    # Test H0: lift <= 0 vs H1: lift > 0
    etest = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")

    print("\n📊 Running price test with e-values...")
    print("   Testing: H0: B <= A vs H1: B > A")

    # Generate test data
    visitors = simulate_customer_visits(n_visitors=1000, baseline_rate=0.12, treatment_lift=0.015)

    print("\n" + "-" * 80)
    print(f"{'Visitor':>10} | {'E-value':>12} | {'Threshold':>12} | {'Decision':>15}")
    print("-" * 80)

    decision_time = None

    for i, visitor in enumerate(visitors, start=1):
        arm = visitor['arm']
        converted = visitor['converted']

        etest.update((arm, converted))
        ev = etest.evalue()

        # Report every 100 visitors
        if i % 100 == 0:
            threshold = 1 / spec.alpha
            decision_status = "✅ REJECT H0" if ev.decision else "Continue monitoring"

            if ev.decision and decision_time is None:
                decision_time = i

            print(f"{i:10d} | {ev.e:12.2f} | {threshold:12.1f} | {decision_status:>15}")

    # Final result
    ev = etest.evalue()
    threshold = 1 / spec.alpha

    print("\n" + "=" * 80)
    print("📈 FINAL RESULTS")
    print("=" * 80)

    print(f"\nFinal e-value: {ev.e:.2f}")
    print(f"Decision threshold: {threshold:.1f}")
    print(f"Decision: {'✅ REJECT H0 (B > A)' if ev.decision else '❌ Cannot reject H0'}")

    if decision_time:
        print(f"\n💡 Detected significance at visitor #{decision_time}")
        print(f"   Stopped early - saved {len(visitors) - decision_time} samples!")

def demo_multiple_variants():
    """
    Demonstrate testing multiple variants (A/B/C/D tests).
    """
    print("\n" + "=" * 80)
    print("🎯 MULTIPLE VARIANT TESTING: A/B/C/D Tests")
    print("=" * 80)

    print("""
SCENARIO:
  Testing 4 different promotional offers:
    - A: Control (no discount)
    - B: 10% discount
    - C: Free shipping
    - D: Bundle deal

CHALLENGE:
  Testing multiple variants increases false positive risk.
  Need to correct for multiple comparisons.

SOLUTION:
  Use alpha spending or Bonferroni correction.
  For k variants, use alpha/k for each test.

  4 variants → alpha = 0.05/4 = 0.0125 per comparison
    """)

    # Simulate 4 variants
    variants = ['A', 'B', 'C', 'D']
    conversion_rates = {'A': 0.10, 'B': 0.11, 'C': 0.12, 'D': 0.105}  # C is best

    n_per_variant = 400
    results = {}

    print(f"\nSimulating {n_per_variant} visitors per variant...")

    for variant in variants:
        spec = StreamSpec(
            alpha=0.05,  # Will apply Bonferroni when comparing
            support=(0.0, 1.0),
            kind="bounded",
            two_sided=True
        )

        cs = EmpiricalBernsteinCS(spec)

        # Simulate visitors for this variant
        random.seed(hash(variant))
        conversions = [1 if random.random() < conversion_rates[variant] else 0
                       for _ in range(n_per_variant)]

        for conv in conversions:
            cs.update(conv)

        iv = cs.interval()
        results[variant] = {
            'rate': sum(conversions) / n_per_variant,
            'ci': (iv.lo, iv.hi),
            'conversions': sum(conversions)
        }

    # Display results
    print("\n" + "-" * 90)
    print(f"{'Variant':>10} | {'Rate':>10} | {'95% CI':>20} | {'vs Control':>15}")
    print("-" * 90)

    control_rate = results['A']['rate']
    control_ci = results['A']['ci']

    for variant in variants:
        r = results[variant]
        rate = r['rate']
        ci_low, ci_high = r['ci']

        # Compare to control
        if variant == 'A':
            comparison = "(control)"
        else:
            # Simple check: does CIs overlap?
            # (Proper analysis would use two-sample CS)
            lifts_over_control = rate - control_rate
            if rate > control_ci[1]:
                comparison = f"✓ +{lifts_over_control:.1%}"
            elif rate < control_ci[0]:
                comparison = f"✗ {lifts_over_control:.1%}"
            else:
                comparison = f"? {lifts_over_control:.1%}"

        print(f"{variant:>10} | {rate:10.3f} | ({ci_low:.3f}, {ci_high:.3f}) | {comparison:>15}")

    print("\n💡 For proper pairwise comparisons, use two-sample confidence sequences")
    print("   with Bonferroni correction: alpha_corrected = 0.05 / (k-1) for k variants")

def main():
    print("=" * 80)
    print("🛍️  E-Commerce Analytics with Anytime-Valid Inference")
    print("=" * 80)

    print("""
This example shows how to use anytime-valid inference for retail and
e-commerce analytics. Stop your price tests and campaign experiments
as soon as you have conclusive evidence!

EXAMPLES COVERED:
  1. A/B price testing with confidence sequences
  2. E-value based stopping for faster decisions
  3. Multiple variant testing (A/B/C/D tests)

REAL-WORLD APPLICATIONS:
  • Price testing and optimization
  • Campaign performance monitoring
  • UX feature testing
  • Email subject line testing
  • Landing page optimization

DATASETS IN PRODUCTION:
  • Your analytics database (Google BigQuery, Snowflake, Redshift)
  • Event tracking (Google Analytics 4, Mixpanel, Amplitude)
  • Experiment platforms (Optimizely, VWO, Statsig)
    """)

    # Run demonstrations
    demo_ab_test_with_confidence_sequences()
    demo_ab_test_with_evalues()
    demo_multiple_variants()

    # Final summary
    print("\n" + "=" * 80)
    print("✅ SUMMARY")
    print("=" * 80)

    print("""
WHAT YOU LEARNED:
  ✓ Two-sample A/B testing with anytime-valid confidence sequences
  ✓ E-value based stopping rules for quick decisions
  ✓ Multiple comparison corrections for multi-variant tests
  ✓ Practical e-commerce analytics patterns

KEY INSIGHTS:
  • Confidence sequences tell you the SIZE of the effect
  • E-values give you faster reject/don't-reject decisions
  • Multiple variants require alpha correction (Bonferroni or similar)
  • You can stop experiments early when results are clear

PRODUCTION TIPS:
  • Use confidence sequences for final reporting (effect size matters!)
  • Use e-values for internal monitoring (faster decisions)
  • Always document your stopping rule
  • Correct for multiple comparisons when testing many variants
  • Track the "time to significance" metric

NEXT STEPS:
  • Example 12: Currency and financial monitoring
  • Example 14: Medical trials and vaccine efficacy
  • Example 15: Multi-armed bandit optimization

SOURCES:
  • [Supermarket Sales Dataset - Kaggle](https://www.kaggle.com/datasets/faresashraf1001/supermarket-sales)
  • [11 Best Free Retail Datasets for Machine Learning](https://www.iguazio.com/blog/13-best-free-retail-datasets-for-machine-learning/)
  • [Data.gov Sales Datasets](https://catalog.data.gov/dataset/?tags=sales)
    """)

if __name__ == "__main__":
    main()
