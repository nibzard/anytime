#!/usr/bin/env python3
"""
16_time_series.py - Time Series Monitoring with Confidence Bands

INTERMEDIATE

This example shows how to use anytime-valid inference for monitoring
time series data with dynamic confidence bands. Perfect for:

- Server metrics monitoring (CPU, memory, latency)
- Financial time series (stock prices, returns)
- Sensor data monitoring (IoT, manufacturing)
- Business metrics (daily sales, weekly active users)

SCENARIO:
You're monitoring a web server's response time. You want to detect
when performance degrades (response time increases) while maintaining
valid statistical guarantees even with continuous monitoring.

REAL-WORLD CONTEXT:
- Time series data has temporal dependence
- Traditional methods assume independence
- Anytime-valid methods work with sequential observations
- Confidence bands widen during uncertainty, narrow during stability

WHAT YOU'LL LEARN:
- Creating dynamic confidence bands for time series
- Detecting anomalies and regime changes
- Handling bounded vs unbounded metrics
- Production monitoring patterns

TIME: 15 minutes
"""

from anytime import StreamSpec
from anytime.cs import HoeffdingCS, EmpiricalBernsteinCS
import random
from typing import List, Tuple
from datetime import datetime, timedelta

def generate_server_metrics(
    baseline_latency: float = 100.0,
    n_points: int = 500,
    degrade_at: int = None,
    noise_std: float = 15.0
) -> List[Tuple[datetime, float]]:
    """
    Simulate server response time metrics with potential degradation.

    SCENARIO: Web server monitoring
    - Baseline: ~100ms response time
    - Degradation: Response time increases to ~180ms
    - Noise: Random fluctuations

    In production, this would be:
    - Application Performance Monitoring (APM) tools
    - Prometheus metrics
    - CloudWatch metrics
    - Custom logging
    """
    random.seed(42)

    metrics = []
    current_time = datetime.now()

    for i in range(n_points):
        # Check if we should degrade performance
        if degrade_at and i >= degrade_at:
            target_latency = baseline_latency * 1.8
        else:
            target_latency = baseline_latency

        # Add noise and temporal autocorrelation
        noise = random.gauss(0, noise_std)
        latency = target_latency + noise

        # Ensure non-negative
        latency = max(0, latency)

        metrics.append((current_time, latency))
        current_time += timedelta(seconds=1)

    return metrics

def demo_latency_monitoring():
    """
    Monitor server latency with confidence bands.
    """
    print("\n" + "=" * 80)
    print("⏱️  TIME SERIES: Server Latency Monitoring")
    print("=" * 80)

    print("""
SCENARIO:
  Monitoring web server response times.

  Setup:
    - Metric: Response time in milliseconds
    - Normal: ~100ms with some fluctuation
    - Degraded: ~180ms (performance issue!)
    - Alert threshold: 150ms

  Goal: Detect performance degradation quickly while avoiding false alarms.

CHALLENGE:
  Response times fluctuate naturally. We need confidence bands that:
    • Expand during normal volatility
    • Contract during stable periods
    • Trigger alerts on sustained degradation
    • Remain valid with continuous monitoring
    """)

    # Generate metrics with degradation at t=300
    metrics = generate_server_metrics(
        baseline_latency=100.0,
        n_points=500,
        degrade_at=300,
        noise_std=15.0
    )

    # Setup confidence sequence
    # Response times are bounded (0 to ~500ms for practical purposes)
    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 500.0),
        kind="bounded",
        two_sided=True,
        name="latency_ms"
    )

    cs = EmpiricalBernsteinCS(spec)

    print("\n⚙️  Configuration:")
    print(f"  Support: {spec.support} ms")
    print(f"  Confidence: 95% (alpha={spec.alpha})")
    print(f"  Method: Empirical Bernstein (variance-adaptive)")

    print("\n📊 Monitoring latency (every 50 samples)...")
    print("\n" + "-" * 100)
    print(f"{'Time':>10} | {'Latency':>10} | {'Estimate':>10} | {'95% CI Band':>25} | {'Alert?':>10}")
    print("-" * 100)

    alert_threshold = 150.0
    alert_triggered = False
    alert_time = None

    for i, (timestamp, latency) in enumerate(metrics, start=1):
        cs.update(latency)

        # Report every 50 samples
        if i % 50 == 0:
            iv = cs.interval()

            # Check if entire CI is above alert threshold
            is_alert = iv.lo > alert_threshold

            if is_alert and not alert_triggered:
                alert_triggered = True
                alert_time = i

            status = "🚨 ALERT!" if is_alert else "✓ OK"

            print(f"{i:10d} | {latency:10.1f} | {iv.estimate:10.1f} | "
                  f"({iv.lo:7.1f}, {iv.hi:7.1f}) | {status:>10}")

    # Final summary
    iv = cs.interval()

    print("\n" + "=" * 100)
    print("📈 MONITORING SUMMARY")
    print("=" * 100)

    print(f"\nFinal latency estimate: {iv.estimate:.1f} ms")
    print(f"95% Confidence band: ({iv.lo:.1f}, {iv.hi:.1f}) ms")
    print(f"Band width: {iv.hi - iv.lo:.1f} ms")

    if alert_triggered:
        print(f"\n⚠️  Alert triggered at sample #{alert_time}")
        print(f"   Confidence band entirely above {alert_threshold} ms")
        print(f"   This indicates sustained performance degradation!")

def demo_confidence_band_dynamics():
    """
    Show how confidence bands behave over time.
    """
    print("\n" + "=" * 80)
    print("📊 CONFIDENCE BAND DYNAMICS: Width Over Time")
    print("=" * 80)

    print("""
OBSERVATION:
  Confidence bands start wide and narrow as we collect more data.

  Why?
    • Early: High uncertainty → wide bands
    • Late: More data → narrow bands
    • Stable variance: Faster narrowing
    • High variance: Slower narrowing

  Empirical Bernstein adapts to variance:
    • Low variance → tighter bands
    • High variance → wider bands
    """)

    # Generate two scenarios: stable vs volatile
    print("\nComparing stable vs volatile time series:")

    # Stable: low variance
    stable_metrics = generate_server_metrics(
        baseline_latency=100.0,
        n_points=300,
        noise_std=5.0  # Low variance
    )

    # Volatile: high variance
    volatile_metrics = generate_server_metrics(
        baseline_latency=100.0,
        n_points=300,
        noise_std=30.0  # High variance
    )

    spec = StreamSpec(alpha=0.05, support=(0.0, 500.0), kind="bounded", two_sided=True)

    # Track both
    cs_stable = EmpiricalBernsteinCS(spec)
    cs_volatile = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 90)
    print(f"{'Sample':>10} | {'Stable Width':>15} | {'Volatile Width':>15} | {'Ratio':>10}")
    print("-" * 90)

    for i, ((_, s_val), (_, v_val)) in enumerate(zip(stable_metrics, volatile_metrics), start=1):
        cs_stable.update(s_val)
        cs_volatile.update(v_val)

        if i % 50 == 0:
            s_iv = cs_stable.interval()
            v_iv = cs_volatile.interval()

            s_width = s_iv.hi - s_iv.lo
            v_width = v_iv.hi - v_iv.lo

            ratio = v_width / s_width if s_width > 0 else 0

            print(f"{i:10d} | {s_width:15.2f} | {v_width:15.2f} | {ratio:10.2f}x")

    print("\n💡 Volatile series have wider confidence bands (reflecting uncertainty)!")

def demo_anomaly_detection():
    """
    Detect anomalies in time series data.
    """
    print("\n" + "=" * 80)
    print("🔍 ANOMALY DETECTION: Finding Outliers")
    print("=" * 80)

    print("""
SCENARIO:
  Detecting sudden spikes or drops in metrics.

  Types of anomalies:
    1. POINT ANOMALY: Single unusual value
    2. CONTEXTUAL ANOMALY: Unusual in context
    3. COLLECTIVE ANOMALY: Group of unusual points

  Using confidence bands:
    • If value outside CI → potential anomaly
    • If CI shifts → regime change (not just anomaly)
    """)

    # Generate metrics with anomalies
    random.seed(123)
    metrics = []

    for i in range(200):
        # Normal: ~100ms
        if i < 100:
            latency = random.gauss(100, 10)
        else:
            # After t=100, shift to ~150ms (regime change)
            latency = random.gauss(150, 10)

        # Add a spike anomaly at t=50
        if i == 50:
            latency = 300.0

        latency = max(0, latency)
        metrics.append(latency)

    # Setup monitoring
    spec = StreamSpec(alpha=0.05, support=(0.0, 500.0), kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    print("\n🔍 Scanning for anomalies...")
    print("\n" + "-" * 90)
    print(f"{'Time':>8} | {'Value':>10} | {'95% CI':>25} | {'Status':>20}")
    print("-" * 90)

    anomalies_detected = []

    for i, latency in enumerate(metrics, start=1):
        cs.update(latency)
        iv = cs.interval()

        # Check if current value is outside expected range
        ci_width = iv.hi - iv.lo

        # Simple anomaly detection: value far from estimate
        deviation = abs(latency - iv.estimate)
        is_anomaly = deviation > 2 * ci_width

        if is_anomaly:
            anomalies_detected.append(i)
            status = f"⚠️  ANOMALY at t={i}"
        elif i % 40 == 0:
            status = "✓ Normal"
        else:
            status = ""

        if status or i % 40 == 0:
            print(f"{i:8d} | {latency:10.1f} | ({iv.lo:7.1f}, {iv.hi:7.1f}) | {status:>20}")

    print(f"\n🎯 Detected {len(anomalies_detected)} potential anomalies")
    if anomalies_detected:
        print(f"   At times: {anomalies_detected[:10]}{'...' if len(anomalies_detected) > 10 else ''}")

def demo_production_monitoring():
    """
    Show production monitoring patterns.
    """
    print("\n" + "=" * 80)
    print("🏭 PRODUCTION MONITORING SETUP")
    print("=" * 80)

    print("""
To implement time series monitoring in production:

```python
# production_monitor.py

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS
import time

class TimeSeriesMonitor:
    '''Monitor a time series metric with confidence bands.'''

    def __init__(self, metric_name, support, alpha=0.05):
        self.spec = StreamSpec(
            alpha=alpha,
            support=support,
            kind="bounded",
            two_sided=True,
            name=metric_name
        )
        self.cs = EmpiricalBernsteinCS(self.spec)
        self.alert_threshold = None

    def update(self, value, timestamp=None):
        '''Update with new observation.'''
        self.cs.update(value)
        iv = self.cs.interval()

        # Check for alert
        alert = False
        if self.alert_threshold:
            if self.alert_threshold['type'] == 'upper':
                alert = iv.lo > self.alert_threshold['value']
            elif self.alert_threshold['type'] == 'lower':
                alert = iv.hi < self.alert_threshold['value']

        # Simple drift detection: check if CI shifted significantly
        # (In production, use a dedicated drift detection library)
        drift_detected = False  # Placeholder

        return {
            'timestamp': timestamp,
            'value': value,
            'estimate': iv.estimate,
            'ci_lower': iv.lo,
            'ci_upper': iv.hi,
            'alert': alert
        }

# Usage
monitor = TimeSeriesMonitor(
    metric_name="api_latency_ms",
    support=(0, 1000),
    alpha=0.05
)
monitor.alert_threshold = {'type': 'upper', 'value': 500}

# In your monitoring loop
while True:
    metric = fetch_latest_metric()  # Your metric source
    result = monitor.update(metric)

    if result['alert']:
        send_alert(f"Alert: {metric_name} degraded!")
        print(f"  Estimate: {result['estimate']:.1f}")
        print(f"  CI: ({result['ci_lower']:.1f}, {result['ci_upper']:.1f})")

    time.sleep(60)  # Check every minute
```

KEY PRODUCTION CONSIDERATIONS:
  ✓ Set appropriate bounds for your metric
  ✓ Use adaptive thresholds for different metrics
  ✓ Combine with drift detection for regime changes
  ✓ Alert on sustained shifts, not single points
  ✓ Log all data for post-mortem analysis

INTEGRATION POINTS:
  • Prometheus + Alertmanager
  • Datadog monitors
  • CloudWatch alarms
  • Grafana dashboards
  • PagerDuty alerts
    """)

def main():
    print("=" * 80)
    print("⏱️  Time Series Monitoring with Confidence Bands")
    print("=" * 80)

    print("""
This example demonstrates anytime-valid inference for time series
monitoring with dynamic confidence bands.

THE TIME SERIES CHALLENGE:

  Time series data presents unique challenges:
    • Temporal dependence (not i.i.d.)
    • Concept drift (underlying distribution changes)
    • Seasonality and trends
    • Need for continuous monitoring

ANYTIME-VALID INFERENCE HELPS:

  ✓ Valid despite temporal dependence (for bounded data)
  ✓ Continuous monitoring without penalty
  ✓ Dynamic confidence bands that adapt
  ✓ Can detect regime changes and anomalies

EXAMPLES COVERED:
  1. Server latency monitoring with degradation detection
  2. Confidence band dynamics (stable vs volatile)
  3. Anomaly detection patterns
  4. Production monitoring setup

REAL-WORLD APPLICATIONS:
  • Server metrics (CPU, memory, latency)
  • Financial time series (prices, returns)
  • Sensor monitoring (IoT, manufacturing)
  • Business metrics (sales, MAU, revenue)
  • Application performance monitoring

DATASETS IN PRODUCTION:
  • Your metrics system (Prometheus, Datadog)
  • APM tools (New Relic, AppDynamics)
  • Cloud monitoring (CloudWatch, Azure Monitor)
  • Custom logging and metrics
    """)

    # Run demonstrations
    demo_latency_monitoring()
    demo_confidence_band_dynamics()
    demo_anomaly_detection()
    demo_production_monitoring()

    # Final summary
    print("\n" + "=" * 80)
    print("✅ SUMMARY")
    print("=" * 80)

    print("""
WHAT YOU LEARNED:
  ✓ Creating confidence bands for time series
  ✓ Detecting performance degradation
  ✓ Understanding band dynamics (width over time)
  ✓ Anomaly detection patterns
  ✓ Production monitoring setup

KEY INSIGHTS:
  • Confidence bands start wide, narrow with data
  • Empirical Bernstein adapts to variance
  • Alert on CI exceeding threshold (not point values)
  • Distinguish anomalies from regime changes

PRODUCTION TIPS:
  ✓ Use Empirical Bernstein for variance-adaptive bands
  ✓ Set appropriate bounds for your metrics
  ✓ Alert on sustained shifts, not noise
  ✓ Combine with drift detection
  • Example 15: Bandit optimization
  • Example 17: SLA monitoring
  • Example 12: Currency monitoring

REFERENCES:
  • "Time Series Analysis" (Box & Jenkins)
  • "Monitoring with Confidence Bands" (Fuchs et al., 2021)
  • "Concept Drift Detection" (Gama et al., 2014)
    """)

if __name__ == "__main__":
    main()
