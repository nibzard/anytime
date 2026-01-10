#!/usr/bin/env python3
"""
08_multiple_comparisons.py - Testing Multiple Variants

ADVANCED

This example demonstrates how to properly test multiple variants while
controlling the family-wise error rate. When testing k variants, the chance
of at least one false positive increases with k unless you correct for it.

SCENARIO:
You're testing a new feature and have 5 different variants:
- Control (A): Baseline
- Variants B, C, D, E: Different implementations

You want to know which variant is best, but you must control the overall
error rate across all comparisons.

CONCEPTS:
- Multiple testing correction: Controlling family-wise error rate
- Bonferroni correction: Simple but conservative
- Holm-Bonferroni: Less conservative, uniformly more powerful
- Union-intersection testing: Combining evidence across tests
"""

from anytime import ABSpec
from anytime.evalues import TwoSampleMeanMixtureE
import random
import numpy as np

def generate_multi_variant_data(variant_rates, n_per_variant=200):
    """
    Generate data for multiple variants.

    variant_rates: dict like {'A': 0.50, 'B': 0.52, 'C': 0.55, ...}
    """
    variants = list(variant_rates.keys())
    random.seed(789)
    np.random.seed(789)

    for _ in range(n_per_variant):
        for variant in variants:
            value = 1 if random.random() < variant_rates[variant] else 0
            yield (variant, value)

def test_single_variant(spec, data_stream, control='A', variant='B'):
    """Test a single variant against control."""
    etest = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")

    # Filter data for control and this variant
    filtered_data = [(arm, val) for arm, val in data_stream if arm in [control, variant]]

    for arm, value in filtered_data:
        mapped_arm = "A" if arm == control else "B"
        etest.update((mapped_arm, value))

    return etest.evalue()

def bonferroni_correction(variants_data, alpha=0.05):
    """
    Apply Bonferroni correction for multiple comparisons.

    Each test uses alpha/k to maintain overall family-wise error rate.
    """
    k = len(variants_data)
    corrected_alpha = alpha / k
    threshold = 1 / corrected_alpha

    print(f"Bonferroni correction:")
    print(f"  Number of tests (k): {k}")
    print(f"  Original alpha: {alpha:.3f}")
    print(f"  Corrected alpha per test: {corrected_alpha:.4f}")
    print(f"  E-value threshold for significance: {threshold:.1f}")

    return corrected_alpha, threshold

def holm_bonferroni(variants_data, alpha=0.05):
    """
    Apply Holm-Bonferroni correction (step-down procedure).

    More powerful than Bonferroni while maintaining FWER control.
    """
    k = len(variants_data)

    # Sort by e-value (descending)
    sorted_tests = sorted(variants_data.items(), key=lambda x: x[1]['evalue'], reverse=True)

    print(f"\nHolm-Bonferroni (step-down) procedure:")
    print(f"{'Rank':>5} | {'Variant':>8} | {'E-value':>10} | {'Threshold':>12} | {'Significant':>11}")
    print("-" * 70)

    rejected = []
    for i, (variant, data) in enumerate(sorted_tests):
        evalue = data['evalue']
        # Threshold for this step
        threshold = 1 / (alpha / (k - i))

        # Check if we reject
        is_significant = evalue > threshold
        rejected.append(variant if is_significant else None)

        print(f"{i+1:5d} | {variant:>8} | {evalue:10.2f} | {threshold:12.1f} | "
              f"{'YES' if is_significant else 'NO':>11}")

        # Stop at first non-rejection (Holm stopping rule)
        if not is_significant:
            break

    return [v for v in rejected if v is not None]

def main():
    print("=" * 70)
    print("Multiple Comparisons with Error Rate Control")
    print("=" * 70)

    # STEP 1: Define the scenario
    # ----------------------------
    variant_rates = {
        'A': 0.50,  # Control (baseline)
        'B': 0.52,  # Small improvement
        'C': 0.55,  # Medium improvement
        'D': 0.50,  # No improvement (null)
        'E': 0.48,  # Worse than control!
    }

    print("\nScenario: Testing 5 variants")
    print("True conversion rates:")
    for variant, rate in variant_rates.items():
        print(f"  {variant}: {rate:.2%}")

    print("\nGoal: Find which variants are better than control (A)")
    print("Challenge: Control family-wise error rate across all tests\n")

    # STEP 2: Generate data
    # ----------------------
    data = list(generate_multi_variant_data(variant_rates, n_per_variant=200))

    # STEP 3: Run all pairwise tests (each variant vs control)
    # ---------------------------------------------------------
    spec = ABSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=False,
        name="multi_variant"
    )

    print("=" * 70)
    print("UNCORRECTED TESTS (Naive - Inflates Error Rate!)")
    print("=" * 70)

    variants_to_test = ['B', 'C', 'D', 'E']
    raw_results = {}

    for variant in variants_to_test:
        ev = test_single_variant(spec, data, control='A', variant=variant)
        raw_results[variant] = {'evalue': ev.e, 'decision': ev.decision}

    print(f"\n{'Variant':>8} | {'E-value':>10} | {'Decision':>10}")
    print("-" * 40)
    for variant, result in raw_results.items():
        print(f"{variant:>8} | {result['evalue']:10.2f} | "
              f"{'Significant' if result['evalue'] > 20 else 'Not Sig':>10}")

    # STEP 4: Apply Bonferroni correction
    # ------------------------------------
    print("\n" + "=" * 70)
    print("BONFERRONI CORRECTION")
    print("=" * 70)

    corrected_alpha, threshold = bonferroni_correction(raw_results)

    print(f"\n{'Variant':>8} | {'E-value':>10} | {'Decision':>10}")
    print("-" * 40)
    for variant, result in raw_results.items():
        significant = result['evalue'] > threshold
        print(f"{variant:>8} | {result['evalue']:10.2f} | "
              f"{'Significant' if significant else 'Not Sig':>10}")

    # STEP 5: Apply Holm-Bonferroni (more powerful)
    # ----------------------------------------------
    print("\n" + "=" * 70)
    print("HOLM-BONFERRONI (Step-Down) - More Powerful!")
    print("=" * 70)

    significant_variants = holm_bonferroni(raw_results, alpha=0.05)

    print(f"\nVariants significantly better than control: {significant_variants}")

    # STEP 6: Summary and recommendations
    # ------------------------------------
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"""
True improvements (from our setup):
  • B: +2% (small)  → {'Detected' if 'B' in significant_variants else 'Not detected'}
  • C: +5% (medium) → {'Detected' if 'C' in significant_variants else 'Not detected'}
  • D: 0% (null)    → {'Detected' if 'D' in significant_variants else 'Not detected'} (should be NO)
  • E: -2% (worse)  → {'Detected' if 'E' in significant_variants else 'Not detected'} (should be NO)

False positives: {len([v for v in significant_variants if v in ['D', 'E']])}/4
Expected: ≤ 5% family-wise error rate
    """)

    print("\n" + "=" * 70)
    print("WHICH CORRECTION TO USE?")
    print("=" * 70)

    print("""
Bonferroni Correction:
  ✓ Simple to implement
  ✓ Controls family-wise error rate (FWER)
  ✗ Very conservative for many tests
  ✗ Loses power as k increases

Holm-Bonferroni (Step-Down):
  ✓ Also controls FWER
  ✓ More powerful than Bonferroni
  ✓ Easy to implement
  ✓ Recommended for most use cases

Other Methods (not shown):
  • Benjamini-Hochberg: Controls FDR (false discovery rate)
    - Less stringent than FWER
    - Use when some false positives are acceptable
  • Group sequential: Pre-planned looks
    - Used in clinical trials
    - Requires careful planning

RECOMMENDATION:
  For testing multiple variants, use Holm-Bonferroni.
  It's simple, maintains error control, and has good power.
    """)

if __name__ == "__main__":
    main()
