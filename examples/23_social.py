#!/usr/bin/env python3
"""
23_social.py - Social Media Metrics Analysis

BEGINNER-FRIENDLY!

Track social media performance with anytime-valid confidence.
Perfect for influencers, marketers, and content creators.

WHAT YOU'LL LEARN:
- Engagement rate tracking
- Follower growth analysis
- Content performance comparison
- Detecting viral posts

TIME: 10 minutes
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS, BernoulliCS
import random

def demo_engagement_rate():
    """Track post engagement rates."""
    print("\n" + "=" * 70)
    print("📱 ENGAGEMENT RATE TRACKING")
    print("=" * 70)

    print("""
SCENARIO: Instagram post engagement rates

  Engagement rate = (likes + comments) / followers

  Good engagement: 3-5%
  Great: 5-10%
  Viral: 10%+

  Track with confidence to know if performance is truly improving!
    """)

    # Simulate 50 posts with varying engagement
    random.seed(42)
    engagements = []

    for _ in range(50):
        # True engagement rate varies by post
        # Quality content: higher engagement
        quality = random.random()
        if quality > 0.8:
            rate = random.gauss(0.08, 0.01)  # Great post
        elif quality > 0.5:
            rate = random.gauss(0.04, 0.01)  # Good post
        else:
            rate = random.gauss(0.02, 0.005)  # Average post

        rate = max(0, min(1, rate))
        engagements.append(rate)

    # Track with confidence sequence
    spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Post':>6} | {'Engagement':>12} | {'Avg':>10} | {'Status':>12}")
    print("-" * 70)

    for post, rate in enumerate(engagements, start=1):
        cs.update(rate)

        # Show every 10 posts
        if post % 10 == 0:
            iv = cs.interval()

            if iv.estimate > 0.05:
                status = "🔥 Viral!"
            elif iv.estimate > 0.03:
                status = "✓ Great"
            else:
                status = "Normal"

            print(f"{post:6d} | {rate:11.2%} | {iv.estimate:9.2%} | {status:>12}")

    iv = cs.interval()
    print("\n" + "=" * 70)
    print("50-POST SUMMARY")
    print("=" * 70)
    print(f"\nAverage engagement: {iv.estimate:.2%}")
    print(f"95% CI: ({iv.lo:.2%}, {iv.hi:.2%})")

def demo_content_comparison():
    """Compare performance of different content types."""
    print("\n" + "=" * 70)
    print("🎨 CONTENT TYPE COMPARISON")
    print("=" * 70)

    print("""
Which content performs best?

  Types to test:
    • Photos
    • Videos/Reels
    • Stories
    • Carousels

  Use confidence intervals to find the winner!
    """)

    content_types = {
        'Photos': 0.04,
        'Videos': 0.07,
        'Stories': 0.05,
        'Carousels': 0.03
    }

    results = {}

    for content, true_rate in content_types.items():
        spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
        cs = EmpiricalBernsteinCS(spec)

        random.seed(hash(content))
        # 20 posts of each type
        for _ in range(20):
            rate = random.gauss(true_rate, 0.01)
            rate = max(0, min(1, rate))
            cs.update(rate)

        iv = cs.interval()
        results[content] = iv

    print(f"\n{'Content':>12} | {'Engagement':>14} | {'Winner?':>10}")
    print("-" * 45)

    # Find best
    best = max(results.keys(), key=lambda k: results[k].estimate)

    for content, iv in results.items():
        winner = "🏆" if content == best else ""
        print(f"{content:>12} | {iv.estimate:13.2%} | {winner:>10}")

def demo_follower_growth():
    """Track follower growth over time."""
    print("\n" + "=" * 70)
    print("📈 FOLLOWER GROWTH TRACKING")
    print("=" * 70)

    print("""
Track your follower growth with confidence intervals.

  Are you growing consistently?
  Did a collaboration cause a spike?
  Is growth accelerating or slowing?
    """)

    # Simulate 60 days of growth
    random.seed(123)
    followers = []
    current = 10000

    for day in range(60):
        # Base growth: +50-100 followers/day
        growth = random.randint(50, 100)

        # Occasional viral post (spike)
        if random.random() < 0.05:
            growth += random.randint(200, 500)

        current += growth
        followers.append(current)

    # Calculate daily growth rates
    growth_rates = [followers[i] - followers[i-1] for i in range(1, len(followers))]

    spec = StreamSpec(alpha=0.05, support=(0, 10000), kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Day':>6} | {'Followers':>10} | {'Growth':>10} | {'Status':>12}")
    print("-" * 70)

    for day, (total, growth) in enumerate(zip(followers[::10], growth_rates[::10]), start=1):
        cs.update(growth)

        iv = cs.interval()
        day *= 10

        if growth > iv.hi:
            status = "🚀 Spike!"
        else:
            status = "✓ Normal"

        print(f"{day:6d} | {total:10,d} | {growth:10,d} | {status:>12}")

    iv = cs.interval()
    print("\n" + "=" * 70)
    print("GROWTH SUMMARY")
    print("=" * 70)
    print(f"\nDaily growth: {iv.estimate:,.0f} followers/day")
    print(f"95% CI: ({iv.lo:,.0f}, {iv.hi:,.0f})")
    print(f"\nProjected monthly growth: {iv.estimate * 30:,.0f}")

def demo_real_social_data():
    """Show how to get real social media data."""
    print("\n" + "=" * 70)
    print("🌐 REAL SOCIAL MEDIA DATA")
    print("=" * 70)

    print("""
To get REAL social media data, use these APIs:

INSTAGRAM:
-----------
• Instagram Graph API (Meta Business account required)
  https://developers.facebook.com/docs/instagram-api/

```python
import requests

def get_instagram_insights(access_token, business_id):
    '''Get engagement metrics from Instagram.'''

    url = f"https://graph.facebook.com/v18.0/{business_id}/insights"
    params = {
        "metric": "engagement,impressions,reach",
        "period": "day",
        "access_token": access_token
    }

    response = requests.get(url, params=params)
    return response.json()
```

TWITTER/X:
----------
• Twitter API v2 (Paid tier required)
  https://developer.twitter.com/en/docs/twitter-api

TIKTOK:
------
• TikTok API (Limited access)
  https://developers.tiktok.com/

LINKEDIN:
---------
• LinkedIn Marketing API (Business account)
  https://learn.microsoft.com/en-us/linkedin/marketing/

ALTERNATIVES (No API needed):
------------------------------

1. Manual tracking spreadsheets
2. Screenshot + manual data entry
3. Third-party analytics tools:
   - Hootsuite Analytics
   - Sprout Social
   - Buffer Analyze

IMPORTANT NOTE:
----------------
Social media platforms increasingly restrict API access.
Many features now require business verification or payment.
Consider manual tracking for personal accounts!

METRICS TO TRACK:
-----------------
• Engagement rate
• Follower growth
• Post impressions
• Profile visits
• Website clicks
• Shares/saves
    """)

def main():
    print("=" * 70)
    print("📱 Social Media Metrics Analysis")
    print("=" * 70)

    print("""
Track social media performance with anytime-valid confidence.

Perfect for:
  • Influencers and content creators
  • Social media managers
  • Brand marketing teams
  • Anyone growing their presence!

EXAMPLES:
  1. Engagement rate tracking
  2. Content type comparison
  3. Follower growth analysis
  4. Real API integration

Note: Demo uses simulated data.
    """)

    demo_engagement_rate()
    demo_content_comparison()
    demo_follower_growth()
    demo_real_social_data()

    print("\n" + "=" * 70)
    print("✅ SUMMARY")
    print("=" * 70)
    print("""
WHAT YOU LEARNED:
  ✓ Engagement rate tracking with confidence
  ✓ Content performance comparison
  ✓ Follower growth analysis
  ✓ Social media API options

KEY INSIGHT:
  Social metrics fluctuate wildly!
  Confidence intervals help identify true improvements.

NEXT STEPS:
  • Example 22: Website traffic
  • Example 18: Stock prices
  • Example 24: Gaming analytics

DATA SOURCES:
  • Instagram: https://developers.facebook.com/docs/instagram-api/
  • Twitter: https://developer.twitter.com/en/docs/twitter-api
  • Manual tracking: Spreadsheets work great!

Remember: Consistency matters more than viral hits!
    """)

if __name__ == "__main__":
    main()
