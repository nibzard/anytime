# Anytime Examples

Welcome to the **friendliest** introduction to anytime-valid inference! These examples are designed to take you from zero to confident user in about 30 minutes.

## 🚀 Where to Start?

**Never heard of anytime inference?** Start here:
1. `00_super_simple.py` - **The simplest possible start** (5 min)

**Know the basics?** Jump to the beginner series:
2. `01_hello_anytime.py` - Your first confidence sequence
3. `02_bernoulli_exact.py` - Binary data (coin flips)
4. `03_ab_test_simple.py` - A/B testing with e-values
5. `04_streaming_monitor.py` - Real-time monitoring

---

## 📚 All Examples by Difficulty

### 🟢 Beginner (Start Here)

| File | Time | Description |
|------|------|-------------|
| [`00_super_simple.py`](00_super_simple.py) | 5 min | **NEW!** Simplest possible start. Track sign-ups with 3 lines of code. |
| [`01_hello_anytime.py`](01_hello_anytime.py) | 10 min | Your first confidence sequence. Monitor conversion rates and stop early. |
| [`02_bernoulli_exact.py`](02_bernoulli_exact.py) | 10 min | Binary data? Use BernoulliCS for tighter intervals. Test coin fairness! |
| [`03_ab_test_simple.py`](03_ab_test_simple.py) | 10 min | A/B testing with e-values. Stop when you have evidence. |
| [`04_streaming_monitor.py`](04_streaming_monitor.py) | 10 min | Real-time monitoring dashboard. Track metrics live with confidence. |

**Total beginner time: ~45 minutes**

---

### 🟡 Intermediate (Ready for More?)

| File | Time | Description |
|------|------|-------------|
| [`05_variance_adaptive.py`](05_variance_adaptive.py) | 15 min | Hoeffding vs EmpiricalBernstein. When to use each method. |
| [`06_two_sample_cs.py`](06_two_sample_cs.py) | 15 min | Confidence intervals for mean differences. "How much better is B?" |
| [`07_early_stopping.py`](07_early_stopping.py) | 15 min | Optimal stopping rules. Save time and money with early decisions. |

**Total intermediate time: ~45 minutes**

---

### 🔵 Advanced (Production Ready)

| File | Time | Description |
|------|------|-------------|
| [`08_multiple_comparisons.py`](08_multiple_comparisons.py) | 20 min | Testing multiple variants? Control error rates properly. |
| [`09_diagnostic_checks.py`](09_diagnostic_checks.py) | 20 min | Production monitoring. Detect assumption violations. |
| [`10_custom_datasets.py`](10_custom_datasets.py) | 20 min | CSV, API, streaming. Real data pipelines. |
| [`11_real_world_data.py`](11_real_world_data.py) | 20 min | Real UCI mushroom dataset. Production patterns. |
| [`12_currency_monitoring.py`](12_currency_monitoring.py) | 10 min | **NEW!** Financial metrics. Exchange rates, stock tracking. |
| [`13_retail_analytics.py`](13_retail_analytics.py) | 15 min | **NEW!** E-commerce. Price testing, A/B optimization. |
| [`14_medical_trials.py`](14_medical_trials.py) | 15 min | **NEW!** Clinical trials. Vaccine efficacy, safety. |
| [`15_bandit_optimization.py`](15_bandit_optimization.py) | 20 min | **NEW!** Multi-armed bandit. Exploration vs exploitation. |
| [`16_time_series.py`](16_time_series.py) | 15 min | **NEW!** Time series monitoring. Confidence bands, anomalies. |
| [`17_sla_monitoring.py`](17_sla_monitoring.py) | 15 min | **NEW!** SLA/SRE monitoring. Error budgets, uptime. |

**Total advanced time: ~2.5 hours**

---

## 🎯 Learning Path

### Path 1: Quick Start (25 min)
```
00_super_simple.py → 01_hello_anytime.py → 03_ab_test_simple.py
```

### Path 2: Complete Beginner (45 min)
```
00_super_simple.py → 01 → 02 → 03 → 04
```

### Path 3: Full Mastery (4 hours)
```
Beginner (00-04) → Intermediate (05-07) → Advanced (08-17)
```

### Path 4: Domain-Specific Tracks
```
🏦 Finance           → 12 (Currency monitoring)
🛍️  E-Commerce      → 13 (Retail analytics)
💉 Healthcare        → 14 (Medical trials)
🎰 Optimization     → 15 (Bandit algorithms)
📊 Time Series      → 16 (Monitoring, anomalies)
🔧 SRE/SLO          → 17 (SLA monitoring)
```

---

## 💻 Running Examples

Each example is **self-contained** and runnable:

```bash
# From repo root
python3 examples/00_super_simple.py

# Or from examples folder
cd examples
python3 00_super_simple.py
```

**No installation needed** if you've installed the anytime package:
```bash
pip install -e .
```

---

## 📁 Datasets

The `datasets/` folder contains sample data:

| File | Description | Source |
|------|-------------|--------|
| `mushroom.data` | 8,124 mushroom samples (edible/poisonous) | [UCI ML Repository](https://archive.ics.uci.edu/ml/datasets/mushroom) |
| `conversions.csv` | Synthetic A/B test conversion data | Generated |
| `ab_test_results.csv` | Full A/B test simulation | Generated |
| `coin_flips.csv` | Coin flip sequences | Generated |
| `metrics_stream.csv` | Time-series metrics | Generated |

---

## 🌟 What Makes These Examples Special?

- ✅ **Zero jargon** - Every term explained in plain English
- ✅ **Real scenarios** - Website metrics, A/B tests, monitoring
- ✅ **Copy-paste ready** - Use code directly in your projects
- ✅ **Visual output** - Tables and charts you can understand
- ✅ **Progressive difficulty** - Start simple, go at your pace
- ✅ **Production patterns** - Advanced examples show real-world usage

---

## 🎓 Key Concepts You'll Learn

| Concept | Learn In | Why It Matters |
|---------|----------|----------------|
| Confidence Sequences | 01, 02 | Valid intervals, even with peeking |
| E-values | 03 | Optional stopping without breaking statistics |
| Variance Adaptation | 05 | Tighter intervals when variance is low |
| Mean Differences | 06 | "How much better?" not just "is it better?" |
| Early Stopping | 07 | Save time, stop experiments early |
| Error Control | 08 | Test multiple variants correctly |
| Diagnostics | 09 | Production-ready monitoring |
| Data Pipelines | 10, 11 | Real-world data integration |
| **Financial Monitoring** | **12** | **Exchange rates, stock tracking** |
| **E-Commerce Analytics** | **13** | **Price testing, A/B tests** |
| **Clinical Trials** | **14** | **Vaccine efficacy, safety** |
| **Bandit Algorithms** | **15** | **Exploration vs exploitation** |
| **Time Series Bands** | **16** | **Dynamic confidence intervals** |
| **SLA Monitoring** | **17** | **Error budgets, uptime** |

---

## 🚧 Need Help?

- **Stuck on an example?** Each file has detailed inline comments
- **Want more theory?** Check the main [README.md](../README.md)
- **Found a bug?** Open an issue on GitHub

---

## 📊 Example Output Preview

```
============================================================
🚀 Super Simple Start: Monitoring Sign-Ups
============================================================

Day 1: 47/100 signed up (47.0%)
        → We're 95% confident the true rate is: 21.1% to 72.9%

Day 2: 39/100 signed up (39.0%)
        → We're 95% confident the true rate is: 23.8% to 62.2%

...

📈 FINAL RESULTS
Total visitors:  700
Total sign-ups:  278
Actual rate:     39.7%

95% Confidence Interval:
  Lower bound:   28.6%
  Point estimate: 39.7%
  Upper bound:   50.8%
```

---

**Ready to dive in?** Start with [`00_super_simple.py`](00_super_simple.py) and see how easy anytime-valid inference can be!
