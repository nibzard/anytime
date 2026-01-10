#!/usr/bin/env python3
"""
10_custom_datasets.py - Working with Real Datasets

ADVANCED

This example demonstrates how to work with real-world data sources including
CSV files, APIs, and streaming data pipelines. It shows practical patterns
for integrating anytime inference into production data workflows.

SCENARIO:
You're a data scientist working with various data sources:
1. CSV files from experiments
2. API responses from monitoring systems
3. Streaming data from Kafka/Kinesis
4. Database query results

You want to apply anytime inference to all of these sources.

CONCEPTS:
- Data adapters: Converting various formats to streaming format
- CSV parsing with pandas
- API polling patterns
- Stream processing
- Production data pipelines
"""

import sys
sys.path.insert(0, '..')

from anytime import StreamSpec, ABSpec
from anytime.cs import EmpiricalBernsteinCS
from anytime.evalues import TwoSampleMeanMixtureE
import random
import csv
from pathlib import Path

# ============================================================================
# DATA SOURCE ADAPTERS
# ============================================================================

class CSVAdapter:
    """Adapter for reading CSV files as streams."""

    def __init__(self, filepath, value_column, arm_column=None):
        self.filepath = filepath
        self.value_column = value_column
        self.arm_column = arm_column

    def stream(self):
        """Yield values (or arm-value pairs) from CSV."""
        with open(self.filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                value = float(row[self.value_column])

                if self.arm_column:
                    yield (row[self.arm_column], value)
                else:
                    yield value

class MockAPIAdapter:
    """Adapter simulating API polling for metrics."""

    def __init__(self, endpoint_url, poll_interval=1.0):
        self.endpoint_url = endpoint_url
        self.poll_interval = poll_interval
        self._iteration = 0

    def stream(self, n_samples=100):
        """Simulate polling an API for metrics."""
        for _ in range(n_samples):
            # Simulate API call delay
            # time.sleep(self.poll_interval)

            # Simulate API response with some noise
            base_value = 0.50 + random.uniform(-0.05, 0.05)
            yield base_value

class DatabaseAdapter:
    """Adapter for database query results."""

    def __init__(self, query_result):
        self.query_result = query_result

    def stream(self):
        """Stream results from a database query."""
        for row in self.query_result:
            yield row['metric_value']

# ============================================================================
# DEMO FUNCTIONS
# ============================================================================

def demo_csv_adapter():
    """Demonstrate working with CSV files."""
    print("\n" + "=" * 70)
    print("DEMO 1: Working with CSV Files")
    print("=" * 70)

    # First, create a sample CSV file
    csv_path = Path(__file__).resolve().parent / "datasets" / "conversions.csv"
    csv_path.parent.mkdir(exist_ok=True)

    print(f"\nCreating sample CSV: {csv_path}")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'user_id', 'converted', 'variant'])
        random.seed(555)
        for i in range(500):
            timestamp = f"2024-01-{(i // 50) + 1:02d}"
            user_id = f"user_{i}"
            variant = random.choice(['A', 'B'])
            # B has slightly higher conversion rate
            rate = 0.52 if variant == 'B' else 0.48
            converted = 1 if random.random() < rate else 0
            writer.writerow([timestamp, user_id, converted, variant])

    print("✓ CSV file created")

    # Now read and process the CSV
    print("\nProcessing CSV with anytime inference...")

    spec = ABSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=False,
        name="csv_ab_test"
    )

    etest = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")

    # Use the adapter
    adapter = CSVAdapter(csv_path, value_column='converted', arm_column='variant')

    for arm, value in adapter.stream():
        etest.update((arm, value))

    ev = etest.evalue()
    print(f"\nResults from CSV data:")
    print(f"  Final e-value: {ev.e:.2f}")
    print(f"  Decision: {'Reject H0' if ev.decision else 'Cannot reject'}")

def demo_api_adapter():
    """Demonstrate working with API data."""
    print("\n" + "=" * 70)
    print("DEMO 2: Working with API Data")
    print("=" * 70)

    print("\nSimulating API polling pattern...")

    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True,
        name="api_metrics"
    )

    cs = EmpiricalBernsteinCS(spec)

    # Simulate polling an API
    adapter = MockAPIAdapter("https://api.example.com/metrics")

    print(f"Polling API endpoint (simulated)...")
    print(f"\n{'Sample':>8} | {'Value':>8} | {'95% CI':>18} | {'Width':>8}")
    print("-" * 55)

    for i, value in enumerate(adapter.stream(n_samples=200), start=1):
        cs.update(value)

        if i % 40 == 0:
            iv = cs.interval()
            print(f"{i:8d} | {value:8.3f} | ({iv.lo:.3f}, {iv.hi:.3f}) | "
                  f"{iv.hi - iv.lo:8.3f}")

    print("\n✓ API polling complete")

def demo_streaming_pattern():
    """Demonstrate streaming data pattern."""
    print("\n" + "=" * 70)
    print("DEMO 3: Streaming Data Pattern")
    print("=" * 70)

    print("""
Real-world streaming pattern (e.g., Kafka, Kinesis):

```python
from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS
import json

def kafka_consumer(topic):
    '''Consume messages from Kafka topic.'''
    consumer = KafkaConsumer(topic)
    for message in consumer:
        data = json.loads(message.value)
        yield data['metric_value']

def monitor_streaming_metrics(topic, alert_threshold=0.45):
    '''Monitor metrics from Kafka with confidence sequences.'''
    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True
    )

    cs = EmpiricalBernsteinCS(spec)

    for value in kafka_consumer(topic):
        cs.update(value)
        iv = cs.interval()

        # Alert if entire CI is below threshold
        if iv.hi < alert_threshold:
            send_alert(f"Metric degraded: CI=({iv.lo:.3f}, {iv.hi:.3f})")

        # Log progress periodically
        if iv.t % 100 == 0:
            log_metric(iv.t, iv.estimate, iv.lo, iv.hi)

# Usage
monitor_streaming_metrics('production_metrics')
```

KEY INSIGHTS FOR STREAMING:
  • Process each observation as it arrives
  • Update confidence sequence incrementally
  • No need to store all historical data
  • Can stop and make decisions at any time
    """)

def demo_batch_processing():
    """Demonstrate batch processing pattern."""
    print("\n" + "=" * 70)
    print("DEMO 4: Batch Processing Pattern")
    print("=" * 70)

    print("""
Batch processing pattern for historical data:

```python
from anytime import StreamSpec
from anytime.cs import HoeffdingCS
import pandas as pd

def analyze_batch_experiment(data_path):
    '''Analyze a completed experiment from CSV/Parquet.'''
    # Load data
    df = pd.read_csv(data_path)

    # Setup
    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True
    )

    cs = HoeffdingCS(spec)

    # Process all rows
    for _, row in df.iterrows():
        cs.update(row['metric_value'])

    # Get final results
    iv = cs.interval()

    # Report
    print(f"Final estimate: {iv.estimate:.3f}")
    print(f"95% CI: ({iv.lo:.3f}, {iv.hi:.3f})")
    print(f"Total samples: {iv.t}")
    print(f"Guarantee tier: {iv.tier.value}")

    return iv

# Usage
result = analyze_batch_experiment('experiment_results.csv')
```

WHEN TO USE BATCH VS STREAMING:
  • Batch: Historical analysis, one-time reports
  • Streaming: Real-time monitoring, continuous experiments
    """)

# ============================================================================
# MAIN DEMO
# ============================================================================

def main():
    print("=" * 70)
    print("Working with Real Datasets and Data Sources")
    print("=" * 70)

    print("""
This example demonstrates practical patterns for integrating anytime
inference into your data pipeline, regardless of where your data comes from.

DATA SOURCES COVERED:
  1. CSV files (local experiments)
  2. API responses (polling pattern)
  3. Streaming platforms (Kafka, Kinesis)
  4. Database queries (batch processing)
    """)

    # Run demos
    demo_csv_adapter()
    demo_api_adapter()
    demo_streaming_pattern()
    demo_batch_processing()

    # SUMMARY
    print("\n" + "=" * 70)
    print("SUMMARY: Production Data Patterns")
    print("=" * 70)

    print("""
UNIFIED INTERFACE:
  All data sources work with the same anytime API:
  1. Create spec (StreamSpec or ABSpec)
  2. Initialize method (CS or e-value)
  3. Stream: for value in data_source: cs.update(value)
  4. Query: iv = cs.interval() or ev = etest.evalue()

BEST PRACTICES:
  ✓ Use adapters to normalize different data sources
  ✓ Handle missing/bad data before updating CS
  ✓ Log guarantee tier and diagnostics
  ✓ Set up alerts for assumption violations
  ✓ Use checkpointing for long-running streams

PRODUCTION TIPS:
  • For CSV: Process in chunks for large files
  • For APIs: Implement retry logic and rate limiting
  • For streaming: Use windowed summaries for dashboards
  • For databases: Use server-side cursors for large queries

COMMON INTEGRATION POINTS:
  • Airflow DAGs: Batch experiment analysis
  • Streamlit apps: Interactive monitoring dashboards
  • Grafana: Visualize confidence intervals over time
  • Alerting: Send alerts when CI crosses thresholds
  • ML pipelines: Feature selection with anytime tests
    """)

if __name__ == "__main__":
    main()
