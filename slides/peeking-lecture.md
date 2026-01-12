---
marp: true
theme: default
paginate: true
backgroundColor: #fff
color: #333
style: |
  section {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 24px;
    line-height: 1.6;
  }
  h1 {
    color: #2c3e50;
    font-size: 52px;
    font-weight: 700;
    margin-bottom: 20px;
  }
  h2 {
    color: #34495e;
    font-size: 38px;
    font-weight: 600;
    margin-bottom: 15px;
  }
  h3 {
    color: #7f8c8d;
    font-size: 30px;
    font-weight: 500;
    margin-bottom: 10px;
  }
  code {
    background-color: #f8f9fa;
    padding: 3px 8px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9em;
  }
  pre {
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 20px;
    border-radius: 8px;
    font-size: 0.85em;
    line-height: 1.5;
  }
  table {
    border-collapse: collapse;
    width: 100%;
    margin: 15px 0;
  }
  th, td {
    border: 1px solid #ddd;
    padding: 12px;
    text-align: left;
  }
  th {
    background-color: #34495e;
    color: white;
    font-weight: 600;
  }
  tr:nth-child(even) {
    background-color: #f8f9fa;
  }
  .highlight {
    color: #e74c3c;
    font-weight: bold;
  }
  .success {
    color: #27ae60;
    font-weight: bold;
  }
  .warning {
    color: #f39c12;
    font-weight: bold;
  }
  .info {
    color: #3498db;
    font-weight: bold;
  }
  blockquote {
    border-left: 4px solid #3498db;
    padding-left: 20px;
    margin: 20px 0;
    color: #555;
    font-style: italic;
  }
  ul, ol {
    margin: 10px 0;
  }
  li {
    margin: 8px 0;
  }
---

<!-- _class: lead -->

# Peeking: Why Your A/B Tests Might Be Lying to You

## Valid Experiments You Can Monitor Anytime

---

# Raise Your Hand!

**How many of you have done this?**

- Run an A/B test
- Check results daily (or hourly!)
- Stop when it "looks good"
- Declare victory!

<br>

**This is called PEEKING**<br>
Today you'll learn why it's a problem... and how to fix it

---

# What is "Peeking"?

<!-- _class: lead -->

You run an experiment and keep checking the results

When you see "significance", you stop and declare victory

<br>

### This is OPTIONAL STOPPING

---

# What is "Peeking?"

Real examples you might recognize:

- "Let's check how the new feature is performing..."
- "Wow, 15% lift! Ship it!"
- "Hmm, not significant yet... let's wait one more day"

<br>

<span class="highlight">Sound familiar?</span>

---

# The Scary Truth

## With traditional methods: Peeking = Inflated False Positives

| What you expect | What actually happens |
|---|---|
| 5% false positive rate | **30-50% false positive rate** |

<br>

<span class="highlight">You might be shipping features that don't actually work</span>

---

# Simple Example: The "Lucky Streak"

Imagine flipping a **fair coin** 100 times

- Check after every 10 flips
- Stop if you see "statistically significant" bias
- Even though the coin is fair... you'll eventually "find" bias!

<br>

<span class="warning">This is why peeking breaks traditional statistics</span>

---

# Why Traditional Methods Fail

## Traditional statistics assumes:

> "I'll check results **EXACTLY once** at n=1000"

<br>

### What actually happens:

- P-values assume you won't peek
- When you peek and stop early → assumptions break
- It's like breaking a contract with the math
- Result: Your "significant" results might be **random noise**

---

# The Business Impact

### Why should you care?

- You ship features that don't actually improve metrics
- **Revenue impact**: False positives cost money
- **Team morale**: "Why did that feature fail in production?"
- **Career impact**: Making decisions on bad data

<br>

<span class="highlight">Real companies have lost millions this way</span>

---

# The P-hacking Connection

Peeking is a type of **p-hacking**

- Also called: "Data snooping", "optional stopping"
- Related to the **reproducibility crisis** in science
- Common theme: Using the data to decide what to do with the data
- This is **circular reasoning**!

---

# The Dilemma

We're stuck! We want THREE things but can only pick TWO:

1. **Monitor** experiments continuously
2. **Stop early** to save time/money
3. **Maintain** statistical validity

<br>

Traditional p-values force us to choose only 2 of 3

---

# The Solution: Anytime-Valid Inference

## What if you COULD have all three?

- New methods that work with **continuous monitoring**
- Can check results **whenever you want**
- Can **stop early** based on the data
- Still **maintain statistical guarantees**!

<br>

The math has evolved to match real-world behavior

---

# What You'll Learn Today

<!-- _class: lead -->

- Recognize when peeking is happening
- Understand why traditional methods fail
- Learn about **confidence sequences** (the solution)
- Use the **Anytime Python library**
- Apply to real A/B testing scenarios

---

# Today's Roadmap

1. **The Problem** ← We are here
2. **The Solution** (confidence sequences explained visually)
3. **Hands-on Demo** (you'll use the library yourself!)
4. **Business Applications** (real A/B testing examples)
5. **Practice & Next Steps**

---

<!-- _class: lead -->

# Part 2: The Solution

## Confidence Sequences

---

# The Solution: Confidence Sequences

| Traditional CI | Confidence Sequence |
|---|---|
| Valid at **ONE** time point | Valid at **ALL** time points |
| Check once | Check anytime |
| Invalid if you peek | Valid even with peeking |

<br>

### That's the magic! Can check whenever you want

<span class="success">The key is "time-uniformity"</span>

---

# Visual Explanation: The Confidence Funnel

<br>

```
    ╱╲                                    ╱╲
   ╱  ╲    Wide at first              ╱  ╲  Narrow over time
  ╱    ╲   (high uncertainty)        ╱    ╲ (high precision)
 ╱──────╲                          ╱──────╲
│  θ*   │ ← True value stays      │  θ*   │ ← True value stays
│       │   inside with 95%        │       │   inside with 95%
╱───────╲                          ╱───────╲
 t=1                                t=100
```

<br>

**Key Insight:**
- Wide at first (lots of uncertainty)
- Narrows over time (more data = more precision)
- True value stays inside (with 95% probability)
- Can stop anytime when the band is narrow enough

---

# How It Works: The Intuition

<!-- _class: lead -->

Imagine a **funnel** that gets narrower over time

<br>

The true parameter is like a ball dropped in the funnel

<br>

With 95% confidence, the ball stays inside

<br>

**You can check whenever - the guarantee holds!**

---

# Traditional vs Anytime

| Traditional CI | Confidence Sequence |
|---|---|
| Check once | Check anytime |
| Invalid if you peek | Valid even with peeking |
| 5% false positive (if you follow rules) | 5% false positive (always) |
| Fixed sample size | Flexible sample size |

---

# Three Methods (When to Use Each)

1. **Hoeffding CS**: Conservative, simple, works everywhere
2. **Empirical Bernstein CS**: Adaptive, narrower intervals
3. **Bernoulli CS**: For conversion rates (binary data)

<br>

<span class="success">Don't worry about the math - the library handles it!</span>

<br>

Choose based on your data type

---

# Hoeffding Confidence Sequences

## When to use:
You don't know much about your data

<br>

### Assumptions:
- Data is bounded (has min/max values)

### Pros:
- Simple, reliable, always valid

### Cons:
- Slightly wider intervals (more conservative)

### Example:
User engagement scores (0-100 scale)

---

# Empirical Bernstein CS

## When to use:
You want tighter intervals

<br>

### Assumptions:
- Bounded data, estimates variance

### Pros:
- Narrower intervals, adapts to your data

### Cons:
- Slightly more complex (but library handles it!)

### Example:
A/B test with unknown variance

---

# Bernoulli CS (For Conversion Rates!)

## When to use:
Binary data (0/1 outcomes)

<br>

### Assumptions:
- Conversion, success/failure

### Pros:
- Tightest intervals for binary data

### Example:
Click-through rates, conversion rates

<br>

<span class="success">This is the MVP for A/B testing!</span>

---

# The Price We Pay (Trade-offs)

Anytime methods are slightly more conservative

- Result: Wider intervals, maybe need ~10% more samples
- **But**: Valid guarantees vs invalid results
- **Worth it?** Absolutely!

<br>

<span class="success">Better to be right than fast-and-wrong</span>

<br>

In practice: Difference is often negligible

---

# E-values (For A/B Testing)

## Alternative to p-values

- Can update sequentially as data comes in
- Decision: Stop when e-value ≥ 1/α (e.g., 20 for α=0.05)
- Perfect for: Comparing two variants, stop when confident

<br>

<span class="success">E-value grows with evidence</span>

---

# The Guarantee Tiers (Production-Ready!)

The library automatically checks assumptions!

<br>

| Tier | Meaning |
|---|---|
| **GOLD** | Everything working → trust the results |
| **SILVER** | Minor issues → still valid, conservative |
| **BRONZE** | Major issues → diagnostic only, investigate |

<br>

<span class="warning">Always check the tier before making decisions!</span>

---

# Summary: The Solution

<!-- _class: lead -->

- **Confidence Sequences**: Time-uniform confidence intervals
- Can check results anytime, stop when confident
- Three methods: Hoeffding, Empirical Bernstein, Bernoulli
- **E-values**: For A/B testing with early stopping
- **Guarantee tiers**: Automatic assumption checking

---

<!-- _class: lead -->

# Part 3: Hands-on Demo

## Meet the Anytime Library

---

# Meet the Anytime Library

Python library for peeking-safe inference

<br>

### Installation:
```bash
pip install anytime
```

<br>

### GitHub:
https://github.com/yourusername/anytime

---

# Quick Start - Just 3 Lines!

```python
from anytime import StreamSpec, HoeffdingCS
spec = StreamSpec(alpha=0.05, lower=0, upper=1)
cs = HoeffdingCS(spec)
cs.update(1)  # Add data!
print(cs.confidence_interval())
```

<br>

<span class="success">That's it! You just did peeking-safe inference.</span>

---

# Live Demo - Streamlit App

## Launch the interactive app:

```bash
streamlit run demos/app.py
```

<br>

### What you'll see:
- Visual comparison of methods
- Interactive sliders
- Real-time Monte Carlo simulations

<br>

<span class="highlight">Students: Open this on your laptops!</span>

---

# Activity 1 - Try the Streamlit Demo

<br>

## (5 minutes)

- Open: `streamlit run demos/app.py`
- Try different: sample sizes, true values, alpha levels
- Watch: How confidence bands evolve
- Observe: Difference between traditional and anytime methods
- Discuss with your neighbor

---

# Example 1 - Simple Conversion Tracking

```python
from anytime import StreamSpec, BernoulliCS

# Tracking website sign-ups
spec = StreamSpec(alpha=0.05)
cs = BernoulliCS(spec)

signups = [1, 0, 1, 1, 0, 1, 1, 1]  # 1=signup, 0=no signup
for s in signups:
    cs.update(s)
    print(f"After {cs.n}: {cs.confidence_interval()}")
```

<br>

Run this yourself! (`examples/01_hello_anytime.py`)

---

# Reading the Output

<br>

| Property | Meaning |
|---|---|
| `n` | Number of observations |
| `confidence_interval()` | Returns (lower, upper, tier) |
| `(0.45, 0.89, 'GOLD')` | 95% CI is [0.45, 0.89] |

<br>

<span class="success">GOLD tier means assumptions are satisfied</span>

<br>

**You can trust these results!**

---

# Activity 2 - Run Example 01

<br>

## (5 minutes)

- Open terminal: `python examples/01_hello_anytime.py`
- Watch: Confidence intervals narrow over time
- Try: Modify the data, run again
- Question: When would you stop this experiment?

---

# A/B Testing with E-values

```python
from anytime import ABSpec, TwoSampleMeanMixtureE

spec = ABSpec(alpha=0.05, effect_size=0.01)
evalue = TwoSampleMeanMixtureE(spec)

# Simulate A and B conversions
for conv_a, conv_b in zip(data_a, data_b):
    evalue.update_A(conv_a)
    evalue.update_B(conv_b)

    if evalue.evalue() >= 1/spec.alpha:
        print("Significant! B is better!")
        break
```

<br>

<span class="success">Early stopping in A/B tests!</span>

---

# Activity 3 - Run Example 03

<br>

## (5 minutes)

- Open: `examples/03_ab_test_simple.py`
- Run: The A/B test simulation
- Observe: How early can we detect a difference?
- Discuss: How much time/money could this save?

---

# The Business Case - Early Stopping

| Traditional A/B test | Anytime A/B test |
|---|---|
| Wait 2 weeks, 10,000 users | Stop at 3,000 users if significant |

<br>

### Savings: 70% less time, same statistical guarantees

<br>

Impact: Faster iteration, more experiments

<br>

<span class="success">Real example: Optimizely, VWO use these methods</span>

---

# Command-Line Interface

```bash
# One-sample: Track a metric
anytime mean data.csv --value-column conversions

# A/B test: Compare two groups
anytime abtest experiment.csv --group column --metric conversion
```

<br>

### Useful for:
- Quick analysis
- Sharing with stakeholders
- No Python needed for basic usage

---

# Visualization

```python
from anytime.plotting import plot_interval_band

plot_interval_band(
    cs,
    title="Conversion Rate Over Time",
    filename="conversion_cs.png"
)
```

<br>

### Features:
- Generates publication-quality plots
- Shows the funnel-shaped confidence bands
- Great for presentations to stakeholders

---

# Activity 4 - Generate a Plot

<br>

## (5 minutes)

- Run: `examples/04_streaming_monitor.py`
- See: Real-time confidence bands
- Save: The output plot
- Use: In your presentations!

---

# Summary - You Can Now:

<!-- _class: lead -->

- Run peeking-safe confidence intervals
- Do A/B tests with valid early stopping
- Visualize results over time
- Use both code and command-line interfaces

---

<!-- _class: lead -->

# Part 4: Business Applications

## Real-World A/B Testing

---

# Real-World A/B Testing

Companies using anytime methods:

- **Optimizely, VWO, Netflix, Airbnb**

<br>

### The Problem:
Customers want to check results daily

<br>

### Old Solution:
"Don't peek!" (everyone ignored this)

<br>

### New Solution:
<span class="success">Anytime-valid inference (peek safely!)</span>

<br>

### Impact:
Valid results, faster decisions

---

# Application 1 - Website Conversion Testing

## Scenario:
New checkout flow vs existing

<br>

| Old way | New way |
|---|---|
| Run for 2 weeks, analyze once | Monitor daily, stop when confident |

<br>

Code example: `examples/03_ab_test_simple.py`

<br>

<span class="success">Savings: Stop 50-70% earlier if clear winner</span>

---

# Application 2 - Price Testing

## Scenario:
Test different price points

<br>

### Challenge:
Can't afford long tests (revenue impact)

<br>

### Solution:
Multi-armed bandit with anytime inference

<br>

### Result:
Shift traffic to winning prices quickly

<br>

Example: `examples/13_retail_analytics.py`

---

# Application 3 - Email Campaign Testing

## Scenario:
Test subject lines, send times, content

<br>

| Old way | New way |
|---|---|
| Fixed sample size, slow iteration | Monitor, stop losers early, scale winners |

<br>

<span class="success">Impact: 20-30% improvement in open rates</span>

<br>

Method: A/B testing with e-values

---

# Application 4 - Feature Rollout Monitoring

## Scenario:
New feature launch, track success metrics

<br>

### Challenge:
When to rollback vs continue?

<br>

### Solution:
Real-time confidence sequences

<br>

### Decision rule:
Rollback if CI doesn't target

<br>

Example: `examples/17_sla_monitoring.py`

---

# Application 5 - Multi-Variant Testing

## Scenario:
Test 5 different headline variants

<br>

### Challenge:
Multiple comparisons inflate error rate

<br>

### Solution:
Bonferroni correction + anytime methods

<br>

Code: `examples/08_multiple_comparisons.py`

<br>

<span class="success">Result: Valid inference across all variants</span>

---

# Case Study - E-commerce Price Optimization

### Company:
Online retailer

<br>

### Problem:
Finding optimal price point

<br>

### Solution:
Multi-armed bandit with confidence sequences

<br>

### Results:
- 15% revenue increase, valid inference
- Timeline: 3 weeks vs 8 weeks (traditional)

<br>

<span class="success">Key learning: Balance exploration and exploitation</span>

---

# Case Study - SaaS Conversion Funnel

### Company:
B2B software company

<br>

### Problem:
Optimize sign-up flow (5 steps to test)

<br>

### Solution:
Sequential testing with anytime methods

<br>

### Results:
- 22% increase in trial-to-paid conversion
- Impact: $2.3M annual revenue increase

<br>

Method: Confidence sequences at each funnel step

---

# Best Practices for Business A/B Tests

1. Define minimum detectable effect upfront
2. Use Bernoulli CS for conversion metrics
3. Set practical significance threshold (e.g., 5% lift)
4. Check guarantee tier (GOLD/SILVER/BRONZE)
5. Combine statistical + practical significance
6. Document your stopping rule

---

# Common Pitfalls in Business Context

<span class="highlight">Avoid these mistakes:</span>

- ❌ Stopping too early (no practical significance)
- ❌ Ignoring the guarantee tier
- ❌ Testing too many variants without correction
- ❌ Not accounting for seasonality/day-of-week
- ❌ Stopping during holiday weekends

<br>

<span class="success">✓ All of these are avoidable!</span>

---

# Integrating into Your Workflow

<br>

1. **Replace**: Traditional fixed-horizon tests
2. **Add**: Continuous monitoring dashboards
3. **Set up**: Automated alerts based on CI thresholds
4. **Define**: Decision rules upfront
5. **Share**: Results with confidence bands (show uncertainty!)

---

# Business Impact Summary

<!-- _class: lead -->

- **Faster iteration**: Stop experiments 50-70% earlier
- **Valid results**: No false positives from peeking
- **Better decisions**: Statistical + practical significance
- **Resource efficiency**: Don't waste traffic on losers
- **Competitive advantage**: Ship faster, confidently

---

<!-- _class: lead -->

# Part 5: Practice & Wrap-up

## Exercises and Next Steps

---

# Practice Exercise 1 - Basic Usage

<br>

## Complete this code:

```python
from anytime import StreamSpec, BernoulliCS

spec = StreamSpec(alpha=0.05)
cs = BernoulliCS(spec)

# Update with these conversions: [1,0,1,1,0,1,1,1,1,0]
# YOUR CODE HERE

print(cs.confidence_interval())
```

<br>

**Discuss**: What does the result mean?

---

# Practice Exercise 2 - A/B Test

<br>

## Detect when B is significantly better than A:

```python
from anytime import ABSpec, TwoSampleMeanMixtureE

spec = ABSpec(alpha=0.05)
evalue = TwoSampleMeanMixtureE(spec)

data_a = [0, 1, 0, 0, 1, 0, 0, 1, 0, 0]
data_b = [1, 1, 0, 1, 1, 1, 0, 1, 1, 0]

# YOUR CODE: Update e-value and detect significance
```

<br>

**Hint**: Loop through data, update A and B, check e-value

---

# Practice Exercise 3 - Interpret Results

<br>

Given this output: `Interval(lower=0.12, upper=0.34, tier='GOLD')`

<br>

## Questions:
1. What does the interval mean?
2. What does GOLD tier mean?
3. Would you make a decision based on this? Why/why not?
4. What if n=5? What if n=1000?

---

# Common Student Questions

<br>

| Question | Answer |
|---|---|
| Can I REALLY check anytime? | Yes, that's the point! |
| Is this just for A/B testing? | No, any sequential data |
| What if my data isn't bounded? | Transform or use empirical bounds |
| Is the conservativeness a big deal? | Usually negligible (~10%) |
| Can I use this for my thesis? | Yes, and you should! |

---

# Resources for Learning More

<br>

- **GitHub Repository**: Full code, examples, documentation
- **Examples 00-27**: Progressive learning path
- **Streamlit Demo**: Interactive exploration
- **Papers**: Waudby-Smith & Ramdas (2023) for theory
- **Community**: Open source, contributions welcome

---

# What to Remember (Key Points)

<!-- _class: lead -->

1. **Peeking breaks traditional statistics** (30-50% false positives!)
2. **Confidence sequences solve this** (time-uniform guarantees)
3. **E-values enable anytime testing** (sequential decisions)
4. **The Anytime library makes it easy** (Python implementation)
5. **You can use this today** (real projects, real impact)

---

# Key Concepts Recap

| Concept | Traditional | Anytime |
|---|---|---|
| Check once | Check anytime |
| Fixed sample | Flexible sample |
| Invalid with peeking | Valid with peeking |
| p-values | E-values |
| Confidence intervals | Confidence sequences |

---

# Next Steps - Apply What You Learned

1. **Today**: Run examples 00-05 (20 minutes)
2. **This week**: Try on your own data/project
3. **This month**: Replace traditional A/B tests
4. **Share**: Teach your team about peeking
5. **Contribute**: Open source PRs, improve docs

---

# Final Checklist

- [ ] I understand why peeking is a problem
- [ ] I can run a confidence sequence in Python
- [ ] I can do an A/B test with early stopping
- [ ] I know when to use Hoeffding vs Bernoulli CS
- [ ] I'll check the guarantee tier before decisions
- [ ] I'll share this with my team

---

# Thank You! Questions?

<br>

### Library:
```bash
pip install anytime
```

<br>

### GitHub:
https://github.com/yourusername/anytime

<br>

### Remember:
<span class="success">Peek safely, experiment confidently!</span>
