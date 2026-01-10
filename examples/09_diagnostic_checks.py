#!/usr/bin/env python3
"""
09_diagnostic_checks.py - Using Assumption Diagnostics

ADVANCED

This example demonstrates the diagnostic system in anytime, which checks
whether your data satisfies the assumptions required for statistical
guarantees. When assumptions are violated, the system downgrades the
guarantee tier and provides diagnostic information.

SCENARIO:
You're running a production monitoring system that processes real-world data
with potential issues: out-of-range values, missing data, concept drift.
The diagnostic system helps you detect and handle these issues.

CONCEPTS:
- Guarantee tiers: GUARANTEED, CLIPPED, DIAGNOSTIC
- Assumption checking: Range validation, missingness detection
- Diagnostic tags: Out-of-range, missing values, drift warnings
- Production readiness: Building robust monitoring systems
"""

import sys
sys.path.insert(0, '..')

from anytime import StreamSpec, GuaranteeTier
from anytime.cs import HoeffdingCS, EmpiricalBernsteinCS
import random

def generate_clean_stream(n=100):
    """Generate clean data that satisfies all assumptions."""
    random.seed(111)
    for _ in range(n):
        yield random.random()  # Values in [0, 1]

def generate_out_of_range_stream(n=100):
    """Generate data with out-of-range values."""
    random.seed(222)
    for _ in range(n):
        # Occasionally generate out-of-range values
        if random.random() < 0.05:
            yield 1.5  # OUT OF RANGE! (> 1.0)
        else:
            yield random.random()

def generate_missing_data_stream(n=100):
    """Generate data with occasional missing values (NaN)."""
    random.seed(333)
    for _ in range(n):
        # Occasionally generate missing values
        if random.random() < 0.10:
            yield float("nan")  # MISSING!
        else:
            yield random.random()

def generate_drift_stream(n=100):
    """Generate data with concept drift (mean shifts over time)."""
    random.seed(444)
    mean = 0.3
    for i in range(n):
        # Drift: mean increases from 0.3 to 0.7 over time
        mean = 0.3 + (0.4 * i / n)
        yield min(1.0, max(0.0, mean + random.uniform(-0.1, 0.1)))

def demonstrate_diagnostics(stream_name, data_stream, clip_mode="error"):
    """Demonstrate diagnostic system on a data stream."""
    print(f"\n{'=' * 70}")
    print(f"Testing: {stream_name}")
    print(f"Clip mode: {clip_mode}")
    print('=' * 70)

    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True,
        name="test",
        clip_mode=clip_mode  # "error" or "clip"
    )

    cs = HoeffdingCS(spec)

    print(f"\n{'t':>5} | {'Value':>8} | {'Estimate':>9} | {'Tier':>12} | {'Diagnostics':>20}")
    print("-" * 75)

    violations = []

    for t, value in enumerate(data_stream, start=1):
        try:
            cs.update(value)

            if t % 20 == 0 or t == 1:
                iv = cs.interval()

                diag_str = str(iv.diagnostics) if iv.diagnostics else "None"

                print(f"{t:5d} | {value:8.3f} | {iv.estimate:9.3f} | "
                      f"{iv.tier.value:>12} | {diag_str:>20}")

                if iv.tier != GuaranteeTier.GUARANTEED:
                    violations.append((t, iv.tier, iv.diagnostics))

        except Exception as e:
            print(f"{t:5d} | {value:8.3f} | ERROR: {str(e)}")
            violations.append((t, "ERROR", str(e)))

    if violations:
        print(f"\n⚠️  Violations detected: {len(violations)}")
        print("First few violations:")
        for t, tier, diag in violations[:3]:
            print(f"  t={t}: {tier} - {diag}")
    else:
        print(f"\n✓ No violations detected!")

    return cs.interval()

def main():
    print("=" * 70)
    print("Assumption Diagnostics for Production Systems")
    print("=" * 70)

    print("""
The anytime library provides a comprehensive diagnostic system that checks
whether your data satisfies the assumptions required for statistical guarantees.

GUARANTEE TIERS:
  • GUARANTEED: All assumptions satisfied, full statistical guarantees
  • CLIPPED: Out-of-range values clipped, guarantees apply to clipped stream
  • DIAGNOSTIC: Assumptions violated, no statistical guarantees

COMMON ISSUES DETECTED:
  • Out-of-range values (data outside declared support)
  • Missing values (None, NaN)
  • Concept drift (distribution shifts over time)
    """)

    # TEST 1: Clean data (should be GUARANTEED)
    # ------------------------------------------
    print("\n" + "=" * 70)
    print("TEST 1: Clean Data (All Assumptions Satisfied)")
    print("=" * 70)

    result = demonstrate_diagnostics(
        "Clean Stream",
        generate_clean_stream(100)
    )

    print(f"\nFinal tier: {result.tier.value}")
    print(f"Expected: GUARANTEED")

    # TEST 2: Out-of-range data (should error or clip)
    # -------------------------------------------------
    print("\n" + "=" * 70)
    print("TEST 2: Out-of-Range Data (Assumption Violation)")
    print("=" * 70)

    # First with error mode (default)
    print("\n--- With clip_mode='error' (default) ---")
    try:
        result = demonstrate_diagnostics(
            "Out-of-Range Stream",
            generate_out_of_range_stream(100),
            clip_mode="error"
        )
    except Exception as e:
        print(f"\n✗ Process stopped due to error: {e}")

    # Now with clip mode
    print("\n--- With clip_mode='clip' ---")
    result = demonstrate_diagnostics(
        "Out-of-Range Stream (clipped)",
        generate_out_of_range_stream(100),
        clip_mode="clip"
    )

    print(f"\nFinal tier: {result.tier.value}")
    print(f"Expected: CLIPPED (values were clipped to [0, 1])")

    # TEST 3: Missing data
    # ---------------------
    print("\n" + "=" * 70)
    print("TEST 3: Missing Data")
    print("=" * 70)

    result = demonstrate_diagnostics(
        "Missing Data Stream",
        generate_missing_data_stream(100)
    )

    print(f"\nFinal tier: {result.tier.value}")
    print(f"Missing values are tracked in diagnostics")

    # TEST 4: Concept drift
    # ----------------------
    print("\n" + "=" * 70)
    print("TEST 4: Concept Drift (Distribution Shift)")
    print("=" * 70)

    result = demonstrate_diagnostics(
        "Drifting Stream",
        generate_drift_stream(100)
    )

    print(f"\nFinal tier: {result.tier.value}")
    print(f"Note: Drift doesn't violate boundedness, but may affect practical performance")

    # SUMMARY: Production checklist
    # -----------------------------
    print("\n" + "=" * 70)
    print("PRODUCTION READINESS CHECKLIST")
    print("=" * 70)

    print("""
BEFORE DEPLOYING TO PRODUCTION:

1. Data Validation
   □ Verify your data falls within declared support bounds
   □ Handle missing values appropriately (impute or filter)
   □ Check for outliers and decide on clipping strategy

2. Monitoring Setup
   □ Set up alerts for tier downgrades (GUARANTEED → CLIPPED/DIAGNOSTIC)
   □ Log diagnostic information for debugging
   □ Track assumption violations over time

3. Error Handling
   □ Choose clip_mode based on your use case:
     - "error": Fail fast when assumptions violated (safer)
     - "clip": Continue with clipped values (more robust)

4. Testing
   □ Run your pipeline on historical data first
   □ Verify assumptions hold in production environment
   □ Set up monitoring dashboards

5. Documentation
   □ Document expected data ranges and sources
   □ Document what happens when assumptions are violated
   □ Create runbooks for handling tier downgrades

RECOMMENDED PRODUCTION PATTERN:

```python
from anytime import StreamSpec, GuaranteeTier
from anytime.cs import EmpiricalBernsteinCS

spec = StreamSpec(
    alpha=0.05,
    support=(0.0, 1.0),
    kind="bounded",
    two_sided=True,
    clip_mode="clip"  # Handle out-of-range gracefully
)

cs = EmpiricalBernsteinCS(spec)

for value in data_stream:
    cs.update(value)

    # Check guarantee tier
    iv = cs.interval()
    if iv.tier == GuaranteeTier.DIAGNOSTIC:
        # Alert: assumptions violated!
        send_alert(f"Diagnostic warning: {iv.diagnostics}")

    # Only make decisions if tier is GUARANTEED or CLIPPED
    if iv.tier in [GuaranteeTier.GUARANTEED, GuaranteeTier.CLIPPED]:
        # Safe to use the interval
        make_decision(iv)
```
    """)

if __name__ == "__main__":
    main()
