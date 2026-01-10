"""Streamlit demo for anytime inference."""

import math
import random

import streamlit as st
import matplotlib.pyplot as plt

from anytime.spec import ABSpec
from anytime.twosample.hoeffding import TwoSampleHoeffdingCS
from anytime.twosample.empirical_bernstein import TwoSampleEmpiricalBernsteinCS


st.set_page_config(page_title="Anytime Demo", page_icon="🔍", layout="wide")

st.title("🔍 Anytime Inference Demo")
st.markdown("""
Peek-safe streaming inference for A/B tests and online metrics.

This demo shows how confidence sequences maintain valid coverage even when
you continuously monitor and stop early.
""")

# Sidebar controls
st.sidebar.header("Configuration")

alpha = st.sidebar.slider("Significance level (α)", 0.01, 0.20, 0.05, 0.01)
p_control = st.sidebar.slider("Control conversion rate", 0.0, 1.0, 0.50, 0.01)
p_treatment = st.sidebar.slider("Treatment conversion rate", 0.0, 1.0, 0.55, 0.01)
method = st.sidebar.selectbox("Method", ["empirical_bernstein", "hoeffding"])
n_max = st.sidebar.slider("Max sample size", 100, 5000, 1000, 100)
look_interval = st.sidebar.slider("Check every n samples", 1, 100, 10)

st.sidebar.markdown("---")
st.sidebar.markdown("### Stopping Rules")
stop_when_positive = st.sidebar.checkbox("Stop when CI excludes 0 (positive effect)")
stop_when_negative = st.sidebar.checkbox("Stop when CI excludes 0 (negative effect)")
stop_when_narrow = st.sidebar.checkbox("Stop when width < threshold", value=False)
width_threshold = st.sidebar.slider("Width threshold", 0.01, 0.20, 0.05, 0.01)


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

# Main content
col1, col2 = st.columns(2)

with col1:
    st.subheader("Setup")
    st.markdown(f"""
    - **Control rate**: {p_control:.1%}
    - **Treatment rate**: {p_treatment:.1%}
    - **True lift**: {p_treatment - p_control:.1%}
    - **Method**: {method}
    - **Max samples**: {n_max:,}
    """)

    if st.button("Run Simulation", type="primary"):
        # Generate data
        rng = random.Random(42)
        control_data = [float(rng.random() < p_control) for _ in range(n_max)]
        treatment_data = [float(rng.random() < p_treatment) for _ in range(n_max)]

        # Track results
        times = []
        estimates = []
        los = []
        his = []
        widths = []
        p_values = []
        stopped_at = None
        naive_stop_at = None
        sum_a = 0.0
        sum_b = 0.0
        n_a = 0
        n_b = 0

        # Setup specs
        spec = ABSpec(
            alpha=alpha,
            support=(0.0, 1.0),
            kind="bernoulli",
            two_sided=True,
        )

        # Select method
        method_map = {
            "hoeffding": TwoSampleHoeffdingCS,
            "empirical_bernstein": TwoSampleEmpiricalBernsteinCS,
        }
        cs = method_map[method](spec)

        # Run simulation
        for i in range(n_max):
            cs.update(("A", control_data[i]))
            cs.update(("B", treatment_data[i]))

            sum_a += control_data[i]
            sum_b += treatment_data[i]
            n_a += 1
            n_b += 1

            iv = cs.interval()
            estimate = iv.estimate
            lo = iv.lo
            hi = iv.hi

            times.append(iv.t)
            estimates.append(estimate)
            los.append(lo)
            his.append(hi)
            widths.append(hi - lo)

            p_pool = (sum_a + sum_b) / (n_a + n_b)
            if p_pool in (0.0, 1.0):
                p_val = 1.0
            else:
                se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
                if se == 0.0:
                    p_val = 1.0
                else:
                    z = (sum_b / n_b - sum_a / n_a) / se
                    p_val = 2.0 * (1.0 - normal_cdf(abs(z)))
            p_values.append(p_val)

            # Check stopping rules
            if i % look_interval == 0:
                should_stop = False
                reason = None

                if stop_when_positive and lo > 0:
                    should_stop = True
                    reason = "Positive effect detected"
                elif stop_when_negative and hi < 0:
                    should_stop = True
                    reason = "Negative effect detected"
                elif stop_when_narrow and (hi - lo) < width_threshold:
                    should_stop = True
                    reason = f"Width < {width_threshold}"

                if should_stop:
                    stopped_at = iv.t
                    break

                if naive_stop_at is None and p_val < alpha:
                    naive_stop_at = iv.t

        # Store results in session state
        st.session_state.results = {
            "times": times,
            "estimates": estimates,
            "los": los,
            "his": his,
            "widths": widths,
            "p_values": p_values,
            "stopped_at": stopped_at,
            "naive_stop_at": naive_stop_at,
            "true_lift": p_treatment - p_control,
        }

with col2:
    st.subheader("Results")

    if "results" in st.session_state:
        r = st.session_state.results

        st.metric("True lift", f"{r['true_lift']:.1%}")
        st.metric("Final estimate", f"{r['estimates'][-1]:.1%}")
        st.metric("Final CI", f"[{r['los'][-1]:.1%}, {r['his'][-1]:.1%}]")
        st.metric("Naive p-value (final)", f"{r['p_values'][-1]:.3f}")

        if r['stopped_at']:
            st.success(f"✅ Stopped at t={r['stopped_at']:,} (peeking-safe!)")
        else:
            st.info(f"Reached max sample size (t={r['times'][-1]:,})")

        if r["naive_stop_at"]:
            st.warning(f"⚠️ Naive p-value would stop at t={r['naive_stop_at']:,}")

        # Check if true value is in CI
        true_covered = r['los'][-1] <= r['true_lift'] <= r['his'][-1]
        if true_covered:
            st.success("✅ True value is in final CI")
        else:
            st.error("❌ True value NOT in final CI (should be rare)")

# Plotting
if "results" in st.session_state:
    r = st.session_state.results

    st.subheader("Confidence Sequence Over Time")

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))

    # Plot 1: Lift estimate with CI
    ax1.fill_between(r['times'], r['los'], r['his'], alpha=0.3, label=f"{1-alpha:.0%} confidence band")
    ax1.plot(r['times'], r['estimates'], 'k-', label='Lift estimate', linewidth=1.5)
    ax1.axhline(y=r['true_lift'], color='r', linestyle='--', label='True lift', linewidth=1.5)
    ax1.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax1.set_xlabel('Sample size (t)')
    ax1.set_ylabel('Lift')
    ax1.set_title('Confidence Sequence for Lift')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    if r['stopped_at']:
        ax1.axvline(x=r['stopped_at'], color='green', linestyle=':', linewidth=2, label='Stopped')
        ax1.legend()

    # Plot 2: Width over time
    ax2.plot(r['times'], r['widths'], 'b-', linewidth=1.5)
    ax2.set_xlabel('Sample size (t)')
    ax2.set_ylabel('CI Width')
    ax2.set_title('Confidence Interval Width Over Time')
    ax2.grid(True, alpha=0.3)

    if r['stopped_at']:
        ax2.axvline(x=r['stopped_at'], color='green', linestyle=':', linewidth=2)

    # Plot 3: Naive p-value over time
    ax3.plot(r['times'], r['p_values'], 'm-', linewidth=1.5)
    ax3.axhline(y=alpha, color='r', linestyle='--', label=f"alpha={alpha:.2f}")
    ax3.set_xlabel('Sample size (t)')
    ax3.set_ylabel('Naive p-value')
    ax3.set_title('Naive p-value Under Peeking')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    if r['naive_stop_at']:
        ax3.axvline(x=r['naive_stop_at'], color='orange', linestyle=':', linewidth=2)

    plt.tight_layout()
    st.pyplot(fig)

# Explanation
st.markdown("---")
st.subheader("How it works")

st.markdown("""
### The peeking problem

Traditional p-values assume a fixed sample size and a single look at the data.
If you continuously monitor and stop early when you see a "significant" result,
your false positive rate inflates dramatically.

### The anytime solution

Confidence sequences and e-values maintain valid guarantees even with:
- **Continuous monitoring**: Look at the data whenever you want
- **Early stopping**: Stop when you have enough evidence
- **Optional stopping**: Change your sample size mid-experiment

The guarantees hold:
- **Confidence sequence**: P(θ is in C_t for all t) ≥ 1 - α
- **E-values**: P(∃t: E_t ≥ 1/α) ≤ α under H₀
""")
