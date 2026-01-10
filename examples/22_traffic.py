#!/usr/bin/env python3
"""
22_traffic.py - Website Traffic Analytics

BEGINNER-FRIENDLY!

Analyze website traffic with anytime-valid confidence sequences.
Perfect for bloggers, site owners, and marketers.

WHAT YOU'LL LEARN:
- Daily visitor tracking
- Bounce rate analysis
- Conversion rate monitoring
- Detecting traffic spikes

TIME: 10 minutes
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS, BernoulliCS
import random

def demo_visitor_tracking():
    """Track daily website visitors."""
    print("\n" + "=" * 70)
    print("📊 WEBSITE VISITOR TRACKING")
    print("=" * 70)

    print("""
SCENARIO: Tracking daily visitors to your blog

  Questions:
    • What's my true daily average?
    • Is traffic trending up or down?
    • When did I get a traffic spike?

  Anytime-valid advantage:
    ✓ Check analytics daily without penalty
    ✓ Valid confidence intervals anytime
    ✓ Stop A/B tests early
    """)

    # Simulate 30 days of traffic
    random.seed(42)
    visitors = []

    # Average 1000 visitors/day with variation
    for day in range(30):
        base = 1000
        variation = random.gauss(0, 200)  # ±200 visitors
        # Weekend boost
        if day % 7 in [5, 6]:
            variation += 150
        daily = int(base + variation)
        visitors.append(max(0, daily))

    # Track with confidence sequence
    spec = StreamSpec(
        alpha=0.05,
        support=(0, 10000),
        kind="bounded",
        two_sided=True,
        name="daily_visitors"
    )

    cs = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Day':>6} | {'Visitors':>10} | {'Avg':>10} | {'95% CI':>16} | {'Status':>10}")
    print("-" * 70)

    for day, count in enumerate(visitors, start=1):
        cs.update(count)

        if day % 5 == 0:
            iv = cs.interval()

            # Check for unusual traffic
            if count > iv.hi:
                status = "📈 High!"
            elif count < iv.lo:
                status = "📉 Low"
            else:
                status = "✓ Normal"

            print(f"{day:6d} | {count:10,d} | {iv.estimate:10,.0f} | "
                  f"({iv.lo:8,.0f}, {iv.hi:8,.0f}) | {status:>10}")

    iv = cs.interval()
    print("\n" + "=" * 70)
    print("30-DAY SUMMARY")
    print("=" * 70)
    print(f"\nDaily average: {iv.estimate:,.0f} visitors")
    print(f"95% CI: ({iv.lo:,.0f}, {iv.hi:,.0f})")
    print(f"Total for month: {sum(visitors):,} visitors")

def demo_bounce_rate():
    """Monitor website bounce rate."""
    print("\n" + "=" * 70)
    print("🔄 BOUNCE RATE MONITORING")
    print("=" * 70)

    print("""
SCENARIO: Tracking bounce rate (visitors who leave immediately)

  Good bounce rate: < 50%
  Excellent: < 40%
  Needs work: > 70%

  With confidence intervals, we know if changes are real!
    """)

    # Simulate visitors (1 = bounce, 0 = engaged)
    # True bounce rate is 45%
    random.seed(789)
    bounces = [1 if random.random() < 0.45 else 0 for _ in range(1000)]

    spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    for bounce in bounces:
        cs.update(bounce)

    iv = cs.interval()

    print(f"\nTotal visitors: {iv.t:,}")
    print(f"Bounce rate: {iv.estimate:.1%}")
    print(f"95% CI: ({iv.lo:.1%}, {iv.hi:.1%})")

    if iv.hi < 0.50:
        print("\n✅ Good! Upper bound below 50%")
    elif iv.lo > 0.50:
        print("\n⚠️  Needs improvement!")
    else:
        print("\n🤷 Uncertain - could be either way")

def demo_conversion_rate():
    """Monitor conversion rate (sign-ups, purchases)."""
    print("\n" + "=" * 70)
    print("🎯 CONVERSION RATE TRACKING")
    print("=" * 70)

    print("""
SCENARIO: Tracking email sign-up conversion rate

  Before change: 5% conversion
  After new design: 8% conversion

  Is the improvement real? Confidence intervals tell us!
    """)

    # Before: 5% conversion
    random.seed(111)
    before = [1 if random.random() < 0.05 else 0 for _ in range(1000)]

    # After: 8% conversion
    after = [1 if random.random() < 0.08 else 0 for _ in range(1000)]

    # Analyze both periods
    spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)

    cs_before = EmpiricalBernsteinCS(spec)
    for outcome in before:
        cs_before.update(outcome)

    cs_after = EmpiricalBernsteinCS(spec)
    for outcome in after:
        cs_after.update(outcome)

    iv_before = cs_before.interval()
    iv_after = cs_after.interval()

    print(f"\n{'Period':>10} | {'Rate':>10} | {'95% CI':>16}")
    print("-" * 45)
    print(f"{'Before':>10} | {iv_before.estimate:9.1%} | ({iv_before.lo:.1%}, {iv_before.hi:.1%})")
    print(f"{'After':>10} | {iv_after.estimate:9.1%} | ({iv_after.lo:.1%}, {iv_after.hi:.1%})")

    # Check if improvement is real
    if iv_after.lo > iv_before.hi:
        print("\n✅ Statistically significant improvement!")
    elif iv_after.estimate > iv_before.estimate:
        print("\n⚠️  Point estimate higher, but not statistically significant")
    else:
        print("\n❌ No improvement detected")

def demo_real_analytics():
    """Show how to get real analytics data."""
    print("\n" + "=" * 70)
    print("🌐 REAL ANALYTICS DATA")
    print("=" * 70)

    print("""
To get REAL website analytics, use these tools:

FREE OPTIONS:
-------------

1. Google Analytics 4 (Free)
   https://analytics.google.com/

```python
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from anytime import StreamSpec
from anytime.cs import BernoulliCS

def get_conversion_rate(property_id, credentials):
    '''Fetch conversion rate from GA4.'''

    client = BetaAnalyticsData.from_credentials(credentials)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="conversions")],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")]
    )

    response = client.run_report(request)

    # Process and analyze
    spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
    cs = BernoulliCS(spec)

    for row in response.rows:
        conversions = int(row.metric_values[0].value)
        total_visitors = 1000  # Would also fetch this
        cs.extend([1]*conversions + [0]*(total_visitors-conversions))

    iv = cs.interval()
    print(f"Conversion rate: {iv.estimate:.1%}")
    print(f"95% CI: ({iv.lo:.1%}, {iv.hi:.1%})")
```

2. Plausible Analytics (Privacy-friendly, free tier)
   https://plausible.io/

3. Matomo (Open source, self-hosted)
   https://matomo.org/

KEY METRICS TO TRACK:
----------------------
• Daily active users (DAU)
• Bounce rate
• Conversion rate
• Session duration
• Page views per session
• Traffic sources

IMPORTANT:
-----------
User privacy is increasingly important.
Consider privacy-first analytics:
• No personal data collection
• Anonymous tracking
• GDPR/CCPA compliance
    """)

def main():
    print("=" * 70)
    print("📊 Website Traffic Analytics")
    print("=" * 70)

    print("""
Analyze website traffic with anytime-valid confidence sequences.

Perfect for:
  • Bloggers and content creators
  • E-commerce store owners
  • Marketers running campaigns
  • Anyone with a website!

EXAMPLES:
  1. Daily visitor tracking
  2. Bounce rate monitoring
  3. Conversion rate analysis
  4. Real analytics integration

Note: Demo uses simulated data.
    """)

    demo_visitor_tracking()
    demo_bounce_rate()
    demo_conversion_rate()
    demo_real_analytics()

    print("\n" + "=" * 70)
    print("✅ SUMMARY")
    print("=" * 70)
    print("""
WHAT YOU LEARNED:
  ✓ Visitor tracking with confidence intervals
  ✓ Bounce rate analysis
  ✓ Conversion rate comparison
  ✓ How to integrate with analytics tools

NEXT STEPS:
  • Example 18: Stock prices
  • Example 20: Sports statistics
  • Example 23: Social media

DATA SOURCES:
  • Google Analytics 4: https://analytics.google.com/
  • Plausible: https://plausible.io/
  • Matomo: https://matomo.org/

Remember: Traffic varies naturally!
Confidence intervals help distinguish real changes from noise.
    """)

if __name__ == "__main__":
    main()
