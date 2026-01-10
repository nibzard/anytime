#!/usr/bin/env python3
"""
27_habits.py - Habit Tracking and Goal Achievement

BEGINNER-FRIENDLY!

Track your habits and goals with anytime-valid confidence sequences.
Perfect for personal development, health tracking, and productivity.

WHAT YOU'LL LEARN:
- Daily habit consistency tracking
- Goal progress monitoring
- Comparing habit strategies
- Building lasting habits

TIME: 10 minutes
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS, BernoulliCS
import random

def demo_habit_tracking():
    """Track daily habit completion."""
    print("\n" + "=" * 70)
    print("✅ HABIT TRACKING")
    print("=" * 70)

    print("""
SCENARIO: Tracking daily exercise habit

  Goal: Exercise 30 minutes daily

  Questions:
    • What's my true consistency rate?
    • Am I improving over time?
    • When can I claim this habit is "built"?

  Anytime-valid advantage:
    ✓ Check progress daily
    ✓ Valid confidence intervals anytime
    ✓ Know when habit is truly established
    """)

    # Simulate 60 days of habit tracking
    # True rate starts at 60%, improves to 85%
    random.seed(42)
    days = []
    for day in range(60):
        # Improvement over time
        base_rate = 0.60 + (day / 60) * 0.25
        done = 1 if random.random() < base_rate else 0
        days.append(done)

    # Track with confidence
    spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
    cs = BernoulliCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Day':>6} | {'Done':>6} | {'Rate':>8} | {'95% CI':>14} | {'Status':>12}")
    print("-" * 70)

    for day, done in enumerate(days, start=1):
        cs.update(done)

        # Report every 10 days
        if day % 10 == 0:
            iv = cs.interval()

            # Check consistency
            if iv.lo > 0.80:
                status = "🔥 Built!"
            elif iv.lo > 0.70:
                status = "✓ Strong"
            elif iv.lo > 0.50:
                status = "→ Building"
            else:
                status = "⚠️  Struggling"

            print(f"{day:6d} | {day and sum(days[:day])/day:5.0%} | {iv.estimate:7.1%} | "
                  f"({iv.lo:.1%}, {iv.hi:.1%}) | {status:>12}")

    iv = cs.interval()
    print("\n" + "=" * 70)
    print("HABIT SUMMARY")
    print("=" * 70)
    print(f"\n60-day consistency: {iv.estimate:.1%}")
    print(f"95% CI: ({iv.lo:.1%}, {iv.hi:.1%})")

    total_days = sum(days)
    print(f"\nTotal successful days: {total_days}/60")

    if iv.lo > 0.75:
        print("\n🎉 Habit is strong! Lower bound above 75%")
    elif iv.lo > 0.50:
        print("\n👍 Making progress, keep going!")
    else:
        print("\n💪 Still building - consistency is key")

def demo_goal_progress():
    """Track progress toward a numeric goal."""
    print("\n" + "=" * 70)
    print("🎯 GOAL PROGRESS TRACKING")
    print("=" * 70)

    print("""
SCENARIO: Reading 24 books in a year

  Goal: 24 books
  Time: 365 days
  Pacing: 2 books per month

  Questions:
    • Am I on track?
    • Will I reach my goal?
    • When will I finish?
    """)

    # Simulate reading progress
    random.seed(789)
    books_read = []
    current = 0

    # Variable pace - some months faster
    for month in range(12):
        # Read 1-3 books per month
        books_this_month = random.randint(1, 3)
        current += books_this_month
        books_read.append(current)

    # Track reading rate
    spec = StreamSpec(alpha=0.05, support=(0, 30), kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Month':>8} | {'Books':>8} | {'Rate':>8} | {'Projected':>12} | {'On Track':>10}")
    print("-" * 70)

    for month, total in enumerate(books_read, start=1):
        # Add as individual data points
        if month == 1:
            books = total
        else:
            books = total - books_read[month - 2]

        for _ in range(books):
            cs.update(1)  # Each book counts

        # Calculate monthly rate
        iv = cs.interval()
        monthly_rate = iv.estimate * 12
        projected = iv.estimate

        # Expected pace
        expected = month * 2
        on_track = total >= expected

        track_status = "✓ Yes" if on_track else "⚠️ Behind"

        print(f"{month:8d} | {total:8d} | {iv.estimate*12:6.1f}/yr | {projected:6.0f}/yr | {track_status:>10}")

    iv = cs.interval()
    final_total = books_read[-1]

    print("\n" + "=" * 70)
    print("GOAL SUMMARY")
    print("=" * 70)
    print(f"\nBooks read: {final_total}/24")
    print(f"Reading rate: {iv.estimate*12:.1f} books/year")
    print(f"95% CI: ({iv.lo*12:.1f}, {iv.hi*12:.1f})")

    if iv.lo >= 24:
        print("\n🏆 Goal achieved!")
    elif iv.estimate >= 24:
        print("\n✓ On track to reach goal!")
    else:
        print("\n📚 Behind pace - need to read more!")

def demo_streak_tracking():
    """Track streaks and consistency."""
    print("\n" + "=" * 70)
    print("🔥 STREAK TRACKING")
    print("=" * 70)

    print("""
SCENARIO: Tracking a daily meditation streak

  Questions:
    • What's my longest streak?
    • What's my true consistency rate?
    • When did streaks break and why?

  Use confidence intervals to understand variability!
    """)

    # Simulate 90 days of meditation
    random.seed(456)
    days = []

    # True consistency: 75%
    for _ in range(90):
        done = 1 if random.random() < 0.75 else 0
        days.append(done)

    # Track current streak
    current_streak = 0
    longest_streak = 0
    streaks = []

    for day in days:
        if day == 1:
            current_streak += 1
        else:
            if current_streak > 0:
                streaks.append(current_streak)
            current_streak = 0

        longest_streak = max(longest_streak, current_streak)

    if current_streak > 0:
        streaks.append(current_streak)

    # Track overall consistency
    spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
    cs = BernoulliCS(spec)

    for day in days:
        cs.update(day)

    iv = cs.interval()

    print(f"\n90-day period:")
    print(f"  Total days completed: {sum(days)}")
    print(f"  Consistency rate: {iv.estimate:.1%}")
    print(f"  95% CI: ({iv.lo:.1%}, {iv.hi:.1%})")

    print(f"\nStreaks:")
    print(f"  Number of streaks: {len(streaks)}")
    print(f"  Longest streak: {max(streaks)} days")
    print(f"  Average streak: {sum(streaks)/len(streaks):.1f} days")

    # Find streak patterns
    if len(streaks) >= 3:
        recent = streaks[-3:]
        if all(s >= 7 for s in recent):
            print(f"\n🔥 Hot streak! Last 3 streaks: {recent}")

def demo_habit_comparison():
    """Compare different habit strategies."""
    print("\n" + "=" * 70)
    print("🧪 HABIT STRATEGY COMPARISON")
    print("=" * 70)

    print("""
SCENARIO: Comparing three habit strategies

  Strategy A: Cue-based (trigger → action)
  Strategy B: Time-based (same time daily)
  Strategy C: Reward-based (treat yourself)

  Which yields better consistency?
    """)

    strategies = {
        'Cue-based': 0.82,
        'Time-based': 0.71,
        'Reward-based': 0.65
    }

    results = {}

    for strategy, true_rate in strategies.items():
        spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
        cs = BernoulliCS(spec)

        random.seed(hash(strategy))
        # 60 days of each
        for _ in range(60):
            done = 1 if random.random() < true_rate else 0
            cs.update(done)

        iv = cs.interval()
        results[strategy] = iv

    print(f"\n{'Strategy':>15} | {'Consistency':>14} | {'95% CI':>16} | {'Rank':>6}")
    print("-" * 60)

    # Rank by consistency
    ranked = sorted(results.keys(), key=lambda k: results[k].estimate, reverse=True)

    for i, strategy in enumerate(ranked, start=1):
        iv = results[strategy]
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else ""
        print(f"{strategy:>15} | {iv.estimate:13.1%} | ({iv.lo:.1%}, {iv.hi:.1%}) | {i:3d} {medal}")

def demo_real_habit_tools():
    """Show real habit tracking tools and strategies."""
    print("\n" + "=" * 70)
    print("🌐 HABIT TRACKING TOOLS")
    print("=" * 70)

    print("""
DEDICATED HABIT APPS:
-----------------------

1. Streaks (Free)
   https://streaks.club/

   • Calendar-based tracking
   • Visual streak motivation
   • Simple and clean

2. Habitica (Free)
   https://habitica.com/

   • Gamified habit tracking
   • RPG-style progression
   • Social features

3. Way of Life (Free tier)
   https://wayoflife.com/

   • Color-coded calendar
   • Quick entry
   • Data visualization

4. TickTick (Free tier)
   https://www.ticktick.com/

   • Habit + todo list combo
   • Smart reminders
   • Progress tracking

SPREADSHEET TEMPLATES:
-------------------------

Google Sheets / Excel templates:

Habit Tracker Template:
```
Date       | Exercise | Read | Meditate | Water | Total
2024-01-01 |    X     |  X   |    X     |   X   | 4/5
2024-01-02 |    X     |  X   |          |   X   | 3/5
...
```

Monthly Summary:
```
Month      | Exercise | Read | Meditate | Water | Avg %
Jan 2024   |     25   |   28 |       22 |    30 |  84%
```

ANALYTICS WITH ANYTIME:
-------------------------

```python
from anytime import StreamSpec
from anytime.cs import BernoulliCS

class HabitAnalyzer:
    '''Analyze habit tracking data.'''

    def __init__(self, habit_name):
        spec = StreamSpec(
            alpha=0.05,
            support=(0, 1),
            kind="bounded",
            two_sided=True
        )
        self.cs = BernoulliCS(spec)
        self.name = habit_name

    def add_day(self, completed):
        '''Add a day's result.'''
        self.cs.update(1 if completed else 0)

    def get_consistency(self):
        '''Get consistency rate with CI.'''
        iv = self.cs.interval()
        return {
            'rate': iv.estimate,
            'ci_lower': iv.lo,
            'ci_upper': iv.hi,
            'days': iv.t
        }

# Usage
exercise = HabitAnalyzer("Morning Exercise")

# After each day
exercise.add_day(True)   # Completed
exercise.add_day(False)  # Missed
exercise.add_day(True)   # Completed

# Get analysis
stats = exercise.get_consistency()
print(f"Consistency: {stats['rate']:.1%}")
print(f"95% CI: ({stats['ci_lower']:.1%}, {stats['ci_upper']:.1%})")
```

HABIT-BUILDING PRINCIPLES:
---------------------------

1. Start Small
   • Begin with 5-10 minutes
   • Build the habit first
   • Increase duration later

2. Use Triggers
   • Link to existing habit
   • "After [current habit], I will [new habit]"
   • Example: "After breakfast, I will meditate"

3. Track Visibly
   • Calendar on wall
   • App notifications
   • Share with friends

4. Never Miss Twice
   • One miss is accident
   • Two misses is start of new habit
   • Get back on track immediately!

5. Celebrate Wins
   • Acknowledge streaks
   • Reward milestones
   • Share progress

POPULAR HABITS TO TRACK:
--------------------------

Health:
• Exercise daily
• Drink 8 glasses of water
• Sleep 7-8 hours
• Take vitamins
• Walk 10k steps

Productivity:
• Deep work 2+ hours
• Read 30 pages
• No social media during work
• Plan tomorrow today
• Review goals weekly

Learning:
• Practice language
• Code daily
• Watch tutorials
• Read research papers
• Take notes

Mindfulness:
• Meditate
• Journal
• Gratitude list
• No phone first 30min
• Breathing exercises

MEASURING SUCCESS:
-------------------

Habits are considered "built" when:
  • Lower bound of CI > 80% for 30+ days
  • Automatic (no willpower needed)
  • Feels wrong NOT to do it

Track with confidence intervals to know when you've truly
established a habit!

RECOMMENDED READING:
---------------------

• Atomic Habits by James Clear
• Tiny Habits by BJ Fogg
• The Power of Habit by Charles Duhigg

Remember: Consistency > Perfection
Track your habits, trust the process!
    """)

def main():
    print("=" * 70)
    print("✅ Habit Tracking and Goal Achievement")
    print("=" * 70)

    print("""
Track habits and goals with anytime-valid confidence.

Perfect for:
  • Personal development enthusiasts
  • New Year's resolution makers
  • Productivity seekers
  • Anyone building better habits!

EXAMPLES:
  1. Daily habit tracking
  2. Goal progress monitoring
  3. Streak analysis
  4. Strategy comparison
  5. Real habit tools

Note: Demo uses simulated data.
    """)

    demo_habit_tracking()
    demo_goal_progress()
    demo_streak_tracking()
    demo_habit_comparison()
    demo_real_habit_tools()

    print("\n" + "=" * 70)
    print("✅ SUMMARY")
    print("=" * 70)
    print("""
WHAT YOU LEARNED:
  ✓ Habit consistency tracking
  ✓ Goal progress monitoring
  ✓ Streak analysis
  ✓ Strategy comparison
  ✓ Real tools and templates

KEY INSIGHT:
  Habits take time to build!
  Confidence intervals show true progress.

NEXT STEPS:
  • Example 25: Survey analysis
  • Example 26: Learning tracking
  • Example 18: Stock prices

TOOLS:
  • Streaks: https://streaks.club/
  • Habitica: https://habitica.com/
  • Way of Life: https://wayoflife.com/

Remember: You don't rise to the level of your goals.
You fall to the level of your systems.

Build the system, track the data, achieve the goals!
    """)

if __name__ == "__main__":
    main()
