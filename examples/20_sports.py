#!/usr/bin/env python3
"""
20_sports.py - Sports Statistics with Confidence Intervals

BEGINNER-FRIENDLY!

Analyze sports performance with anytime-valid confidence sequences.
Perfect for sports fans who want to go beyond basic averages.

WHAT YOU'LL LEARN:
- Batting averages with confidence
- Free throw percentages
- Performance tracking over a season
- Comparing players statistically

TIME: 10 minutes
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS, BernoulliCS
import random

def demo_batting_average():
    """Analyze baseball batting averages."""
    print("\n" + "=" * 70)
    print("⚾ BASEBALL: Batting Average Analysis")
    print("=" * 70)

    print("""
SCENARIO: Tracking a batter's performance over the season

  Traditional: "He's batting .275"
  With confidence: "He's batting .275, and we're 95% confident
                    his true ability is between .260 and .290"

  Anytime-valid advantage:
    ✓ Update after every game
    ✓ Valid even if you check daily
    ✓ Compare players fairly
    """)

    # Simulate a season (162 games)
    random.seed(42)
    at_bats = 0
    hits = 0

    # True batting average is .275
    true_avg = 0.275

    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True,
        name="batting_average"
    )

    cs = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Game':>6} | {'AB':>4} | {'H':>3} | {'Avg':>6} | {'95% CI':>16} | {'Status':>12}")
    print("-" * 70)

    for game in range(1, 163):
        # 3-5 at-bats per game
        game_abs = random.randint(3, 5)

        for _ in range(game_abs):
            at_bats += 1
            hit = 1 if random.random() < true_avg else 0
            hits += hit
            cs.update(hit)

        # Report every 27 games (approx once a month)
        if game % 27 == 0:
            iv = cs.interval()
            avg = iv.estimate

            # Check if in "slump" or "hot streak"
            if avg < 0.250:
                status = "Slump"
            elif avg > 0.300:
                status = "Hot!"
            else:
                status = "Normal"

            print(f"{game:6d} | {at_bats:4d} | {hits:3d} | {avg:.3f} | "
                  f"({iv.lo:.3f}, {iv.hi:.3f}) | {status:>12}")

    # Final stats
    iv = cs.interval()
    print("\n" + "=" * 70)
    print("📊 SEASON SUMMARY")
    print("=" * 70)
    print(f"\nFinal: {hits}/{at_bats} = {iv.estimate:.3f}")
    print(f"95% CI: ({iv.lo:.3f}, {iv.hi:.3f})")
    print(f"\nWe're 95% confident the batter's true skill level is in this range!")

def demo_free_throws():
    """Analyze basketball free throw percentages."""
    print("\n" + "=" * 70)
    print("🏀 BASKETBALL: Free Throw Analysis")
    print("=" * 70)

    print("""
SCENARIO: Comparing two players' free throw percentages

  Player A: Known good shooter (~85%)
  Player B: Struggling (~70%)

  With confidence intervals, we can:
    • Say when we're confident one is better
    • Track improvement over time
    • Detect real changes in performance
    """)

    # Compare two players
    players = {
        'Player A': 0.85,
        'Player B': 0.70
    }

    results = {}

    for player, true_rate in players.items():
        spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
        cs = EmpiricalBernsteinCS(spec)

        random.seed(hash(player))
        attempts = 0
        made = 0

        # Simulate 100 free throws
        for _ in range(100):
            attempts += 1
            shot = 1 if random.random() < true_rate else 0
            made += shot
            cs.update(shot)

        iv = cs.interval()
        results[player] = {
            'made': made,
            'attempts': attempts,
            'rate': iv.estimate,
            'ci_lower': iv.lo,
            'ci_upper': iv.hi
        }

    print(f"{'Player':>10} | {'Made':>6} | {'Rate':>8} | {'95% CI':>14}")
    print("-" * 50)

    for player, stats in results.items():
        print(f"{player:>10} | {stats['made']:3d}/{stats['attempts']:<3} | "
              f"{stats['rate']:7.1%} | ({stats['ci_lower']:.1%}, {stats['ci_upper']:.1%})")

    # Check if confident A is better
    a_lower = results['Player A']['ci_lower']
    b_upper = results['Player B']['ci_upper']

    if a_lower > b_upper:
        print(f"\n✅ We're 95% confident Player A is better!")
    else:
        print(f"\n⚠️  CI overlap - need more data to be certain")

def demo_real_sports_data():
    """Show how to get real sports data."""
    print("\n" + "=" * 70)
    print("🌐 REAL SPORTS DATA")
    print("=" * 70)

    print("""
To get REAL sports data, use these APIs:

FREE DATA SOURCES:
------------------

1. Sports Reference (scraping)
   https://www.sports-reference.com/
   • MLB: https://www.baseball-reference.com/
   • NBA: https://www.basketball-reference.com/
   • NFL: https://www.pro-football-reference.com/

2. API-NBA (Free tier)
   https://api-nba-v1.p.rapidapi.com/
   pip install rapidapi-python

3. TheSportsDB (Free)
   https://www.thesportsdb.com/api.php
   pip install python-thesportsdb

EXAMPLE: Fetching MLB stats
----------------------------

```python
import requests
from bs4 import BeautifulSoup
from anytime import StreamSpec
from anytime.cs import BernoulliCS

def get_mlb_stats(player_url):
    '''Scrape batting stats from Baseball Reference.'''

    response = requests.get(player_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find batting table
    table = soup.find('table', {'id': 'batting_standard'})

    # Parse last 30 games
    recent_stats = []
    rows = table.find_all('tr')[1:31]  # Last 30 games

    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 0:
            ab = int(cols[0].text)
            h = int(cols[1].text)
            recent_stats.extend([1]*h + [0]*(ab-h))

    return recent_stats

# Analyze player
stats = get_mlb_stats("https://www.baseball-reference.com/players/a/aaronha01.shtml")

spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
cs = BernoulliCS(spec)

for outcome in stats:
    cs.update(outcome)

iv = cs.interval()
print(f"Batting average: {iv.estimate:.3f}")
print(f"95% CI: ({iv.lo:.3f}, {iv.hi:.3f})")
```

POPULAR STATISTICS TO TRACK:
---------------------------
BASEBALL:
  • Batting average
  • On-base percentage
  • Slugging percentage
  • Earned run average (ERA)

BASKETBALL:
  • Field goal percentage
  • Free throw percentage
  • Three-point percentage
  • Points per game

FOOTBALL:
  • Completion percentage
  • Field goal percentage
  • Yards per carry
  • Quarterback rating
    """)

def main():
    print("=" * 70)
    print("⚽ Sports Statistics Analysis")
    print("=" * 70)

    print("""
Analyze sports performance with anytime-valid confidence intervals.

Perfect for:
  • Sports fans who want deeper insights
  • Fantasy sports players
  • Coaches tracking performance
  • Anyone who loves sports and data

EXAMPLES:
  1. Baseball batting averages
  2. Basketball free throws
  3. Real sports data sources

Note: Demo uses simulated data for illustration.
    """)

    demo_batting_average()
    demo_free_throws()
    demo_real_sports_data()

    print("\n" + "=" * 70)
    print("✅ SUMMARY")
    print("=" * 70)
    print("""
WHAT YOU LEARNED:
  ✓ Batting average analysis with confidence
  ✓ Free throw percentage comparison
  ✓ How to fetch real sports data

KEY INSIGHT:
  Confidence intervals tell you if differences are real
  or just due to chance!

NEXT STEPS:
  • Example 18: Stock prices
  • Example 19: Weather data
  • Example 21: Cryptocurrency

DATA SOURCES:
  • Baseball Reference: https://www.baseball-reference.com/
  • Basketball Reference: https://www.basketball-reference.com/
  • TheSportsDB API: https://www.thesportsdb.com/

Fun fact: Many "hot streaks" are just normal variation!
Confidence intervals help distinguish real changes from luck.
    """)

if __name__ == "__main__":
    main()
