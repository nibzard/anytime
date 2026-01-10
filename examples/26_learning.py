#!/usr/bin/env python3
"""
26_learning.py - Learning Progress Tracking

BEGINNER-FRIENDLY!

Track your learning progress with anytime-valid confidence sequences.
Perfect for students, lifelong learners, and skill development.

WHAT YOU'LL LEARN:
- Test score tracking
- Study session effectiveness
- Skill improvement over time
- Comparing learning methods

TIME: 10 minutes
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS, BernoulliCS
import random

def demo_test_scores():
    """Track test scores over a semester."""
    print("\n" + "=" * 70)
    print("📚 TEST SCORE TRACKING")
    print("=" * 70)

    print("""
SCENARIO: Tracking test scores throughout a course

  Questions:
    • What's my true ability level?
    • Am I improving over time?
    • Was the final exam harder or easier?

  Anytime-valid advantage:
    ✓ Check after every test
    ✓ Valid confidence intervals anytime
    ✓ Detect real improvement vs luck
    """)

    # Simulate 10 tests over a semester
    random.seed(42)
    scores = []

    # Student starts at 75% and improves to 85%
    for test in range(10):
        improvement = test * 1.5
        base = 75 + improvement
        noise = random.gauss(0, 8)
        score = max(0, min(100, base + noise))
        scores.append(score)

    # Track with confidence
    spec = StreamSpec(alpha=0.05, support=(0, 100), kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Test':>6} | {'Score':>8} | {'Avg':>8} | {'95% CI':>14} | {'Grade':>8}")
    print("-" * 70)

    for test, score in enumerate(scores, start=1):
        cs.update(score)

        iv = cs.interval()

        # Letter grade
        if iv.estimate >= 90:
            grade = "A"
        elif iv.estimate >= 80:
            grade = "B"
        elif iv.estimate >= 70:
            grade = "C"
        elif iv.estimate >= 60:
            grade = "D"
        else:
            grade = "F"

        print(f"{test:6d} | {score:8.1f} | {iv.estimate:8.1f} | "
              f"({iv.lo:5.1f}, {iv.hi:5.1f}) | {grade:>8}")

    iv = cs.interval()
    print("\n" + "=" * 70)
    print("SEMESTER SUMMARY")
    print("=" * 70)
    print(f"\nFinal average: {iv.estimate:.1f}")
    print(f"95% CI: ({iv.lo:.1f}, {iv.hi:.1f})")
    print(f"Letter grade: {'A' if iv.estimate >= 90 else 'B' if iv.estimate >= 80 else 'C'}")

    # Check improvement
    first_half_avg = sum(scores[:5]) / 5
    second_half_avg = sum(scores[5:]) / 5

    if second_half_avg > first_half_avg + 5:
        print(f"\n✅ Significant improvement! ({second_half_avg:.1f} vs {first_half_avg:.1f})")

def demo_flashcard_accuracy():
    """Track flashcard learning accuracy."""
    print("\n" + "=" * 70)
    print("⚡ FLASHCARD LEARNING")
    print("=" * 70)

    print("""
SCENARIO: Using flashcards (Anki, Quizlet, etc.)

  Track accuracy over time to see:
    • Which cards I know well
    • Which need more practice
    • When I've mastered a deck

  Spaced repetition works better with data tracking!
    """)

    # Simulate learning a deck of 100 cards
    random.seed(789)

    # Start: 60% know the card
    # End: 95% know the card
    sessions = 10
    cards_per_session = 100

    spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
    cs = BernoulliCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Session':>10} | {'Accuracy':>12} | {'Known':>8} | {'Status':>12}")
    print("-" * 70)

    for session in range(1, sessions + 1):
        # Improvement curve
        base_rate = 0.60 + (session / sessions) * 0.35

        # Practice this session
        session_correct = 0
        for _ in range(cards_per_session):
            correct = 1 if random.random() < base_rate else 0
            session_correct += correct
            cs.update(correct)

        iv = cs.interval()

        # Check mastery
        if iv.lo > 0.90:
            status = "✓ Mastered!"
        elif iv.estimate > 0.80:
            status = "👍 Good"
        else:
            status = "Keep practicing"

        if session % 2 == 0:
            accuracy = session_correct / cards_per_session
            print(f"{session:10d} | {accuracy:11.1%} | {session_correct:8d} | {status:>12}")

    iv = cs.interval()
    print("\n" + "=" * 70)
    print("LEARNING SUMMARY")
    print("=" * 70)
    print(f"\nFinal accuracy: {iv.estimate:.1%}")
    print(f"95% CI: ({iv.lo:.1%}, {iv.hi:.1%})")

    if iv.lo > 0.90:
        print("\n🎉 Deck mastered!")

def demo_study_methods():
    """Compare different study methods."""
    print("\n" + "=" * 70)
    print("🧪 STUDY METHOD COMPARISON")
    print("=" * 70)

    print("""
SCENARIO: Comparing study methods

  Method A: Passive reading
  Method B: Active recall
  Method C: Spaced repetition

  Which yields better test scores?
    """)

    methods = {
        'Passive Reading': 72,
        'Active Recall': 85,
        'Spaced Repetition': 88
    }

    results = {}

    for method, true_score in methods.items():
        spec = StreamSpec(alpha=0.05, support=(0, 100), kind="bounded", two_sided=True)
        cs = EmpiricalBernsteinCS(spec)

        random.seed(hash(method))
        # 20 practice tests
        for _ in range(20):
            noise = random.gauss(0, 10)
            score = max(0, min(100, true_score + noise))
            cs.update(score)

        iv = cs.interval()
        results[method] = iv

    print(f"\n{'Method':>20} | {'Score':>8} | {'95% CI':>14} | {'Best?':>8}")
    print("-" * 60)

    best = max(results.keys(), key=lambda k: results[k].estimate)

    for method, iv in results.items():
        is_best = "🏆" if method == best else ""
        print(f"{method:>20} | {iv.estimate:7.1f} | ({iv.lo:5.1f}, {iv.hi:5.1f}) | {is_best:>8}")

def demo_real_learning_tools():
    """Show real learning tracking tools."""
    print("\n" + "=" * 70)
    print("🌐 LEARNING TRACKING TOOLS")
    print("=" * 70)

    print("""
TOOLS FOR TRACKING LEARNING:
-----------------------------

FLASHCARD APPS:
--------------

1. Anki (Free, Open Source)
   https://apps.ankiweb.net/

   Features:
   • Spaced repetition algorithm
   • Detailed statistics
   • Custom decks
   • Sync across devices

2. Quizlet (Free tier)
   https://quizlet.com/

   Features:
   • Pre-made flashcards
   • Various study modes
   • Progress tracking

3. Brainscape (Free tier)
   https://www.brainscape.com/

   Features:
   • Confidence-based repetition
   • Smart study schedule
   • Progress analytics

LEARNING PLATFORMS:
-------------------

1. Khan Academy (Free)
   https://www.khanacademy.org/

   • Track course progress
   • Practice exercises
   • Video lessons

2. Duolingo (Free)
   https://www.duolingo.com/

   • Language learning
   • Streak tracking
   • XP system

3. Coursera / edX
   https://www.coursera.org/
   https://www.edx.org/

   • Online courses
   • Quizzes and assignments
   • Certificates

HABIT TRACKERS:
---------------

1. Notion (Free tier)
   https://www.notion.so/

2. Evernote (Free tier)
   https://evernote.com/

3. Google Sheets (Free)
   https://www.google.com/sheets/

DIY TRACKING TEMPLATE:
----------------------

```python
from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS

class LearningTracker:
    '''Track your learning progress.'''

    def __init__(self, skill_name):
        self.spec = StreamSpec(
            alpha=0.05,
            support=(0, 100),
            kind="bounded",
            two_sided=True
        )
        self.cs = EmpiricalBernsteinCS(self.spec)
        self.skill_name = skill_name

    def add_session(self, score):
        '''Add a practice session score.'''
        self.cs.update(score)
        return self.get_progress()

    def get_progress(self):
        '''Get current progress with confidence.'''
        iv = self.cs.interval()
        return {
            'average': iv.estimate,
            'ci_lower': iv.lo,
            'ci_upper': iv.hi,
            'sessions': iv.t
        }

# Usage
tracker = LearningTracker("Python Programming")

# After each practice session
tracker.add_session(75)  # Got 75% on quiz
tracker.add_session(82)  # Got 82%
tracker.add_session(88)  # Got 88%

progress = tracker.get_progress()
print(f"Progress: {progress['average']:.1f}%")
print(f"95% CI: ({progress['ci_lower']:.1f}%, {progress['ci_upper']:.1f}%)")
```

METRICS TO TRACK:
-----------------

1. Test scores
   • Quizzes
   • Exams
   • Practice tests

2. Time spent
   • Study hours
   • Practice sessions
   • Active learning time

3. Retention rate
   • Flashcard accuracy
   • Review performance
   • Long-term memory

4. Project completion
   • Coding projects
   • Essays written
   • Problems solved

LEARNING PRINCIPLES:
--------------------

1. Spaced Repetition
   • Review at increasing intervals
   • Better long-term retention
   • Efficient use of time

2. Active Recall
   • Test yourself regularly
   • Better than re-reading
   • Strengthens memory

3. Interleaving
   • Mix different topics
   • Improves transfer
   • Prevents plateauing

4. Deliberate Practice
   • Focus on weaknesses
   • Get feedback
   • Push beyond comfort zone

Remember: Consistency beats intensity!
Track your progress to stay motivated.
    """)

def main():
    print("=" * 70)
    print("📚 Learning Progress Tracking")
    print("=" * 70)

    print("""
Track your learning with anytime-valid confidence sequences.

Perfect for:
  • Students tracking grades
  • Lifelong learners
  • Skill development
  • Anyone learning something new!

EXAMPLES:
  1. Test score tracking
  2. Flashcard accuracy
  3. Study method comparison
  4. Learning tools integration

Note: Demo uses simulated data.
    """)

    demo_test_scores()
    demo_flashcard_accuracy()
    demo_study_methods()
    demo_real_learning_tools()

    print("\n" + "=" * 70)
    print("✅ SUMMARY")
    print("=" * 70)
    print("""
WHAT YOU LEARNED:
  ✓ Test score analysis with confidence
  ✓ Flashcard accuracy tracking
  ✓ Study method comparison
  ✓ Real learning tools

KEY INSIGHT:
  Learning has plateaus and breakthroughs!
  Confidence intervals show real progress.

NEXT STEPS:
  • Example 20: Sports statistics
  • Example 24: Gaming stats
  • Example 27: Habit tracking

TOOLS:
  • Anki: https://apps.ankiweb.net/
  • Quizlet: https://quizlet.com/
  • Khan Academy: https://www.khanacademy.org/

Remember: Learning is a journey, not a destination!
Track progress to stay motivated.
    """)

if __name__ == "__main__":
    main()
