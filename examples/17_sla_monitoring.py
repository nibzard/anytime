#!/usr/bin/env python3
"""
17_sla_monitoring.py - Service Level Agreement (SLA) Monitoring

INTERMEDIATE

This example shows how to use anytime-valid inference for monitoring
service level agreements (SLAs) and service level objectives (SLOs).

Perfect for:
- SRE/DevOps teams monitoring service reliability
- API uptime and error rate tracking
- Performance guarantee validation
- Customer-facing SLA dashboards

SCENARIO:
You're an SRE managing a critical API. You've promised customers 99.9%
uptime (no more than 43 minutes of downtime per month). You need to
track this continuously and provide valid confidence intervals.

REAL-WORLD CONTEXT:
- SLAs are legal/contractual obligations with financial penalties
- Traditional point estimates don't capture uncertainty
- Need valid inference with continuous monitoring
- Must distinguish between temporary blips and real degradation

WHAT YOU'LL LEARN:
- Monitoring uptime/error rates with confidence sequences
- Setting up SLO alerting with valid guarantees
- Burn rate and error budget calculations
- Production SLA dashboard patterns

TIME: 15 minutes
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS, BernoulliCS
import random
from datetime import datetime, timedelta
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class SLAConfig:
    """Configuration for an SLA monitor."""
    name: str
    target_success_rate: float  # e.g., 0.999 for 99.9%
    window_minutes: int
    alert_threshold: float  # Alert when CI lower bound crosses this

def generate_api_requests(
    n_requests: int = 10000,
    success_rate: float = 0.995,
    degrade_at: int = None,
    degraded_rate: float = 0.98
) -> List[int]:
    """
    Simulate API requests (1=success, 0=failure).

    SCENARIO: API endpoint monitoring
    - Normal: 99.5% success rate (0.5% errors)
    - Degraded: 98% success rate (2% errors)
    - Need to detect degradation quickly

    In production, this would come from:
    - Load balancer logs
    - API gateway metrics
    - Application logs
    - Monitoring systems (Prometheus, Datadog)
    """
    random.seed(42)

    requests = []
    for i in range(n_requests):
        # Check if we should degrade
        if degrade_at and i >= degrade_at:
            current_rate = degraded_rate
        else:
            current_rate = success_rate

        # Generate request outcome
        success = 1 if random.random() < current_rate else 0
        requests.append(success)

    return requests

def demo_sla_monitoring():
    """
    Monitor API success rate against SLA.
    """
    print("\n" + "=" * 80)
    print("📊 SLA MONITORING: API Success Rate")
    print("=" * 80)

    print("""
SCENARIO:
  Monitoring a critical API endpoint.

  SLA Commitment:
    - Target: 99.5% success rate
    - Measurement window: Rolling 24 hours
    - Alert threshold: 99.0% (must be confident we're above this)

  Current State:
    - Normal operation: ~99.5% success
    - Degraded operation: ~98% success
    - Need to detect degradation reliably

CHALLENGE:
  With thousands of requests, even small error rate increases matter.
  We need confidence intervals to know if we've truly violated SLA.
    """)

    # Generate requests with degradation at 7000
    requests = generate_api_requests(
        n_requests=10000,
        success_rate=0.995,
        degrade_at=7000,
        degraded_rate=0.98
    )

    # Setup SLA monitoring
    config = SLAConfig(
        name="api_success_rate",
        target_success_rate=0.995,
        window_minutes=1440,  # 24 hours
        alert_threshold=0.990  # Alert when confident we're below 99%
    )

    # Use Bernoulli-specific CS for binary outcomes
    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bernoulli",
        two_sided=True,
        name=config.name
    )

    cs = BernoulliCS(spec)

    print("\n⚙️  SLA Configuration:")
    print(f"  Target success rate: {config.target_success_rate:.3%}")
    print(f"  Alert threshold: {config.alert_threshold:.3%}")
    print(f"  Confidence level: 95%")
    print(f"  Method: Bernoulli-specific (optimal for binary data)")

    print("\n📊 Monitoring requests (every 1000 requests)...")
    print("\n" + "-" * 100)
    print(f"{'Requests':>10} | {'Success %':>12} | {'95% CI':>25} | {'SLA Status':>20}")
    print("-" * 100)

    sla_breached = False
    breach_time = None

    for i, success in enumerate(requests, start=1):
        cs.update(success)

        # Report every 1000 requests
        if i % 1000 == 0:
            iv = cs.interval()

            # Check SLA status
            ci_lower = iv.lo
            if ci_lower < config.alert_threshold:
                status = "🚨 SLA BREACH!"
                if not sla_breached:
                    sla_breached = True
                    breach_time = i
            elif ci_lower < config.target_success_rate:
                status = "⚠️  Below target"
            else:
                status = "✓ On track"

            print(f"{i:10d} | {iv.estimate:11.3%} | ({iv.lo:7.4f}, {iv.hi:7.4f}) | {status:>20}")

    # Final summary
    iv = cs.interval()

    print("\n" + "=" * 100)
    print("📈 SLA MONITORING SUMMARY")
    print("=" * 100)

    total_requests = iv.t
    total_successes = iv.estimate * iv.t
    total_failures = iv.t - total_successes

    print(f"\nTotal requests analyzed: {total_requests:,}")
    print(f"Successful requests: {int(total_successes):,}")
    print(f"Failed requests: {int(total_failures):,}")

    print(f"\nFinal success rate: {iv.estimate:.4%}")
    print(f"95% Confidence interval: ({iv.lo:.4%}, {iv.hi:.4%})")

    print(f"\nSLA Target: {config.target_success_rate:.3%}")
    print(f"Alert Threshold: {config.alert_threshold:.3%}")

    if sla_breached:
        print(f"\n⚠️  SLA ALERT triggered at request #{breach_time:,}")
        print(f"   We're 95% confident success rate < {config.alert_threshold:.3%}")
        print(f"   This may indicate service degradation!")

    # Calculate error budget
    error_budget = (1 - config.target_success_rate) * total_requests
    actual_errors = total_failures

    print(f"\n💰 Error Budget Analysis:")
    print(f"  Budgeted errors per {total_requests:,} requests: {error_budget:.1f}")
    print(f"  Actual errors: {actual_errors:.1f}")
    print(f"  Remaining budget: {error_budget - actual_errors:.1f}")

    if actual_errors > error_budget:
        print(f"  ⚠️  Over budget by {actual_errors - error_budget:.1f} errors!")

def demo_burn_rate_calculation():
    """
    Calculate burn rate for error budget.
    """
    print("\n" + "=" * 80)
    print("🔥 ERROR BUDGET BURN RATE")
    print("=" * 80)

    print("""
ERROR BUDGET BURN RATE:
  How fast are we consuming our error budget?

  Calculation:
    burn_rate = (current_error_rate) / (allowed_error_rate)

  Interpretation:
    • burn_rate = 1.0: On track to exhaust budget exactly
    • burn_rate > 1.0: Burning too fast, will breach SLA early
    • burn_rate < 1.0: Under budget, headroom available

EXAMPLE:
  SLA: 99.9% success (0.1% error rate allowed)
  Current: 99.5% success (0.5% error rate)
  Burn rate = 0.5% / 0.1% = 5.0x

  At this rate, we'll exhaust our 30-day budget in ~6 days!
    """)

    # Simulate burn rate calculation
    scenarios = [
        ("Excellent", 0.9995, 0.999),  # 99.95% vs 99.9% target
        ("Good", 0.9992, 0.999),      # 99.92% vs 99.9% target
        ("Warning", 0.9985, 0.999),   # 99.85% vs 99.9% target
        ("Critical", 0.9970, 0.999),  # 99.7% vs 99.9% target
    ]

    print("\n" + "-" * 90)
    print(f"{'Status':>12} | {'Current':>12} | {'Target':>12} | {'Burn Rate':>12} | {'Days Left':>12}")
    print("-" * 90)

    for status, current, target in scenarios:
        current_error_rate = 1 - current
        allowed_error_rate = 1 - target

        burn_rate = current_error_rate / allowed_error_rate if allowed_error_rate > 0 else 0

        # If burn rate > 1, we exhaust budget faster
        days_in_month = 30
        if burn_rate > 0:
            days_left = days_in_month / burn_rate
        else:
            days_left = days_in_month

        print(f"{status:>12} | {current:11.4%} | {target:11.4%} | {burn_rate:12.2f}x | {days_left:12.1f}")

    print("\n💡 Higher burn rate = exhausting error budget faster!")

def demo_comparison_period():
    """
    Demonstrate SLA comparison period monitoring.
    """
    print("\n" + "=" * 80)
    print("📅 COMPARISON PERIOD: Monthly SLA Reporting")
    print("=" * 80)

    print("""
SCENARIO:
  Monthly SLA compliance reporting.

  Setup:
    - 30-day comparison period
    - ~10 million requests per day
    - Need 99.9% uptime for the month
    - Report with confidence intervals

CHALLENGE:
  With millions of requests, even tiny error rates matter.
  Need precise confidence intervals to show compliance.
    """)

    # Simulate a month of data (scaled down for demo)
    days = 30
    requests_per_day = 10_000  # Scaled down for faster demo (300k total)
    target_rate = 0.999  # 99.9%

    # Slightly below target (realistic scenario)
    actual_rate = 0.9991  # 99.91%

    print("\n📊 Simulating 30-day month...")
    print(f"  Requests per day: {requests_per_day:,} (scaled down for demo)")
    print(f"  Target success rate: {target_rate:.3%}")
    print(f"  Actual success rate: {actual_rate:.3%}")

    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bernoulli",
        two_sided=True
    )

    cs = BernoulliCS(spec)

    print("\n" + "-" * 80)
    print(f"{'Day':>6} | {'Requests':>15} | {'Success Rate':>14} | {'95% CI':>20} | {'Status':>12}")
    print("-" * 80)

    for day in range(1, days + 1):
        # Generate one day of requests
        random.seed(day)
        day_requests = [1 if random.random() < actual_rate else 0
                       for _ in range(requests_per_day)]

        # Update confidence sequence
        for req in day_requests:
            cs.update(req)

        # Report weekly
        if day % 7 == 0 or day == days:
            iv = cs.interval()

            # Check SLA compliance
            if iv.lo >= target_rate:
                status = "✓ Compliant"
            elif iv.estimate >= target_rate:
                status = "⚠️  Uncertain"
            else:
                status = "🚨 Breach"

            print(f"{day:6d} | {iv.t:15,} | {iv.estimate:13.6%} | "
                  f"({iv.lo:.6%}, {iv.hi:.6%}) | {status:>12}")

    # Final report
    iv = cs.interval()

    print("\n" + "=" * 80)
    print("📋 MONTHLY SLA REPORT")
    print("=" * 80)

    print(f"\nPeriod: 30 days")
    print(f"Total requests: {iv.t:,}")
    print(f"Success rate: {iv.estimate:.6%}")
    print(f"95% Confidence interval: ({iv.lo:.6%}, {iv.hi:.6%})")
    print(f"SLA Target: {target_rate:.3%}")

    if iv.lo >= target_rate:
        print(f"\n✅ SLA COMPLIANT")
        print(f"   We are 95% confident the true success rate exceeds {target_rate:.3%}")
    elif iv.estimate >= target_rate:
        print(f"\n⚠️  UNCERTAIN")
        print(f"   Point estimate meets SLA but confidence interval includes failure")
    else:
        print(f"\n❌ SLA BREACH")
        print(f"   Success rate below target")

def demo_production_dashboard():
    """
    Show production SLA dashboard patterns.
    """
    print("\n" + "=" * 80)
    print("📺 PRODUCTION SLA DASHBOARD")
    print("=" * 80)

    print("""
Building an SLA dashboard with anytime-valid inference:

```python
# sla_dashboard.py

from anytime import StreamSpec
from anytime.cs import BernoulliCS
from flask import Flask, jsonify
import redis

app = Flask(__name__)

# Store SLA monitors in Redis for persistence
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class SLAMonitor:
    '''Monitor an SLA with anytime-valid confidence sequences.'''

    def __init__(self, name, target_rate, alpha=0.05):
        self.name = name
        self.target_rate = target_rate
        self.spec = StreamSpec(
            alpha=alpha,
            support=(0.0, 1.0),
            kind="bernoulli",
            two_sided=True,
            name=name
        )
        self.cs = BernoulliCS(self.spec)

    def update(self, success):
        '''Update with new observation.'''
        self.cs.update(success)
        return self.get_status()

    def get_status(self):
        '''Get current SLA status.'''
        iv = self.cs.interval()

        return {
            'name': self.name,
            'total_requests': iv.t,
            'success_rate': iv.estimate,
            'ci_lower': iv.lo,
            'ci_upper': iv.hi,
            'target_rate': self.target_rate,
            'compliant': iv.lo >= self.target_rate,
            'tier': iv.tier.value
        }

# Global monitors
monitors = {
    'api_success': SLAMonitor('api_success', 0.999),
    'db_success': SLAMonitor('db_success', 0.995),
    'cdn_success': SLAMonitor('cdn_success', 0.9999),
}

@app.route('/update/<service>/<int:success>')
def update_service(service, success):
    '''Update service status (called by your monitoring).'''
    if service in monitors:
        status = monitors[service].update(success)
        return jsonify(status)
    return jsonify({'error': 'Unknown service'}), 404

@app.route('/status')
def get_status():
    '''Get all service statuses.'''
    return jsonify({
        name: monitor.get_status()
        for name, monitor in monitors.items()
    })

@app.route('/dashboard')
def dashboard():
    '''Render dashboard (HTML).'''
    return render_template('sla_dashboard.html')
```

DASHBOARD TEMPLATE (HTML):
```html
<!-- sla_dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>SLA Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Fetch status every 10 seconds
        setInterval(async () => {
            const response = await fetch('/status');
            const data = await response.json();
            updateDashboard(data);
        }, 10000);

        function updateDashboard(services) {
            for (const [name, status] of Object.entries(services)) {
                updateServiceCard(name, status);
            }
        }

        function updateServiceCard(name, status) {
            const card = document.getElementById(`card-${name}`);
            const compliant = status.compliant;

            card.className = `card ${compliant ? 'compliant' : 'breach'}`;
            card.innerHTML = `
                <h3>${name}</h3>
                <p>Success Rate: ${(status.success_rate * 100).toFixed(4)}%</p>
                <p>95% CI: [${(status.ci_lower * 100).toFixed(4)}%,
                           ${(status.ci_upper * 100).toFixed(4)}%]</p>
                <p>Target: ${(status.target_rate * 100).toFixed(2)}%</p>
                <p class="status ${compliant ? 'compliant' : 'breach'}">
                    ${compliant ? '✓ COMPLIANT' : '🚨 BREACH'}
                </p>
                <p>Requests: ${status.total_requests.toLocaleString()}</p>
            `;
        }
    </script>
    <style>
        .card { border: 2px solid #ccc; padding: 20px; margin: 10px; }
        .compliant { background: #d4edda; }
        .breach { background: #f8d7da; }
        .status.compliant { color: green; font-weight: bold; }
        .status.breach { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>SLA Dashboard</h1>
    <div id="cards">
        <div id="card-api_success" class="card"></div>
        <div id="card-db_success" class="card"></div>
        <div id="card-cdn_success" class="card"></div>
    </div>
</body>
</html>
```

KEY FEATURES:
  ✓ Real-time updates every 10 seconds
  ✓ Visual compliant/breach indicators
  ✓ Confidence intervals show uncertainty
  ✓ Historical data persistence via Redis
  ✓ Simple Flask/HTML/JS stack

DEPLOYMENT:
  • Run with Gunicorn for production
  • Use Nginx as reverse proxy
  • Add authentication
  • Set up alerting (PagerDuty, Slack)
  • Configure retention policies
    """)

def main():
    print("=" * 80)
    print("📊 Service Level Agreement (SLA) Monitoring")
    print("=" * 80)

    print("""
This example demonstrates anytime-valid inference for SLA monitoring
and service level objective (SLO) tracking.

THE SLA CHALLENGE:

  SLAs are contractual obligations with real consequences:
    • Financial penalties for breaches
    • Customer trust implications
    • Legal requirements for accuracy
    • Need continuous monitoring

ANYTIME-VALID INFERENCE HELPS:

  ✓ Valid confidence intervals for success rates
  ✓ Continuous monitoring without penalty
  ✓ Clear breach detection with uncertainty quantified
  ✓ Burn rate calculations for error budgets
  ✓ Compliant reporting with statistical guarantees

EXAMPLES COVERED:
  1. API success rate monitoring
  2. Error budget burn rate calculation
  3. Monthly SLA compliance reporting
  4. Production dashboard setup

REAL-WORLD APPLICATIONS:
  • SRE/DevOps SLA monitoring
  • API uptime tracking
  • Cloud service guarantees
  • Customer-facing SLA dashboards
  • Internal SLO tracking

DATASETS IN PRODUCTION:
  • Load balancer logs (NGINX, HAProxy, Envoy)
  • API gateway metrics (Kong, AWS API Gateway)
  • Application monitoring (Prometheus, Datadog)
  • Cloud provider metrics (CloudWatch, Azure Monitor)
    """)

    # Run demonstrations
    demo_sla_monitoring()
    demo_burn_rate_calculation()
    demo_comparison_period()
    demo_production_dashboard()

    # Final summary
    print("\n" + "=" * 80)
    print("✅ SUMMARY")
    print("=" * 80)

    print("""
WHAT YOU LEARNED:
  ✓ SLA monitoring with confidence sequences
  ✓ Error budget and burn rate calculations
  ✓ Monthly compliance reporting
  ✓ Production dashboard patterns

KEY INSIGHTS:
  • Confidence intervals quantify SLA uncertainty
  • Burn rate shows how fast error budget depletes
  • Use Bernoulli CS for binary (success/failure) metrics
  • Alert on CI lower bound crossing threshold

PRODUCTION TIPS:
  ✓ Use Bernoulli-specific CS for optimal tightness
  ✓ Monitor burn rate to predict breaches early
  ✓ Report with CIs for transparency
  ✓ Set up automated alerting
  • Example 12: Currency monitoring
  • Example 15: Bandit optimization
  • Example 16: Time series monitoring

REFERENCES:
  • Google SRE Workbook (Chapter 5: Service Level Objectives)
  • "Site Reliability Engineering" (SRE Book)
  • "SLA Monitoring and Alerting" (O'Reilly)
    """)

if __name__ == "__main__":
    main()
