#!/usr/bin/env python3
"""
11_real_world_data.py - Working with Real Datasets

ADVANCED

This example shows you how to use anytime inference with REAL data from
the UCI Machine Learning Repository. We'll analyze mushroom edibility
patterns - a classic binary classification problem.

DATASET: Mushroom Classification Dataset (UCI ML Repository)
- 8,124 mushrooms
- 22 features (cap shape, color, odor, etc.)
- Binary target: edible (e) or poisonous (p)

SCENARIO: You're a data scientist analyzing mushroom samples. You receive
batches of mushrooms and want to track what percentage are edible with
statistical guarantees - even if you stop sampling early.

WHAT YOU'LL LEARN:
- Loading real datasets
- Processing categorical features into binary metrics
- Real-time monitoring with confidence intervals
- Production-like data pipeline patterns

DATASET SOURCE: https://archive.ics.uci.edu/ml/datasets/mushroom
"""

from anytime import StreamSpec
from anytime.cs import HoeffdingCS, BernoulliCS
from pathlib import Path
import csv

def load_mushroom_data():
    """Load the mushroom dataset from UCI ML Repository."""
    # The dataset should be in datasets/mushroom.data
    # Download from: https://archive.ics.uci.edu/ml/machine-learning-databases/mushroom/agaricus-lepiota.data

    data_path = Path(__file__).parent / "datasets" / "mushroom.data"

    if not data_path.exists():
        print("⚠️  Dataset not found!")
        print(f"Expected: {data_path}")
        print("\nTo download the dataset:")
        print("  curl -o datasets/mushroom.data \\")
        print("    https://archive.ics.uci.edu/ml/machine-learning-databases/mushroom/agaricus-lepiota.data")
        print("\nFor now, using simulated data...")
        return generate_simulated_mushrooms()

    print("✓ Loaded real mushroom dataset from UCI ML Repository")
    mushrooms = []
    with open(data_path, 'r') as f:
        for line in f:
            features = line.strip().split(',')
            # First column is edibility: e=edible, p=poisonous
            edible = 1 if features[0] == 'e' else 0
            mushrooms.append(edible)
    return mushrooms

def generate_simulated_mushrooms():
    """Generate simulated mushroom data for demonstration."""
    import random
    random.seed(42)
    print("✓ Using simulated mushroom data")
    return [1 if random.random() < 0.52 else 0 for _ in range(1000)]

def analyze_edibility_stream(mushrooms, batch_size=200):
    """Analyze mushroom edibility with streaming confidence sequences."""
    print("\n" + "=" * 70)
    print("STREAMING ANALYSIS: Mushroom Edibility Rate")
    print("=" * 70)

    # Setup confidence sequence
    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bernoulli",  # Binary: edible (1) or poisonous (0)
        two_sided=True,
        name="edibility_rate"
    )

    cs = BernoulliCS(spec)

    print("\nProcessing mushrooms in batches...")
    print(f"{'Batch':>8} | {'Edible':>8} | {'Total':>8} | {'Rate %':>8} | {'95% CI':>20}")
    print("-" * 70)

    for i in range(0, len(mushrooms), batch_size):
        batch = mushrooms[i:i+batch_size]

        # Update confidence sequence
        for mushroom in batch:
            cs.update(mushroom)

        # Get current interval
        iv = cs.interval()
        batch_num = i // batch_size + 1
        edible_count = sum(mushrooms[i:i+len(batch)])
        rate_pct = iv.estimate * 100

        print(f"{batch_num:>8} | {edible_count:>8} | {iv.t:>8} | {rate_pct:>7.1f}% | "
              f"({iv.lo*100:.1f}%, {iv.hi*100:.1f}%)")

    return cs.interval()

def compare_methods(mushrooms):
    """Compare Hoeffding vs Bernoulli-specific methods."""
    print("\n" + "=" * 70)
    print("METHOD COMPARISON: Hoeffding vs Bernoulli-Specific")
    print("=" * 70)

    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True,
        name="comparison"
    )

    # Test with first 1000 mushrooms
    n_test = min(1000, len(mushrooms))
    test_data = mushrooms[:n_test]

    # Hoeffding (generic bounded)
    hoeffding_cs = HoeffdingCS(spec)
    for x in test_data:
        hoeffding_cs.update(x)
    h_iv = hoeffding_cs.interval()

    # Bernoulli-specific (tighter for binary)
    bern_spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bernoulli",
        two_sided=True,
        name="bernoulli_comparison"
    )
    bern_cs = BernoulliCS(bern_spec)
    for x in test_data:
        bern_cs.update(x)
    b_iv = bern_cs.interval()

    print(f"\nAfter {n_test} mushrooms:")
    print(f"\n{'Method':>20} | {'Estimate':>10} | {'95% CI Width':>15} | {'Tighter?':>10}")
    print("-" * 70)

    h_width = h_iv.hi - h_iv.lo
    b_width = b_iv.hi - b_iv.lo

    print(f"{'Hoeffding':>20} | {h_iv.estimate:>10.3f} | {h_width:>15.3f} | {'-':>10}")
    print(f"{'Bernoulli-Specific':>20} | {b_iv.estimate:>10.3f} | {b_width:>15.3f} | "
          f"{'✓ Yes!' if b_width < h_width else 'No':>10}")

    improvement = (1 - b_width / h_width) * 100
    print(f"\nBernoulli-specific is {improvement:.1f}% tighter!")

def main():
    print("=" * 70)
    print("🍄 Real-World Data Analysis: Mushroom Edibility")
    print("=" * 70)

    print("""
DATASET: UCI Mushroom Classification
SOURCE: https://archive.ics.uci.edu/ml/datasets/mushroom

This dataset contains 8,124 mushroom samples with 22 features describing:
- Cap shape, color, surface
- Gill size, spacing, color
- Stalk shape, color, ring type
- Spore print color
- Population, habitat
- Edibility: edible (e) or poisonous (p)

We'll analyze: What percentage of mushrooms are edible?
    """)

    # Load real data
    mushrooms = load_mushroom_data()

    print(f"\nTotal mushrooms: {len(mushrooms)}")
    print(f"Edible mushrooms: {sum(mushrooms)}")
    print(f"Actual edibility rate: {sum(mushrooms)/len(mushrooms)*100:.1f}%")

    # Run streaming analysis
    final_iv = analyze_edibility_stream(mushrooms, batch_size=200)

    # Compare methods
    compare_methods(mushrooms)

    # FINAL SUMMARY
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)

    print(f"\nAfter analyzing all {len(mushrooms)} mushrooms:")
    print(f"  Edibility rate:      {final_iv.estimate*100:.1f}%")
    print(f"  95% CI:             ({final_iv.lo*100:.1f}%, {final_iv.hi*100:.1f}%)")
    print(f"  Guarantee tier:     {final_iv.tier.value}")

    print("\n" + "=" * 70)
    print("💡 KEY INSIGHTS")
    print("=" * 70)

    print(f"""
✓ REAL DATA PATTERNS:
  • We analyzed {len(mushrooms)} real mushroom samples
  • Confidence intervals narrow as we collect more data
  • Bernoulli-specific CS is tighter than generic Hoeffding

✓ PRODUCTION PATTERNS:
  • Data arrives in batches (200 samples at a time)
  • We update our confidence after each batch
  • We could stop at any batch and still be valid

✓ WHEN TO USE:
  • Quality control in manufacturing
  • Medical diagnosis accuracy tracking
  • User engagement monitoring
  • Any binary outcome tracking

NEXT STEPS:
  • Example 10: More on CSV and API data sources
  • Example 09: Production diagnostics and monitoring
    """)

if __name__ == "__main__":
    main()
