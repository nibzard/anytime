#!/usr/bin/env python3
"""
04_streaming_monitor.py - Real-Time Monitoring Dashboard

BEGINNER

This example shows how to build a simple real-time monitoring dashboard
using anytime confidence sequences. It simulates a production system where
metrics arrive continuously and you need to track uncertainty.

SCENARIO:
You're monitoring a server's success rate. Requests come in continuously,
and you want to track the success rate with confidence bounds over time.
This helps you detect degradations quickly while maintaining statistical rigor.

CONCEPTS:
- Continuous streaming with periodic reporting
- Tracking interval width over time
- Visualizing shrinking uncertainty
- Detecting when metrics go out of bounds
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS
import random
import time

def simulate_requests(initial_rate=0.95, drift_start=200, drift_to=0.85, n=500):
    """
    Simulate server requests with a gradual degradation.

    Initially: 95% success rate
    After drift_start: Degrades to 85% success rate
    """
    random.seed(999)

    current_rate = initial_rate
    rate_step = (drift_to - initial_rate) / 100  # Gradual drift over 100 requests

    for i in range(n):
        # Apply gradual drift after drift_start
        if i >= drift_start:
            current_rate += rate_step

        yield 1 if random.random() < current_rate else 0

def format_bar(value, width=30):
    """Create a simple ASCII bar chart."""
    filled = int(value * width)
    return "█" * filled + "░" * (width - filled)

def main():
    print("=" * 70)
    print("Real-Time Monitoring Dashboard")
    print("Server Success Rate with Confidence Sequences")
    print("=" * 70)

    # STEP 1: Setup monitoring specification
    # --------------------------------------
    spec = StreamSpec(
        alpha=0.05,           # 95% confidence
        support=(0.0, 1.0),   # Success in [0, 1]
        kind="bounded",
        two_sided=True,
        name="success_rate"
    )

    # Use EmpiricalBernstein for variance-adaptive intervals
    cs = EmpiricalBernsteinCS(spec)

    print("\nMonitoring server success rate in real-time...")
    print("Expected: ~95% initially, then degrading to ~85%\n")

    # STEP 2: Real-time monitoring loop
    # ---------------------------------
    print(f"{'Time':>6} | {'Rate':>6} | {'95% CI':>20} | {'Width':>6} | {'Status':>10}")
    print("-" * 70)

    request_stream = simulate_requests(
        initial_rate=0.95,
        drift_start=200,
        drift_to=0.85,
        n=500
    )

    threshold = 0.90  # Alert threshold
    alert_triggered = None

    for t, success in enumerate(request_stream, start=1):
        # Update confidence sequence
        cs.update(success)

        # Report every 25 requests
        if t % 25 == 0:
            iv = cs.interval()
            width = iv.hi - iv.lo

            # Check if entire CI is below threshold
            below_threshold = iv.hi < threshold
            status = "⚠️ ALERT!" if below_threshold else "✓ OK"

            if below_threshold and alert_triggered is None:
                alert_triggered = t

            print(f"{t:6d} | {iv.estimate:6.3f} | ({iv.lo:.3f}, {iv.hi:.3f}) | "
                  f"{width:6.3f} | {status:>10}")

            # Visual bar
            bar = format_bar(iv.estimate)
            print(f"       {bar}  (estimate)")
            lo_bar = format_bar(iv.lo)
            hi_bar = format_bar(iv.hi)
            print(f"       [{lo_bar}]  (lower bound)")

        # Stop after detecting degradation
        if alert_triggered and t >= alert_triggered + 50:
            break

    # STEP 3: Final summary
    # ----------------------
    iv = cs.interval()
    print("\n" + "=" * 70)
    print("MONITORING SUMMARY")
    print("=" * 70)
    print(f"Total requests observed: {iv.t}")
    print(f"Final success rate:      {iv.estimate:.3f}")
    print(f"Final 95% CI:            ({iv.lo:.3f}, {iv.hi:.3f})")
    print(f"Interval width:          {iv.hi - iv.lo:.3f}")
    print(f"Alert threshold:         {threshold:.3f}")
    print(f"Alert triggered:         At t={alert_triggered if alert_triggered else 'Never'}")

    print("\n" + "=" * 70)
    print("INSIGHTS")
    print("=" * 70)
    print("✓ Confidence intervals start wide and narrow over time")
    print("✓ EmpiricalBernstein adapts to variance (tighter intervals)")
    print("✓ You can stop monitoring as soon as CI crosses threshold")
    print("✓ Statistical guarantees remain valid despite continuous peeking")

if __name__ == "__main__":
    main()
