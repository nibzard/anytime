#!/usr/bin/env python3
"""
12_currency_monitoring.py - Financial Metrics Monitoring

BEGINNER-FRIENDLY with REAL-WORLD context

This example shows how to monitor financial metrics with anytime-valid
confidence sequences. Perfect for:
- Currency exchange rate monitoring
- Stock price tracking
- Revenue dashboards
- Conversion rate monitoring

SCENARIO:
You're a data analyst at an e-commerce company. You need to monitor the
EUR/USD exchange rate throughout the day and get alerts when it moves
significantly. You want valid confidence intervals even if you check
the rates every minute!

REAL-WORLD CONTEXT:
- Exchange rates fluctuate continuously
- Traditional statistics fail if you peek repeatedly
- Anytime-valid methods let you monitor continuously without worry
- You can set up automated alerts based on confidence intervals

WHAT YOU'LL LEARN:
- Monitoring bounded continuous metrics (rates between 0.8 and 1.2)
- Setting up alert thresholds with confidence sequences
- Understanding "narrowing confidence intervals" over time
- Production monitoring patterns

TIME: 10 minutes
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS, HoeffdingCS
import random
from datetime import datetime, timedelta

def generate_exchange_rates(base_rate=1.08, n=500, volatility=0.005):
    """
    Simulate EUR/USD exchange rate movements.

    In production, this would be:
    - API calls to: https://frankfurter.dev, exchangerate-api.com
    - Database queries to your rates table
    - Kafka messages from a rates feed

    SIMULATION PARAMETERS:
    - base_rate: Starting EUR/USD rate (historically ~1.08-1.12 in 2024)
    - n: Number of time points (e.g., 500 = 500 minutes of monitoring)
    - volatility: Daily fluctuation magnitude
    """
    random.seed(42)

    # Simulate realistic rate movement with drift and noise
    rates = []
    current_rate = base_rate

    for i in range(n):
        # Random walk with mean-reversion
        drift = random.gauss(0, volatility)
        mean_reversion = (base_rate - current_rate) * 0.01  # Gentle pull to base
        current_rate += drift + mean_reversion

        # Keep within realistic bounds (EUR/USD rarely goes outside 0.8-1.3)
        current_rate = max(0.8, min(1.3, current_rate))
        rates.append(current_rate)

    return rates

def demo_real_time_monitoring():
    """
    Monitor exchange rates with real-time confidence intervals.
    """
    print("\n" + "=" * 80)
    print("💱 REAL-TIME EXCHANGE RATE MONITORING")
    print("=" * 80)

    print("""
SCENARIO:
  Monitoring EUR/USD exchange rate throughout the trading day.

  Typical EUR/USD range (2024):
    - Low: ~1.08 (1 EUR = $1.08 USD)
    - High: ~1.12 (1 EUR = $1.12 USD)

  We want to detect when the rate moves outside our expected range.
    """)

    # Setup confidence sequence for exchange rates
    # Exchange rates are bounded (roughly 0.8 to 1.3 for EUR/USD)
    spec = StreamSpec(
        alpha=0.05,              # 95% confidence
        support=(0.8, 1.3),      # Realistic EUR/USD bounds
        kind="bounded",          # Bounded continuous metric
        two_sided=True,          # We want both upper and lower bounds
        name="eur_usd_rate"
    )

    # Use Empirical Bernstein for tighter intervals
    cs = EmpiricalBernsteinCS(spec)

    print("\n📊 Generating simulated exchange rate data...")
    print("   (In production: fetch from frankfurter.dev or your API)")

    # Generate rates
    rates = generate_exchange_rates(base_rate=1.08, n=500, volatility=0.003)

    print(f"\n✓ Generated {len(rates)} rate observations")
    print(f"  True mean rate: {sum(rates)/len(rates):.4f}")

    # Monitor with progress updates
    print("\n" + "-" * 80)
    print(f"{'Time':>8} | {'Rate':>8} | {'95% CI':>22} | {'Width':>8} | {'Status':>12}")
    print("-" * 80)

    alert_threshold_low = 1.07
    alert_threshold_high = 1.09

    alert_triggered = False

    for t, rate in enumerate(rates, start=1):
        cs.update(rate)

        # Report every 50 observations
        if t % 50 == 0:
            iv = cs.interval()
            ci_width = iv.hi - iv.lo

            # Check if we're confident rate is outside thresholds
            below_low = iv.hi < alert_threshold_low
            above_high = iv.lo > alert_threshold_high

            if below_low:
                status = "🔴 LOW"
                if not alert_triggered:
                    alert_triggered = True
                    print(f"\n⚠️  ALERT: Rate confidently BELOW {alert_threshold_low} at t={t}")
            elif above_high:
                status = "🔴 HIGH"
                if not alert_triggered:
                    alert_triggered = True
                    print(f"\n⚠️  ALERT: Rate confidently ABOVE {alert_threshold_high} at t={t}")
            else:
                status = "✓ Normal"

            print(f"{t:8d} | {rate:8.4f} | ({iv.lo:.4f}, {iv.hi:.4f}) | {ci_width:8.4f} | {status:>12}")

    # Final summary
    iv = cs.interval()

    print("\n" + "=" * 80)
    print("📈 FINAL ANALYSIS")
    print("=" * 80)
    print(f"\nAfter monitoring {iv.t} time points:")
    print(f"  Current estimate: {iv.estimate:.4f}")
    print(f"  95% Confidence Interval: ({iv.lo:.4f}, {iv.hi:.4f})")
    print(f"  CI width: {iv.hi - iv.lo:.4f}")
    print(f"  Guarantee tier: {iv.tier.value}")

def demo_method_comparison():
    """
    Compare Hoeffding vs Empirical Bernstein for financial data.
    """
    print("\n" + "=" * 80)
    print("🔬 METHOD COMPARISON: Hoeffding vs Empirical Bernstein")
    print("=" * 80)

    print("""
For financial metrics, you have two main options:

1. HOEFFDING (Conservative, simpler)
   - Wider intervals (more conservative)
   - No variance estimation needed
   - Better when: Early monitoring, high volatility

2. EMPIRICAL BERNSTEIN (Tighter, variance-adaptive)
   - Narrower intervals when variance is low
   - Estimates variance from data
   - Better when: Sufficient data, stable variance
    """)

    # Generate test data
    rates = generate_exchange_rates(n=300)
    spec = StreamSpec(alpha=0.05, support=(0.8, 1.3), kind="bounded", two_sided=True)

    # Test both methods
    hoeffding = HoeffdingCS(spec)
    eb = EmpiricalBernsteinCS(spec)

    for rate in rates:
        hoeffding.update(rate)
        eb.update(rate)

    h_iv = hoeffding.interval()
    eb_iv = eb.interval()

    print(f"\nResults after {len(rates)} observations:")
    print(f"\n{'Method':>25} | {'Estimate':>10} | {'CI Width':>12} | {'Efficiency':>12}")
    print("-" * 80)

    h_width = h_iv.hi - h_iv.lo
    eb_width = eb_iv.hi - eb_iv.lo
    efficiency = (1 - eb_width / h_width) * 100

    print(f"{'Hoeffding':>25} | {h_iv.estimate:10.4f} | {h_width:12.4f} | {'(baseline)':>12}")
    print(f"{'Empirical Bernstein':>25} | {eb_iv.estimate:10.4f} | {eb_width:12.4f} | {efficiency:>+11.1f}%")

    print(f"\n💡 Empirical Bernstein is {efficiency:.1f}% more efficient!")
    print("   This means tighter intervals = earlier decisions.")

def demo_production_setup():
    """
    Show how to set up production monitoring.
    """
    print("\n" + "=" * 80)
    print("🏭 PRODUCTION SETUP GUIDE")
    print("=" * 80)

    print("""
To implement this in production, you would use:

```python
# production_monitor.py

import requests
from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS
from datetime import datetime
import time

def fetch_exchange_rate():
    \"\"\"Fetch current EUR/USD rate from API.\"\"\"
    response = requests.get('https://api.frankfurter.dev/latest?from=EUR&to=USD')
    return float(response.json()['rates']['USD'])

def setup_alert_thresholds():
    \"\"\"Define your business thresholds.\"\"\"
    return {
        'warning_low': 1.07,
        'critical_low': 1.05,
        'warning_high': 1.12,
        'critical_high': 1.15
    }

def monitor_continuously(interval_seconds=60):
    \"\"\"Monitor every N seconds.\"\"\"
    spec = StreamSpec(
        alpha=0.05,
        support=(0.8, 1.3),
        kind="bounded",
        two_sided=True
    )

    cs = EmpiricalBernsteinCS(spec)
    thresholds = setup_alert_thresholds()

    while True:
        try:
            # Fetch current rate
            rate = fetch_exchange_rate()
            cs.update(rate)

            # Get confidence interval
            iv = cs.interval()

            # Check thresholds
            if iv.lo > thresholds['critical_high']:
                send_alert(f"CRITICAL: Rate confidently above {thresholds['critical_high']}")
            elif iv.hi < thresholds['critical_low']:
                send_alert(f"CRITICAL: Rate confidently below {thresholds['critical_low']}")

            # Log for dashboard
            log_to_dashboard(iv.t, rate, iv.lo, iv.hi)

            time.sleep(interval_seconds)

        except Exception as e:
            log_error(e)
            time.sleep(interval_seconds)

if __name__ == "__main__":
    monitor_continuously(interval_seconds=60)
```

KEY PRODUCTION CONSIDERATIONS:
  ✓ Use exponential backoff for API failures
  ✓ Store checkpoints to resume after crashes
  ✓ Set up separate monitoring for the API itself
  ✓ Log everything for debugging
  ✓ Use a message queue (Kafka, SQS) for scalability
    """)

def main():
    print("=" * 80)
    print("💱 Financial Metrics Monitoring with Anytime-Valid Inference")
    print("=" * 80)

    print("""
This example demonstrates monitoring financial metrics with anytime-valid
confidence sequences. Unlike traditional statistics, you can check your
metrics as often as you want without breaking statistical guarantees!

EXAMPLES COVERED:
  1. Real-time exchange rate monitoring
  2. Method comparison (Hoeffding vs Empirical Bernstein)
  3. Production setup guide

DATASETS IN PRODUCTION:
  • Exchange rates: frankfurter.dev, exchangerate-api.com
  • Stock prices: Alpha Vantage, Yahoo Finance API
  • Revenue metrics: Your database/data warehouse
  • Conversion rates: Your analytics platform
    """)

    # Run demonstrations
    demo_real_time_monitoring()
    demo_method_comparison()
    demo_production_setup()

    # Final summary
    print("\n" + "=" * 80)
    print("✅ SUMMARY")
    print("=" * 80)

    print("""
WHAT YOU LEARNED:
  ✓ How to monitor bounded continuous metrics (exchange rates)
  ✓ Setting up alert thresholds with confidence intervals
  ✓ When to use Hoeffding vs Empirical Bernstein
  ✓ Production patterns for continuous monitoring

WHY THIS MATTERS:
  • Traditional p-values break if you peek repeatedly
  • Anytime-valid methods let you monitor continuously
  • Confidence intervals narrow as you collect more data
  • You can automate alerts based on statistical evidence

REAL-WORLD APPLICATIONS:
  • Currency risk monitoring
  • Stock price tracking for algorithmic trading
  • Revenue dashboards with valid confidence intervals
  • Conversion rate monitoring with early stopping
  • Any metric that you need to track continuously!

NEXT STEPS:
  • Example 13: Retail sales analytics
  • Example 14: Medical trials and vaccine efficacy
  • Example 15: Multi-armed bandit optimization

SOURCES:
  • [Frankfurter - Free Exchange Rates API](https://frankfurter.dev/)
  • [ExchangeRate-API](https://www.exchangerate-api.com/)
  • [11 Best Free Retail Datasets for Machine Learning](https://www.iguazio.com/blog/13-best-free-retail-datasets-for-machine-learning/)
  • [Top 10 Healthcare Data Sets and Sources](https://kms-technology.com/blog/healthcare-data-sets/)
    """)

if __name__ == "__main__":
    main()
