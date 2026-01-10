#!/usr/bin/env python3
"""
00_super_simple.py - Simplest Possible Start (5 minutes)

BEGINNER

This is the FRIENDLIEST way to start with anytime inference.
No complex math, no jargon - just practical monitoring.

SCENARIO: You're tracking website sign-ups. Each person either signs up (1) or doesn't (0).
You want to know: "What's our sign-up rate?" with confidence.

WHAT YOU'LL LEARN:
- How to create a confidence sequence in 3 lines
- How to update it with new data
- How to get a confidence interval

TIME: 5 minutes
"""

from anytime import StreamSpec
from anytime.cs import HoeffdingCS

def main():
    print("=" * 60)
    print("🚀 Super Simple Start: Monitoring Sign-Ups")
    print("=" * 60)

    # STEP 1: Create your spec (one line!)
    # ------------------------------------
    # alpha = 0.05 → 95% confidence (5% error rate)
    # support = (0, 1) → values are between 0 and 1
    # two_sided = True → we want both upper and lower bounds
    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)

    # STEP 2: Create confidence sequence (one line!)
    # -----------------------------------------------
    cs = HoeffdingCS(spec)

    print("\n📊 Tracking sign-ups...")
    print("\nEach ✓ = someone signed up (1)")
    print("Each ✗ = no sign-up (0)")
    print()

    # STEP 3: Stream data and see results!
    # -------------------------------------
    # Simulating a week of website traffic
    # True sign-up rate is about 40%
    import random
    random.seed(42)

    signups = []
    for day in range(7):
        # Simulate 100 visitors per day
        daily_visitors = 100
        daily_signups = 0

        for visitor in range(daily_visitors):
            # 40% chance of signing up
            did_signup = 1 if random.random() < 0.40 else 0
            signups.append(did_signup)
            cs.update(did_signup)
            daily_signups += did_signup

        # Get current confidence interval
        interval = cs.interval()

        # Pretty print results
        rate = daily_signups / daily_visitors * 100
        ci_lower = interval.lo * 100
        ci_upper = interval.hi * 100

        print(f"Day {day + 1}: {daily_signups}/{daily_visitors} signed up ({rate:.1f}%)")
        print(f"        → We're 95% confident the true rate is: {ci_lower:.1f}% to {ci_upper:.1f}%")
        print()

    # FINAL SUMMARY
    # -------------
    final = cs.interval()
    total_signups = sum(signups)
    total_visitors = len(signups)
    actual_rate = total_signups / total_visitors * 100

    print("=" * 60)
    print("📈 FINAL RESULTS")
    print("=" * 60)
    print(f"Total visitors:  {total_visitors}")
    print(f"Total sign-ups:  {total_signups}")
    print(f"Actual rate:     {actual_rate:.1f}%")
    print(f"\n95% Confidence Interval:")
    print(f"  Lower bound:   {final.lo * 100:.1f}%")
    print(f"  Point estimate: {final.estimate * 100:.1f}%")
    print(f"  Upper bound:   {final.hi * 100:.1f}%")

    print("\n" + "=" * 60)
    print("💡 KEY INSIGHT")
    print("=" * 60)
    print("""
The confidence interval tells you:
• "We're 95% confident the TRUE sign-up rate is between X% and Y%"
• You could stop checking at ANY time and still be valid!
• Unlike traditional statistics, you can peek as often as you want!

NEXT STEPS:
• Try example 01 to learn more about early stopping
• Try example 02 for binary data (coin flips)
• Try example 03 for A/B testing
    """)

if __name__ == "__main__":
    main()
