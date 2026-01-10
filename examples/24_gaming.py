#!/usr/bin/env python3
"""
24_gaming.py - Video Game Statistics Analysis

BEGINNER-FRIENDLY!

Analyze gaming performance with anytime-valid confidence sequences.
Perfect for gamers who want to track their stats scientifically.

WHAT YOU'LL LEARN:
- Win rate tracking
- K/D ratio analysis
- Performance over time
- Comparing weapons/characters

TIME: 10 minutes
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS, BernoulliCS
import random

def demo_win_rate():
    """Track win rate in competitive games."""
    print("\n" + "=" * 70)
    print("🎮 WIN RATE TRACKING")
    print("=" * 70)

    print("""
SCENARIO: Tracking competitive gaming win rate

  Games like League of Legends, Valorant, Overwatch, etc.

  Questions:
    • What's my true skill level (win rate)?
    • Am I improving over time?
    • Is this losing streak bad luck or am I playing worse?

  Anytime-valid advantage:
    ✓ Check stats after every match
    ✓ Valid confidence intervals anytime
    ✓ Detect real improvement vs variance
    """)

    # Simulate 100 matches with 52% win rate
    random.seed(42)
    wins = [1 if random.random() < 0.52 else 0 for _ in range(100)]

    spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
    cs = BernoulliCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Match':>8} | {'Wins':>8} | {'Total':>8} | {'Win Rate':>12} | {'95% CI':>16}")
    print("-" * 70)

    wins_count = 0

    for match, result in enumerate(wins, start=1):
        wins_count += result
        cs.update(result)

        # Report every 20 matches
        if match % 20 == 0:
            iv = cs.interval()
            wr = wins_count / match

            print(f"{match:8d} | {wins_count:8d} | {match:8d} | {wr:11.1%} | "
                  f"({iv.lo:.1%}, {iv.hi:.1%})")

    iv = cs.interval()
    print("\n" + "=" * 70)
    print("SEASON SUMMARY")
    print("=" * 70)
    print(f"\nFinal record: {wins_count}-{len(wins)-wins_count}")
    print(f"Win rate: {iv.estimate:.1%}")
    print(f"95% CI: ({iv.lo:.1%}, {iv.hi:.1%})")

    if iv.lo > 0.50:
        print("\n✅ You're statistically above average (>50% win rate)!")
    elif iv.hi < 0.50:
        print("\n⚠️  Below average - time to practice!")
    else:
        print("\n🤷 Around average - could be either way")

def demo kd_ratio():
    """Analyze Kill/Death ratio in FPS games."""
    print("\n" + "=" * 70)
    print("🔫 K/D RATIO ANALYSIS")
    print("=" * 70)

    print("""
SCENARIO: Tracking K/D ratio in FPS games

  Games: Call of Duty, Valorant, CS:GO, Apex Legends

  K/D = Kills / Deaths

  What's good?
    • K/D > 1.0: Above average
    • K/D > 1.5: Good player
    • K/D > 2.0: Excellent

  Track per match to see true skill level!
    """)

    # Simulate matches with varying performance
    random.seed(789)
    matches = []

    for _ in range(50):
        # True K/D is around 1.3
        kills = int(random.gauss(20, 8))
        deaths = int(random.gauss(15, 5))
        kills = max(0, kills)
        deaths = max(1, deaths)
        matches.append((kills, deaths))

    # Track K/D ratio
    # For ratio, we track kills and deaths separately
    total_kills = 0
    total_deaths = 0

    print("\n" + "-" * 70)
    print(f"{'Match':>8} | {'K':>6} | {'D':>6} | {'K/D':>8} | {'Cumul K/D':>10}")
    print("-" * 70)

    for match, (kills, deaths) in enumerate(matches, start=1):
        total_kills += kills
        total_deaths += deaths
        kd = kills / deaths
        cumulative_kd = total_kills / total_deaths

        if match % 10 == 0:
            print(f"{match:8d} | {kills:6d} | {deaths:6d} | {kd:7.2f} | {cumulative_kd:9.2f}")

    final_kd = total_kills / total_deaths
    print("\n" + "=" * 70)
    print("SESSION SUMMARY")
    print("=" * 70)
    print(f"\nTotal kills: {total_kills}")
    print(f"Total deaths: {total_deaths}")
    print(f"K/D ratio: {final_kd:.2f}")

    if final_kd > 2.0:
        print("🏆 Excellent performance!")
    elif final_kd > 1.5:
        print("✓ Good player!")
    elif final_kd > 1.0:
        print("👍 Above average!")
    else:
        print("💪 Room for improvement!")

def demo_rank_progression():
    """Track rank progression over time."""
    print("\n" + "=" * 70)
    print("📈 RANK PROGRESSION")
    print("=" * 70)

    print("""
Track your climb through ranked play.

  Questions:
    • How fast am I climbing?
    • Am I plateauing?
    • When will I reach the next rank?

  Use confidence intervals to predict!
    """)

    # Simulate rank points (RR, LP, etc.)
    random.seed(456)
    points = []
    current = 100

    for _ in range(50):
        # Win: +20-25 points
        # Loss: -15-20 points
        if random.random() < 0.52:
            gain = random.randint(20, 25)
            current += gain
        else:
            loss = random.randint(15, 20)
            current -= loss
        points.append(current)

    # Track with confidence
    spec = StreamSpec(alpha=0.05, support=(0, 5000), kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Game':>8} | {'Points':>10} | {'Avg':>10} | {'Trend':>12}")
    print("-" * 70)

    for game, pts in enumerate(points, start=1):
        cs.update(pts)

        if game % 10 == 0:
            iv = cs.interval()

            # Check trend
            if iv.estimate > points[0]:
                trend = "📈 Climbing!"
            elif iv.estimate < points[0]:
                trend = "📉 Falling"
            else:
                trend = "→ Stable"

            print(f"{game:8d} | {pts:10,d} | {iv.estimate:10,.0f} | {trend:>12}")

    start_points = points[0]
    end_points = points[-1]
    gained = end_points - start_points

    print("\n" + "=" * 70)
    print("PROGRESSION SUMMARY")
    print("=" * 70)
    print(f"\nStarting: {start_points:,} points")
    print(f"Current: {end_points:,} points")
    print(f"Net gain: {gained:+,} points")

    if gained > 0:
        print("✅ Positive progression!")
    else:
        print("⚠️  Down on luck - keep grinding!")

def demo_real_gaming_stats():
    """Show how to get real gaming statistics."""
    print("\n" + "=" * 70)
    print("🌐 REAL GAMING STATISTICS")
    print("=" * 70)

    print("""
To get REAL gaming statistics, use these platforms:

TRACKING SITES:
----------------

1. OP.GG (League of Legends)
   https://op.gg/

2. Tracker Network (Multiple games)
   https://tracker.gg/

   Supports:
   • Valorant
   • Apex Legends
   • Fortnite
   • Call of Duty
   • And more!

3. Steam (PC games)
   https://steamcommunity.com/

4. Destiny Tracker
   https://destinytracker.com/

5. Halo Tracker
   https://halotracker.com/

API ACCESS:
------------
Some sites offer APIs for data retrieval:

```python
import requests
from anytime import StreamSpec
from anytime.cs import BernoulliCS

def get_valorant_stats(player_name):
    '''Fetch Valorant stats from tracker.gg.'''

    # Note: Check site's ToS before scraping
    url = f"https://tracker.gg/valorant/profile/riot/{player_name}"

    # Would need web scraping or official API
    # This is pseudocode for illustration
    response = requests.get(url)

    # Parse match history
    matches = parse_matches(response)

    spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
    cs = BernoulliCS(spec)

    for match in matches:
        result = 1 if match['won'] else 0
        cs.update(result)

    iv = cs.interval()
    print(f"Win rate: {iv.estimate:.1%}")
    print(f"95% CI: ({iv.lo:.1%}, {iv.hi:.1%})")

    return iv
```

POPULAR GAMES TO TRACK:
----------------------
• League of Legends
• Valorant
• Counter-Strike (CS:GO/CS2)
• Apex Legends
• Fortnite
• Overwatch 2
• Call of Duty (Warzone, MW2)
• Destiny 2

MANUAL TRACKING:
----------------
For games without automated tracking:

1. Use spreadsheet
2. Record after each session:
   - Wins/Losses
   - K/D
   - Rank/Division
   - Notes on what worked

3. Weekly review:
   - Calculate overall stats
   - Identify trends
   - Set improvement goals

IMPORTANT:
-----------
• Gaming stats fluctuate - variance is real!
• Confidence intervals help identify true skill
• Focus on improvement, not just numbers
• Take breaks to avoid burnout

COMPETITIVE RANKS:
------------------
Different games use different systems:

• LoL: Iron → Bronze → Silver → Gold → Plat → Diamond → Master → GM → Challenger
• Valorant: Iron → Bronze → Silver → Gold → Plat → Diamond → Ascendant → Immortal → Radiant
• CS:GO: Silver → Gold Nova → Master Guardian → Legendary → Eagle → Supreme → Global

Track your journey through ranks!
    """)

def main():
    print("=" * 70)
    print("🎮 Gaming Statistics Analysis")
    print("=" * 70)

    print("""
Analyze gaming performance with anytime-valid confidence.

Perfect for:
  • Competitive gamers
  • Esports enthusiasts
  • Anyone wanting to improve!
  • Content creators streaming gameplay

EXAMPLES:
  1. Win rate tracking
  2. K/D ratio analysis
  3. Rank progression
  4. Real gaming stats sources

Note: Demo uses simulated data.
    """)

    demo_win_rate()
    demo kd_ratio()
    demo_rank_progression()
    demo_real_gaming_stats()

    print("\n" + "=" * 70)
    print("✅ SUMMARY")
    print("=" * 70)
    print("""
WHAT YOU LEARNED:
  ✓ Win rate analysis with confidence
  ✓ K/D ratio tracking
  ✓ Rank progression monitoring
  ✓ Real gaming stat sources

KEY INSIGHT:
  Gaming has high variance!
  Confidence intervals distinguish skill from luck.

NEXT STEPS:
  • Example 20: Sports statistics
  • Example 21: Cryptocurrency
  • Example 25: Product reviews

DATA SOURCES:
  • Tracker.gg: https://tracker.gg/
  • OP.GG: https://op.gg/
  • Steam: https://steamcommunity.com/

Remember: Improvement matters more than current stats!
    """)

if __name__ == "__main__":
    main()
