#!/usr/bin/env python3
"""
25_surveys.py - Survey and Poll Analysis

BEGINNER-FRIENDLY!

Analyze survey responses with anytime-valid confidence sequences.
Perfect for researchers, marketers, and anyone running surveys.

WHAT YOU'LL LEARN:
- Analyzing Likert scale responses
- Tracking approval ratings
- Comparing survey responses
- Detecting sentiment changes

TIME: 10 minutes
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS
import random

def demo_approval_rating():
    """Track approval ratings (like political polls)."""
    print("\n" + "=" * 70)
    print("📊 APPROVAL RATING TRACKING")
    print("=" * 70)

    print("""
SCENARIO: Tracking approval ratings over time

  Like political polls, customer satisfaction, NPS scores

  Traditional: "52% approve"
  With confidence: "52% ± 3%, we're 95% confident true rating is 49-55%"

  Anytime-valid advantage:
    ✓ Update after every response
    ✓ Valid even with frequent polling
    ✓ Detect real changes vs noise
    """)

    # Simulate daily polling (30 days)
    random.seed(42)
    approvals = []

    # True approval is 52%, with random fluctuation
    for day in range(30):
        daily_sample = [1 if random.random() < 0.52 else 0 for _ in range(1000)]
        approval_rate = sum(daily_sample) / 1000
        approvals.append(approval_rate)

    # Track with confidence
    spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Day':>6} | {'Approve':>10} | {'Avg':>10} | {'95% CI':>16} | {'Trend':>10}")
    print("-" * 70)

    for day, rate in enumerate(approvals, start=1):
        # Add each response individually
        for _ in range(1000):
            response = 1 if random.random() < rate else 0
            cs.update(response)

        if day % 5 == 0:
            iv = cs.interval()

            if iv.estimate > 0.55:
                trend = "📈 High"
            elif iv.estimate < 0.45:
                trend = "📉 Low"
            else:
                trend = "→ Stable"

            print(f"{day:6d} | {rate:9.1%} | {iv.estimate:9.1%} | "
                  f"({iv.lo:.1%}, {iv.hi:.1%}) | {trend:>10}")

    iv = cs.interval()
    print("\n" + "=" * 70)
    print("POLLING SUMMARY")
    print("=" * 70)
    print(f"\nFinal approval: {iv.estimate:.1%}")
    print(f"95% CI: ({iv.lo:.1%}, {iv.hi:.1%})")
    print(f"Margin of error: ±{(iv.hi - iv.lo)/2:.1%}")

def demo_likert_scale():
    """Analyze Likert scale survey responses."""
    print("\n" + "=" * 70)
    print("📋 LIKERT SCALE ANALYSIS")
    print("=" * 70)

    print("""
SCENARIO: Customer satisfaction survey (1-5 scale)

  1 = Very Dissatisfied
  2 = Dissatisfied
  3 = Neutral
  4 = Satisfied
  5 = Very Satisfied

  Questions:
    • What's the true average satisfaction?
    • Are customers happy (avg > 4)?
    • How confident are we in this rating?
    """)

    # Simulate 500 survey responses
    random.seed(789)
    responses = []

    # True average is around 3.8
    for _ in range(500):
        # Weighted random towards higher scores
        r = random.random()
        if r < 0.10:
            score = 1
        elif r < 0.20:
            score = 2
        elif r < 0.40:
            score = 3
        elif r < 0.70:
            score = 4
        else:
            score = 5
        responses.append(score)

    # Track with confidence
    spec = StreamSpec(alpha=0.05, support=(1, 5), kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    for response in responses:
        cs.update(response)

    iv = cs.interval()

    print(f"\nResponses collected: {iv.t}")
    print(f"Average rating: {iv.estimate:.2f} / 5")
    print(f"95% CI: ({iv.lo:.2f}, {iv.hi:.2f})")

    # Calculate percentages
    dist = {i: responses.count(i) / len(responses) for i in range(1, 6)}

    print(f"\nDistribution:")
    for score, pct in dist.items():
        bar = "█" * int(pct * 50)
        print(f"  {score} stars: {pct:.1%} {bar}")

    if iv.lo > 4:
        print("\n✅ Excellent! Lower bound above 4")
    elif iv.lo > 3.5:
        print("\n✓ Good performance")
    else:
        print("\n⚠️  Room for improvement")

def demo_a_b_testing():
    """A/B test survey questions or landing pages."""
    print("\n" + "=" * 70)
    print("🔬 SURVEY A/B TESTING")
    print("=" * 70)

    print("""
SCENARIO: Testing two survey versions

  Version A: Short survey (5 questions)
  Version B: Long survey (20 questions)

  Metric: Completion rate

  Which version gets more completions?
    """)

    # Version A: 70% completion
    random.seed(111)
    version_a = [1 if random.random() < 0.70 else 0 for _ in range(500)]

    # Version B: 55% completion
    version_b = [1 if random.random() < 0.55 else 0 for _ in range(500)]

    # Analyze both
    spec = StreamSpec(alpha=0.05, support=(0, 1), kind="bounded", two_sided=True)

    cs_a = EmpiricalBernsteinCS(spec)
    for result in version_a:
        cs_a.update(result)

    cs_b = EmpiricalBernsteinCS(spec)
    for result in version_b:
        cs_b.update(result)

    iv_a = cs_a.interval()
    iv_b = cs_b.interval()

    print(f"\n{'Version':>10} | {'Rate':>10} | {'95% CI':>16}")
    print("-" * 42)
    print(f"{'A (Short)':>10} | {iv_a.estimate:9.1%} | ({iv_a.lo:.1%}, {iv_a.hi:.1%})")
    print(f"{'B (Long)':>10} | {iv_b.estimate:9.1%} | ({iv_b.lo:.1%}, {iv_b.hi:.1%})")

    # Check if difference is significant
    if iv_a.lo > iv_b.hi:
        print("\n✅ Version A is significantly better!")
    elif iv_b.lo > iv_a.hi:
        print("\n✅ Version B is significantly better!")
    else:
        print("\n🤷 No significant difference - CI overlap")

def demo_real_surveys():
    """Show how to conduct real surveys."""
    print("\n" + "=" * 70)
    print("🌐 CONDUCTING REAL SURVEYS")
    print("=" * 70)

    print("""
TOOLS FOR CREATING SURVEYS:
---------------------------

FREE OPTIONS:
-------------

1. Google Forms (Free, easy)
   https://forms.google.com/

2. Typeform (Free tier available)
   https://www.typeform.com/

3. SurveyMonkey (Free tier)
   https://www.surveymonkey.com/

4. Microsoft Forms (Free with Office 365)
   https://forms.microsoft.com/

5. JotForm (Free tier)
   https://www.jotform.com/

SURVEY BEST PRACTICES:
-----------------------

1. Keep it short
   • 5-10 questions max
   • Takes < 5 minutes
   • Higher completion rates

2. Use clear questions
   • Avoid jargon
   • Be specific
   • Test with friends first

3. Use consistent scales
   • Likert: 1-5 or 1-7
   • Same direction throughout
   • Label all points

4. Avoid bias
   • Neutral wording
   • No leading questions
   • Balanced options

ANALYZING RESULTS:
------------------

```python
from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS

def analyze_survey(responses, support=(0, 5)):
    '''Analyze survey responses with confidence intervals.'''

    spec = StreamSpec(alpha=0.05, support=support, kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    for response in responses:
        cs.update(response)

    iv = cs.interval()

    print(f"Average: {iv.estimate:.2f}")
    print(f"95% CI: ({iv.lo:.2f}, {iv.hi:.2f})")
    print(f"Sample size: {iv.t}")

    # Calculate distribution
    for score in sorted(set(responses)):
        count = responses.count(score)
        pct = count / len(responses) * 100
        print(f"  {score}: {pct:.1f}%")

    return iv

# Example usage
survey_data = [5, 4, 5, 3, 4, 5, 5, 4, 3, 5]  # Responses
result = analyze_survey(survey_data)
```

COMMON SURVEY TYPES:
---------------------

1. Customer Satisfaction (CSAT)
   • Scale: 1-5
   • Question: "How satisfied were you?"

2. Net Promoter Score (NPS)
   • Scale: 0-10
   • Question: "How likely to recommend?"
   • Scores: 0-6 Detractor, 7-8 Passive, 9-10 Promoter

3. Product Feedback
   • Multiple choice + open text
   • Feature requests
   • Bug reports

4. Employee Engagement
   • Annual surveys
   • Pulse surveys
   • Anonymous feedback

SAMPLE SIZE CONSIDERATIONS:
----------------------------

More responses = tighter confidence intervals

  • 50 responses: Roughly ±14%
  • 100 responses: Roughly ±10%
  • 500 responses: Roughly ±4%
  • 1000 responses: Roughly ±3%

Always report confidence intervals with survey results!
    """)

def main():
    print("=" * 70)
    print("📋 Survey and Poll Analysis")
    print("=" * 70)

    print("""
Analyze survey responses with anytime-valid confidence.

Perfect for:
  • Market researchers
  • Product managers
  • HR professionals
  • Anyone running surveys!

EXAMPLES:
  1. Approval rating tracking
  2. Likert scale analysis
  3. A/B testing survey versions
  4. Real survey tools

Note: Demo uses simulated data.
    """)

    demo_approval_rating()
    demo_likert_scale()
    demo_a_b_testing()
    demo_real_surveys()

    print("\n" + "=" * 70)
    print("✅ SUMMARY")
    print("=" * 70)
    print("""
WHAT YOU LEARNED:
  ✓ Approval rating analysis
  ✓ Likert scale interpretation
  ✓ A/B testing methodology
  ✓ Survey best practices

KEY INSIGHT:
  Survey results have uncertainty!
  Always report confidence intervals.

NEXT STEPS:
  • Example 20: Sports statistics
  • Example 22: Website traffic
  • Example 26: Learning analytics

TOOLS:
  • Google Forms: https://forms.google.com/
  • Typeform: https://www.typeform.com/
  • SurveyMonkey: https://www.surveymonkey.com/

Remember: Bad data in, bad insights out!
Design surveys carefully.
    """)

if __name__ == "__main__":
    main()
