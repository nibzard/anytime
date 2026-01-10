"""Streamlit demo for anytime inference."""

import math
import random
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from scipy import stats

from anytime.spec import StreamSpec, ABSpec
from anytime.cs.hoeffding import HoeffdingCS
from anytime.cs.empirical_bernstein import EmpiricalBernsteinCS
from anytime.cs.bernoulli_exact import BernoulliCS
from anytime.twosample.hoeffding import TwoSampleHoeffdingCS
from anytime.twosample.empirical_bernstein import TwoSampleEmpiricalBernsteinCS
from anytime.evalues.bernoulli import BernoulliMixtureE
from anytime.evalues.twosample import TwoSampleMeanMixtureE
from anytime.errors import AssumptionViolationError
from anytime.core.estimators import OnlineVariance
from anytime.io import read_one_sample_csv, read_ab_test_csv
from anytime.atlas.runner import AtlasRunner
from anytime.atlas.types import Scenario, StoppingRule
from anytime.atlas.report import generate_comparison_report
from anytime.config import load_yaml_config, validate_atlas_config


st.set_page_config(page_title="Anytime Demo", page_icon="🔍", layout="wide")

st.title("🔍 Anytime Inference Demo")
st.markdown(
    """
Peek-safe streaming inference for A/B tests and online metrics.

This demo shows how confidence sequences and e-values maintain valid guarantees
under continuous monitoring and optional stopping.
"""
)

SUPPORT = (0.0, 1.0)
DEFAULT_SEED = 42


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def beta_params(mean: float, concentration: float) -> tuple[float, float]:
    mean = clamp(mean, 1e-6, 1.0 - 1e-6)
    concentration = max(concentration, 1e-3)
    alpha = mean * concentration
    beta = (1.0 - mean) * concentration
    return alpha, beta


def drifted_value(base: float, delta: float, step: int, total: int) -> float:
    if delta == 0.0:
        return base
    frac = step / max(1, total - 1)
    return base + delta * frac


def inject_anomalies(
    x: float,
    rng: random.Random,
    missing_rate: float,
    out_of_range_rate: float,
    support: tuple[float, float],
) -> float:
    if missing_rate > 0.0 and rng.random() < missing_rate:
        return float("nan")
    if out_of_range_rate > 0.0 and rng.random() < out_of_range_rate:
        lo, hi = support
        span = hi - lo
        bump = 0.2 * span if span > 0 else 1.0
        return hi + bump if rng.random() < 0.5 else lo - bump
    return x


def sanitize_for_naive(
    x: float, support: tuple[float, float], clip_mode: str
) -> float | None:
    if not math.isfinite(x):
        return None
    lo, hi = support
    if x < lo:
        return lo if clip_mode == "clip" else None
    if x > hi:
        return hi if clip_mode == "clip" else None
    return x


def ttest_pvalue(mean: float, var: float, n: int, null_value: float) -> float:
    if n < 2:
        return 1.0
    if var <= 0.0:
        return 1.0
    se = math.sqrt(var / n)
    if se == 0.0:
        return 1.0
    t_stat = (mean - null_value) / se
    return float(2.0 * stats.t.sf(abs(t_stat), n - 1))


def welch_pvalue(
    mean_a: float,
    var_a: float,
    n_a: int,
    mean_b: float,
    var_b: float,
    n_b: int,
) -> float:
    if n_a < 2 or n_b < 2:
        return 1.0
    se_sq = var_a / n_a + var_b / n_b
    if se_sq <= 0.0:
        return 1.0
    t_stat = (mean_b - mean_a) / math.sqrt(se_sq)
    denom = 0.0
    if n_a > 1:
        denom += (var_a ** 2) / (n_a ** 2 * (n_a - 1))
    if n_b > 1:
        denom += (var_b ** 2) / (n_b ** 2 * (n_b - 1))
    df = (se_sq ** 2) / denom if denom > 0 else n_a + n_b - 2
    return float(2.0 * stats.t.sf(abs(t_stat), df))


def render_plots(results: dict) -> None:
    times = results.get("times", [])
    if not times:
        st.info("No valid observations were processed.")
        return

    plots = 2
    if results.get("p_values"):
        plots += 1
    if results.get("evalues"):
        plots += 1

    fig, axes = plt.subplots(plots, 1, figsize=(12, 4 * plots))
    if plots == 1:
        axes = [axes]

    idx = 0
    # Plot CS band
    ax = axes[idx]
    idx += 1
    ax.fill_between(times, results["los"], results["his"], alpha=0.3)
    ax.plot(times, results["estimates"], "k-", linewidth=1.5)
    if results.get("true_value") is not None:
        ax.axhline(y=results["true_value"], color="r", linestyle="--", label="True value")
    if results.get("null_value") is not None:
        ax.axhline(y=results["null_value"], color="gray", linestyle=":", label="Null")
    if results.get("stopped_at"):
        ax.axvline(x=results["stopped_at"], color="green", linestyle=":", linewidth=2)
    ax.set_xlabel("Samples (t)")
    ax.set_ylabel(results.get("value_label", "Value"))
    ax.set_title(results.get("cs_title", "Confidence Sequence"))
    ax.grid(True, alpha=0.3)
    if results.get("true_value") is not None or results.get("null_value") is not None:
        ax.legend()

    # Width plot
    ax = axes[idx]
    idx += 1
    ax.plot(times, results["widths"], "b-", linewidth=1.5)
    if results.get("stopped_at"):
        ax.axvline(x=results["stopped_at"], color="green", linestyle=":", linewidth=2)
    ax.set_xlabel("Samples (t)")
    ax.set_ylabel("CI Width")
    ax.set_title("Interval Width Over Time")
    ax.grid(True, alpha=0.3)

    # Naive p-values
    if results.get("p_values"):
        ax = axes[idx]
        idx += 1
        ax.plot(times, results["p_values"], "m-", linewidth=1.5)
        ax.axhline(y=results["alpha"], color="r", linestyle="--", label=f"alpha={results['alpha']:.2f}")
        if results.get("naive_stop_at"):
            ax.axvline(x=results["naive_stop_at"], color="orange", linestyle=":", linewidth=2)
        ax.set_xlabel("Samples (t)")
        ax.set_ylabel("Naive p-value")
        ax.set_title("Naive p-value Under Peeking")
        ax.legend()
        ax.grid(True, alpha=0.3)

    # E-values
    if results.get("evalues"):
        ax = axes[idx]
        ax.plot(results["e_times"], results["evalues"], "g-", linewidth=1.5)
        threshold = 1.0 / results["alpha"]
        ax.axhline(y=threshold, color="r", linestyle="--", label=f"1/alpha={threshold:.1f}")
        ax.set_xlabel("Samples (t)")
        ax.set_ylabel("E-value")
        ax.set_title("E-value Over Time")
        ax.set_yscale("log")
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig)


def display_results(results: dict) -> None:
    if results.get("error"):
        st.error(results["error"])

    if not results.get("times"):
        st.info("No valid observations were processed.")
        return

    final = results.get("final", {})
    st.subheader("Results")

    st.metric("Final estimate", f"{final.get('estimate', 0.0):.4f}")
    st.metric("Final CI", f"[{final.get('lo', 0.0):.4f}, {final.get('hi', 0.0):.4f}]")

    if results.get("true_value") is not None:
        st.metric("True value", f"{results['true_value']:.4f}")

    if results.get("p_values"):
        st.metric("Naive p-value (final)", f"{results['p_values'][-1]:.4f}")

    if results.get("final_evalue"):
        ev = results["final_evalue"]
        st.metric("Final e-value", f"{ev['e']:.3f}")
        if ev["decision"]:
            st.success("E-value crossed the decision threshold.")

    if results.get("stopped_at"):
        st.success(f"Stopped at t={results['stopped_at']:,} ({results.get('stop_reason', 'rule')})")
    else:
        st.info(f"Reached max sample size (t={results['times'][-1]:,})")

    if results.get("naive_stop_at"):
        st.warning(f"Naive p-value would stop at t={results['naive_stop_at']:,}")

    diagnostics = results.get("diagnostics")
    if diagnostics:
        st.subheader("Diagnostics")
        st.json(diagnostics)

    evalue_diagnostics = results.get("evalue_diagnostics")
    if evalue_diagnostics:
        st.subheader("E-value Diagnostics")
        st.json(evalue_diagnostics)

    if results.get("csv_summary"):
        st.subheader("CSV Summary")
        st.json(results["csv_summary"])

    render_plots(results)


def run_one_sample_sim(
    kind: str,
    method_name: str,
    true_mean: float,
    null_value: float,
    n_max: int,
    alpha: float,
    two_sided: bool,
    clip_mode: str,
    missing_rate: float,
    out_of_range_rate: float,
    drift_delta: float,
    concentration: float,
    show_naive: bool,
    show_evalues: bool,
    evalue_side: str,
    seed: int,
    look_interval: int,
    stop_when_positive: bool,
    stop_when_negative: bool,
    stop_when_narrow: bool,
    width_threshold: float,
) -> dict:
    spec = StreamSpec(
        alpha=alpha,
        support=SUPPORT,
        kind=kind,
        two_sided=two_sided,
        clip_mode=clip_mode,
    )

    method_map = {
        "hoeffding": HoeffdingCS,
        "empirical_bernstein": EmpiricalBernsteinCS,
    }
    if kind == "bernoulli":
        method_map["bernoulli_exact"] = BernoulliCS

    cs = method_map[method_name](spec)

    eproc = None
    if show_evalues and kind == "bernoulli":
        eproc = BernoulliMixtureE(spec, p0=null_value, side=evalue_side)

    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    times = []
    estimates = []
    los = []
    his = []
    widths = []
    p_values = []
    evalues = []
    e_times = []
    error = None
    stopped_at = None
    stop_reason = None
    naive_stop_at = None
    naive_stop_at = None

    naive_var = OnlineVariance() if show_naive else None
    last_iv = None
    last_ev = None

    for i in range(n_max):
        if kind == "bernoulli":
            p_i = clamp(drifted_value(true_mean, drift_delta, i, n_max), 0.0, 1.0)
            x = 1.0 if rng.random() < p_i else 0.0
        else:
            mean_i = clamp(drifted_value(true_mean, drift_delta, i, n_max), 0.0, 1.0)
            alpha_b, beta_b = beta_params(mean_i, concentration)
            x = float(np_rng.beta(alpha_b, beta_b))

        x = inject_anomalies(x, rng, missing_rate, out_of_range_rate, SUPPORT)

        try:
            cs.update(x)
            if eproc:
                eproc.update(x)
        except AssumptionViolationError as exc:
            error = str(exc)
            break

        iv = cs.interval()
        if iv.t <= 0:
            continue

        if show_naive and naive_var is not None:
            x_naive = sanitize_for_naive(x, SUPPORT, clip_mode)
            if x_naive is not None:
                naive_var.update(x_naive)

        if not times or iv.t != times[-1]:
            times.append(iv.t)
            estimates.append(iv.estimate)
            los.append(iv.lo)
            his.append(iv.hi)
            widths.append(iv.width)
            last_iv = iv

            if show_naive and naive_var is not None:
                p_val = ttest_pvalue(
                    naive_var.mean, naive_var.variance, naive_var.n, null_value
                )
                p_values.append(p_val)
                if naive_stop_at is None and p_val < alpha:
                    naive_stop_at = iv.t

            if eproc:
                ev = eproc.evalue()
                last_ev = ev
                evalues.append(ev.e)
                e_times.append(ev.t)

        if iv.t % look_interval == 0:
            if stop_when_positive and iv.lo > null_value:
                stopped_at = iv.t
                stop_reason = "positive effect"
                break
            if stop_when_negative and iv.hi < null_value:
                stopped_at = iv.t
                stop_reason = "negative effect"
                break
            if stop_when_narrow and iv.width < width_threshold:
                stopped_at = iv.t
                stop_reason = f"width < {width_threshold}"
                break

    if last_iv is None:
        last_iv = cs.interval()

    result = {
        "mode": "one_sample",
        "times": times,
        "estimates": estimates,
        "los": los,
        "his": his,
        "widths": widths,
        "p_values": p_values if show_naive else None,
        "evalues": evalues if evalues else None,
        "e_times": e_times if evalues else None,
        "alpha": alpha,
        "true_value": true_mean,
        "null_value": null_value,
        "stopped_at": stopped_at,
        "stop_reason": stop_reason,
        "naive_stop_at": naive_stop_at,
        "error": error,
        "value_label": "Mean",
        "cs_title": "Confidence Sequence for Mean",
        "final": {
            "estimate": last_iv.estimate,
            "lo": last_iv.lo,
            "hi": last_iv.hi,
        },
        "diagnostics": last_iv.diagnostics.to_dict() if last_iv.diagnostics else None,
    }

    if last_ev is not None:
        result["final_evalue"] = {
            "t": last_ev.t,
            "e": last_ev.e,
            "decision": last_ev.decision,
        }
        result["evalue_diagnostics"] = (
            last_ev.diagnostics.to_dict() if last_ev.diagnostics else None
        )

    return result


def run_two_sample_sim(
    kind: str,
    method_name: str,
    mean_a: float,
    mean_b: float,
    null_value: float,
    n_max: int,
    alpha: float,
    two_sided: bool,
    clip_mode: str,
    missing_rate: float,
    out_of_range_rate: float,
    drift_delta: float,
    concentration_a: float,
    concentration_b: float,
    show_naive: bool,
    show_evalues: bool,
    evalue_side: str,
    seed: int,
    look_interval: int,
    stop_when_positive: bool,
    stop_when_negative: bool,
    stop_when_narrow: bool,
    width_threshold: float,
) -> dict:
    spec = ABSpec(
        alpha=alpha,
        support=SUPPORT,
        kind=kind,
        two_sided=two_sided,
        clip_mode=clip_mode,
    )

    method_map = {
        "hoeffding": TwoSampleHoeffdingCS,
        "empirical_bernstein": TwoSampleEmpiricalBernsteinCS,
    }
    cs = method_map[method_name](spec)

    eproc = None
    if show_evalues:
        eproc = TwoSampleMeanMixtureE(spec, delta0=null_value, side=evalue_side)

    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    times = []
    estimates = []
    los = []
    his = []
    widths = []
    p_values = []
    evalues = []
    e_times = []
    error = None
    stopped_at = None
    stop_reason = None

    naive_var_a = OnlineVariance() if show_naive else None
    naive_var_b = OnlineVariance() if show_naive else None
    last_iv = None
    last_ev = None

    for i in range(n_max):
        if kind == "bernoulli":
            p_a = clamp(mean_a, 0.0, 1.0)
            p_b = clamp(drifted_value(mean_b, drift_delta, i, n_max), 0.0, 1.0)
            x_a = 1.0 if rng.random() < p_a else 0.0
            x_b = 1.0 if rng.random() < p_b else 0.0
        else:
            mean_a_i = clamp(mean_a, 0.0, 1.0)
            mean_b_i = clamp(drifted_value(mean_b, drift_delta, i, n_max), 0.0, 1.0)
            alpha_a, beta_a = beta_params(mean_a_i, concentration_a)
            alpha_b, beta_b = beta_params(mean_b_i, concentration_b)
            x_a = float(np_rng.beta(alpha_a, beta_a))
            x_b = float(np_rng.beta(alpha_b, beta_b))

        x_a = inject_anomalies(x_a, rng, missing_rate, out_of_range_rate, SUPPORT)
        x_b = inject_anomalies(x_b, rng, missing_rate, out_of_range_rate, SUPPORT)

        try:
            cs.update(("A", x_a))
            cs.update(("B", x_b))
            if eproc:
                eproc.update(("A", x_a))
                eproc.update(("B", x_b))
        except AssumptionViolationError as exc:
            error = str(exc)
            break

        if show_naive and naive_var_a and naive_var_b:
            x_a_naive = sanitize_for_naive(x_a, SUPPORT, clip_mode)
            x_b_naive = sanitize_for_naive(x_b, SUPPORT, clip_mode)
            if x_a_naive is not None:
                naive_var_a.update(x_a_naive)
            if x_b_naive is not None:
                naive_var_b.update(x_b_naive)

        iv = cs.interval()
        if iv.t <= 0:
            continue

        times.append(iv.t)
        estimates.append(iv.estimate)
        los.append(iv.lo)
        his.append(iv.hi)
        widths.append(iv.width)
        last_iv = iv

        if show_naive and naive_var_a and naive_var_b:
            p_val = welch_pvalue(
                naive_var_a.mean,
                naive_var_a.variance,
                naive_var_a.n,
                naive_var_b.mean,
                naive_var_b.variance,
                naive_var_b.n,
            )
            p_values.append(p_val)
            if naive_stop_at is None and p_val < alpha:
                naive_stop_at = iv.t

        if eproc:
            ev = eproc.evalue()
            last_ev = ev
            evalues.append(ev.e)
            e_times.append(ev.t * 2)

        if iv.t % look_interval == 0:
            if stop_when_positive and iv.lo > null_value:
                stopped_at = iv.t
                stop_reason = "positive effect"
                break
            if stop_when_negative and iv.hi < null_value:
                stopped_at = iv.t
                stop_reason = "negative effect"
                break
            if stop_when_narrow and iv.width < width_threshold:
                stopped_at = iv.t
                stop_reason = f"width < {width_threshold}"
                break

    if last_iv is None:
        last_iv = cs.interval()

    result = {
        "mode": "two_sample",
        "times": times,
        "estimates": estimates,
        "los": los,
        "his": his,
        "widths": widths,
        "p_values": p_values if show_naive else None,
        "evalues": evalues if evalues else None,
        "e_times": e_times if evalues else None,
        "alpha": alpha,
        "true_value": mean_b - mean_a,
        "null_value": null_value,
        "stopped_at": stopped_at,
        "stop_reason": stop_reason,
        "naive_stop_at": naive_stop_at,
        "error": error,
        "value_label": "Lift",
        "cs_title": "Confidence Sequence for Lift",
        "final": {
            "estimate": last_iv.estimate,
            "lo": last_iv.lo,
            "hi": last_iv.hi,
        },
        "diagnostics": last_iv.diagnostics.to_dict() if last_iv.diagnostics else None,
    }

    if last_ev is not None:
        result["final_evalue"] = {
            "t": last_ev.t,
            "e": last_ev.e,
            "decision": last_ev.decision,
        }
        result["evalue_diagnostics"] = (
            last_ev.diagnostics.to_dict() if last_ev.diagnostics else None
        )

    return result


def run_csv_one_sample(
    path: str,
    column: str,
    kind: str,
    method_name: str,
    alpha: float,
    two_sided: bool,
    clip_mode: str,
    null_value: float,
    show_evalues: bool,
    evalue_side: str,
) -> dict:
    spec = StreamSpec(
        alpha=alpha,
        support=SUPPORT,
        kind=kind,
        two_sided=two_sided,
        clip_mode=clip_mode,
    )

    method_map = {
        "hoeffding": HoeffdingCS,
        "empirical_bernstein": EmpiricalBernsteinCS,
    }
    if kind == "bernoulli":
        method_map["bernoulli_exact"] = BernoulliCS

    cs = method_map[method_name](spec)

    eproc = None
    if show_evalues and kind == "bernoulli":
        eproc = BernoulliMixtureE(spec, p0=null_value, side=evalue_side)

    reader = read_one_sample_csv(path, value_column=column)

    times = []
    estimates = []
    los = []
    his = []
    widths = []
    evalues = []
    e_times = []
    error = None
    last_iv = None
    last_ev = None

    for row, _ in reader.rows():
        value = reader.read_numeric(row, column)
        if value is None:
            continue
        try:
            cs.update(value)
            if eproc:
                eproc.update(value)
        except AssumptionViolationError as exc:
            error = str(exc)
            break

        iv = cs.interval()
        if iv.t <= 0:
            continue

        if not times or iv.t != times[-1]:
            times.append(iv.t)
            estimates.append(iv.estimate)
            los.append(iv.lo)
            his.append(iv.hi)
            widths.append(iv.width)
            last_iv = iv

            if eproc:
                ev = eproc.evalue()
                last_ev = ev
                evalues.append(ev.e)
                e_times.append(ev.t)

    if last_iv is None:
        last_iv = cs.interval()

    result = {
        "mode": "csv_one_sample",
        "times": times,
        "estimates": estimates,
        "los": los,
        "his": his,
        "widths": widths,
        "alpha": alpha,
        "true_value": None,
        "null_value": null_value,
        "error": error,
        "value_label": "Mean",
        "cs_title": "Confidence Sequence from CSV",
        "final": {
            "estimate": last_iv.estimate,
            "lo": last_iv.lo,
            "hi": last_iv.hi,
        },
        "diagnostics": last_iv.diagnostics.to_dict() if last_iv.diagnostics else None,
        "csv_summary": reader.get_summary(),
    }

    if last_ev is not None:
        result["final_evalue"] = {
            "t": last_ev.t,
            "e": last_ev.e,
            "decision": last_ev.decision,
        }
        result["evalue_diagnostics"] = (
            last_ev.diagnostics.to_dict() if last_ev.diagnostics else None
        )
        result["evalues"] = evalues
        result["e_times"] = e_times

    return result


def run_csv_two_sample(
    path: str,
    arm_column: str,
    value_column: str,
    kind: str,
    method_name: str,
    alpha: float,
    two_sided: bool,
    clip_mode: str,
    null_value: float,
    show_evalues: bool,
    evalue_side: str,
) -> dict:
    spec = ABSpec(
        alpha=alpha,
        support=SUPPORT,
        kind=kind,
        two_sided=two_sided,
        clip_mode=clip_mode,
    )

    method_map = {
        "hoeffding": TwoSampleHoeffdingCS,
        "empirical_bernstein": TwoSampleEmpiricalBernsteinCS,
    }
    cs = method_map[method_name](spec)

    eproc = None
    if show_evalues:
        eproc = TwoSampleMeanMixtureE(spec, delta0=null_value, side=evalue_side)

    reader = read_ab_test_csv(path, arm_column=arm_column, value_column=value_column)

    times = []
    estimates = []
    los = []
    his = []
    widths = []
    evalues = []
    e_times = []
    error = None
    last_iv = None
    last_ev = None

    for row, _ in reader.rows():
        arm = row[arm_column]
        value = reader.read_numeric(row, value_column)
        if value is None:
            continue
        try:
            cs.update((arm, value))
            if eproc:
                eproc.update((arm, value))
        except AssumptionViolationError as exc:
            error = str(exc)
            break

        iv = cs.interval()
        if iv.t <= 0:
            continue

        times.append(iv.t)
        estimates.append(iv.estimate)
        los.append(iv.lo)
        his.append(iv.hi)
        widths.append(iv.width)
        last_iv = iv

        if eproc:
            ev = eproc.evalue()
            last_ev = ev
            evalues.append(ev.e)
            e_times.append(ev.t * 2)

    if last_iv is None:
        last_iv = cs.interval()

    result = {
        "mode": "csv_two_sample",
        "times": times,
        "estimates": estimates,
        "los": los,
        "his": his,
        "widths": widths,
        "alpha": alpha,
        "true_value": None,
        "null_value": null_value,
        "error": error,
        "value_label": "Lift",
        "cs_title": "Confidence Sequence from CSV",
        "final": {
            "estimate": last_iv.estimate,
            "lo": last_iv.lo,
            "hi": last_iv.hi,
        },
        "diagnostics": last_iv.diagnostics.to_dict() if last_iv.diagnostics else None,
        "csv_summary": reader.get_summary(),
    }

    if last_ev is not None:
        result["final_evalue"] = {
            "t": last_ev.t,
            "e": last_ev.e,
            "decision": last_ev.decision,
        }
        result["evalue_diagnostics"] = (
            last_ev.diagnostics.to_dict() if last_ev.diagnostics else None
        )
        result["evalues"] = evalues
        result["e_times"] = e_times

    return result


def _direction_check_fn(direction: str, threshold: float):
    if direction in ("ge", "lower"):
        return lambda iv: iv.lo > threshold
    if direction in ("le", "upper"):
        return lambda iv: iv.hi < threshold
    return lambda iv: iv.lo > threshold or iv.hi < threshold


def parse_stopping_rule(rule_cfg: dict | None) -> StoppingRule | None:
    if not rule_cfg:
        return None

    rule_type = rule_cfg.get("type", "fixed")
    if rule_type == "fixed":
        return None
    if rule_type == "exclude_threshold":
        threshold = float(rule_cfg.get("threshold", 0.0))
        direction = rule_cfg.get("direction", "both")
        name = f"exclude_{direction}_{threshold}"
        check_fn = _direction_check_fn(direction, threshold)
        return StoppingRule(name=name, fn=lambda iv, _t: check_fn(iv))
    if rule_type == "periodic":
        every = int(rule_cfg.get("every", 50))
        inner_cfg = rule_cfg.get("rule", {"type": "exclude_threshold"})
        inner = parse_stopping_rule(inner_cfg)
        if inner is None:
            return None
        name = f"periodic_{every}_{inner.name}"
        return StoppingRule(
            name=name,
            fn=lambda iv, t: t % every == 0 and inner.fn(iv, t),
        )

    return None


def run_atlas_from_config(cfg: dict) -> tuple[str | None, str | None]:
    validate_atlas_config(cfg)
    n_sim = int(cfg.get("n_sim", 50))
    runner = AtlasRunner(n_sim=n_sim)

    report_one = None
    report_two = None

    one_sample_cfg = cfg.get("one_sample")
    if one_sample_cfg:
        spec_cfg = one_sample_cfg.get("spec", {})
        spec = StreamSpec(
            alpha=spec_cfg.get("alpha", 0.05),
            support=tuple(spec_cfg.get("support", [0.0, 1.0])),
            kind=spec_cfg.get("kind", "bounded"),
            two_sided=spec_cfg.get("two_sided", True),
            name=spec_cfg.get("name", ""),
        )
        method_map = {
            "hoeffding": HoeffdingCS,
            "empirical_bernstein": EmpiricalBernsteinCS,
            "bernoulli": BernoulliCS,
        }
        results: dict[str, dict[str, object]] = {}
        stop_rule = parse_stopping_rule(one_sample_cfg.get("stopping_rule"))
        for method_name in one_sample_cfg.get("methods", []):
            cs_cls = method_map.get(method_name)
            if cs_cls is None:
                continue
            results[method_name] = {}
            for sc in one_sample_cfg.get("scenarios", []):
                scenario = Scenario(
                    name=sc["name"],
                    true_mean=float(sc["true_mean"]),
                    distribution=sc.get("distribution", "bernoulli"),
                    support=tuple(sc.get("support", spec.support)),
                    n_max=int(sc.get("n_max", 200)),
                    seed=int(sc.get("seed", 42)),
                    is_null=bool(sc.get("is_null", False)),
                )
                sc_rule = parse_stopping_rule(sc.get("stopping_rule")) or stop_rule
                metrics = runner.run_one_sample(scenario, spec, cs_cls, sc_rule)
                results[method_name][scenario.name] = metrics

        if results:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                report_path = f.name
            generate_comparison_report(results, report_path, specs={"one_sample": spec})
            report_one = Path(report_path).read_text()
            Path(report_path).unlink()

    two_sample_cfg = cfg.get("two_sample")
    if two_sample_cfg:
        spec_cfg = two_sample_cfg.get("spec", {})
        spec = ABSpec(
            alpha=spec_cfg.get("alpha", 0.05),
            support=tuple(spec_cfg.get("support", [0.0, 1.0])),
            kind=spec_cfg.get("kind", "bounded"),
            two_sided=spec_cfg.get("two_sided", True),
            name=spec_cfg.get("name", ""),
        )
        method_map = {
            "hoeffding": TwoSampleHoeffdingCS,
            "empirical_bernstein": TwoSampleEmpiricalBernsteinCS,
        }
        results = {}
        stop_rule = parse_stopping_rule(two_sample_cfg.get("stopping_rule"))
        for method_name in two_sample_cfg.get("methods", []):
            cs_cls = method_map.get(method_name)
            if cs_cls is None:
                continue
            results[method_name] = {}
            for sc in two_sample_cfg.get("scenarios", []):
                true_lift = float(sc["true_lift"])
                is_null = sc.get("is_null")
                if is_null is None:
                    is_null = true_lift == 0.0
                scenario = Scenario(
                    name=sc["name"],
                    true_mean=float(sc["true_mean"]),
                    true_lift=true_lift,
                    distribution=sc.get("distribution", "bernoulli"),
                    support=tuple(sc.get("support", spec.support)),
                    n_max=int(sc.get("n_max", 200)),
                    seed=int(sc.get("seed", 42)),
                    is_null=bool(is_null),
                )
                sc_rule = parse_stopping_rule(sc.get("stopping_rule")) or stop_rule
                metrics = runner.run_two_sample(scenario, spec, cs_cls, sc_rule)
                results[method_name][scenario.name] = metrics

        if results:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                report_path = f.name
            generate_comparison_report(results, report_path, specs={"two_sample": spec})
            report_two = Path(report_path).read_text()
            Path(report_path).unlink()

    return report_one, report_two


st.sidebar.header("View")
view = st.sidebar.radio("Mode", ["Simulation", "CSV replay", "Atlas smoke"])

if view == "Simulation":
    st.sidebar.header("Simulation")
    sim_mode = st.sidebar.selectbox("Simulation type", ["one-sample", "two-sample"])

    alpha = st.sidebar.slider("Significance level (alpha)", 0.01, 0.20, 0.05, 0.01)
    n_max = st.sidebar.slider("Max sample size", 100, 5000, 1000, 100)
    look_interval = st.sidebar.slider("Check every n samples", 1, 200, 10)
    two_sided = st.sidebar.checkbox("Two-sided interval", value=True)
    clip_mode = st.sidebar.selectbox("Clip mode", ["error", "clip"], index=0)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Diagnostics stress")
    missing_rate = st.sidebar.slider("Missing rate", 0.0, 0.2, 0.0, 0.01)
    out_of_range_rate = st.sidebar.slider("Out-of-range rate", 0.0, 0.2, 0.0, 0.01)
    drift_delta = st.sidebar.slider("Drift delta", 0.0, 0.2, 0.0, 0.01)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Stopping rules")
    stop_when_positive = st.sidebar.checkbox("Stop when CI excludes null (positive)")
    stop_when_negative = st.sidebar.checkbox("Stop when CI excludes null (negative)")
    stop_when_narrow = st.sidebar.checkbox("Stop when width < threshold")
    width_threshold = st.sidebar.slider("Width threshold", 0.01, 0.5, 0.05, 0.01)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Outputs")
    show_naive = st.sidebar.checkbox("Show naive p-values", value=True)
    show_evalues = st.sidebar.checkbox("Show e-values", value=True)
    evalue_side = st.sidebar.selectbox("E-value side", ["ge", "le", "two"], index=0)

    if sim_mode == "one-sample":
        st.sidebar.subheader("One-sample setup")
        kind = st.sidebar.selectbox("Data kind", ["bernoulli", "bounded"], index=0)
        true_mean = st.sidebar.slider("True mean", 0.0, 1.0, 0.5, 0.01)
        null_value = st.sidebar.slider("Null value", 0.0, 1.0, 0.5, 0.01)
        if kind == "bounded":
            concentration = st.sidebar.slider("Beta concentration", 2.0, 200.0, 20.0, 1.0)
        else:
            concentration = 20.0

        method_options = ["hoeffding", "empirical_bernstein"]
        if kind == "bernoulli":
            method_options.append("bernoulli_exact")
        method_name = st.sidebar.selectbox("Method", method_options)

        if kind != "bernoulli" and show_evalues:
            st.sidebar.info("E-values are available for Bernoulli data only.")

        if st.button("Run simulation", type="primary", key="run_one_sample"):
            results = run_one_sample_sim(
                kind=kind,
                method_name=method_name,
                true_mean=true_mean,
                null_value=null_value,
                n_max=n_max,
                alpha=alpha,
                two_sided=two_sided,
                clip_mode=clip_mode,
                missing_rate=missing_rate,
                out_of_range_rate=out_of_range_rate,
                drift_delta=drift_delta,
                concentration=concentration,
                show_naive=show_naive,
                show_evalues=show_evalues,
                evalue_side=evalue_side,
                seed=DEFAULT_SEED,
                look_interval=look_interval,
                stop_when_positive=stop_when_positive,
                stop_when_negative=stop_when_negative,
                stop_when_narrow=stop_when_narrow,
                width_threshold=width_threshold,
            )
            st.session_state.results = results

    else:
        st.sidebar.subheader("Two-sample setup")
        kind = st.sidebar.selectbox("Data kind", ["bernoulli", "bounded"], index=0)
        mean_a = st.sidebar.slider("Control mean", 0.0, 1.0, 0.5, 0.01)
        mean_b = st.sidebar.slider("Treatment mean", 0.0, 1.0, 0.55, 0.01)
        null_value = st.sidebar.slider("Null lift", -0.5, 0.5, 0.0, 0.01)
        if kind == "bounded":
            concentration_a = st.sidebar.slider("Control concentration", 2.0, 200.0, 20.0, 1.0)
            concentration_b = st.sidebar.slider("Treatment concentration", 2.0, 200.0, 20.0, 1.0)
        else:
            concentration_a = 20.0
            concentration_b = 20.0

        method_name = st.sidebar.selectbox("Method", ["hoeffding", "empirical_bernstein"])

        if st.button("Run simulation", type="primary", key="run_two_sample"):
            results = run_two_sample_sim(
                kind=kind,
                method_name=method_name,
                mean_a=mean_a,
                mean_b=mean_b,
                null_value=null_value,
                n_max=n_max,
                alpha=alpha,
                two_sided=two_sided,
                clip_mode=clip_mode,
                missing_rate=missing_rate,
                out_of_range_rate=out_of_range_rate,
                drift_delta=drift_delta,
                concentration_a=concentration_a,
                concentration_b=concentration_b,
                show_naive=show_naive,
                show_evalues=show_evalues,
                evalue_side=evalue_side,
                seed=DEFAULT_SEED,
                look_interval=look_interval,
                stop_when_positive=stop_when_positive,
                stop_when_negative=stop_when_negative,
                stop_when_narrow=stop_when_narrow,
                width_threshold=width_threshold,
            )
            st.session_state.results = results

    if "results" in st.session_state:
        display_results(st.session_state.results)

elif view == "CSV replay":
    st.sidebar.header("CSV replay")
    csv_mode = st.sidebar.selectbox("CSV mode", ["one-sample", "two-sample"])

    alpha = st.sidebar.slider("Significance level (alpha)", 0.01, 0.20, 0.05, 0.01)
    two_sided = st.sidebar.checkbox("Two-sided interval", value=True)
    clip_mode = st.sidebar.selectbox("Clip mode", ["error", "clip"], index=0)
    if csv_mode == "one-sample":
        null_value = st.sidebar.slider("Null value", 0.0, 1.0, 0.5, 0.01)
    else:
        null_value = st.sidebar.slider("Null lift", -0.5, 0.5, 0.0, 0.01)
    show_evalues = st.sidebar.checkbox("Show e-values", value=True)
    evalue_side = st.sidebar.selectbox("E-value side", ["ge", "le", "two"], index=0)

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if csv_mode == "one-sample":
        kind = st.sidebar.selectbox("Data kind", ["bernoulli", "bounded"], index=0)
        column = st.sidebar.text_input("Value column", value="value")
        method_options = ["hoeffding", "empirical_bernstein"]
        if kind == "bernoulli":
            method_options.append("bernoulli_exact")
        method_name = st.sidebar.selectbox("Method", method_options)

        if uploaded_file and st.button("Run CSV", type="primary", key="run_csv_one"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            try:
                results = run_csv_one_sample(
                    path=tmp_path,
                    column=column,
                    kind=kind,
                    method_name=method_name,
                    alpha=alpha,
                    two_sided=two_sided,
                    clip_mode=clip_mode,
                    null_value=null_value,
                    show_evalues=show_evalues,
                    evalue_side=evalue_side,
                )
                display_results(results)
            except Exception as exc:
                st.error(str(exc))
            finally:
                Path(tmp_path).unlink(missing_ok=True)

    else:
        kind = st.sidebar.selectbox("Data kind", ["bernoulli", "bounded"], index=0)
        arm_column = st.sidebar.text_input("Arm column", value="arm")
        value_column = st.sidebar.text_input("Value column", value="value")
        method_name = st.sidebar.selectbox("Method", ["hoeffding", "empirical_bernstein"])

        if uploaded_file and st.button("Run CSV", type="primary", key="run_csv_two"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            try:
                results = run_csv_two_sample(
                    path=tmp_path,
                    arm_column=arm_column,
                    value_column=value_column,
                    kind=kind,
                    method_name=method_name,
                    alpha=alpha,
                    two_sided=two_sided,
                    clip_mode=clip_mode,
                    null_value=null_value,
                    show_evalues=show_evalues,
                    evalue_side=evalue_side,
                )
                display_results(results)
            except Exception as exc:
                st.error(str(exc))
            finally:
                Path(tmp_path).unlink(missing_ok=True)

else:
    st.sidebar.header("Atlas smoke")
    n_sim = st.sidebar.slider("Simulations per scenario", 5, 100, 20, 5)
    n_max = st.sidebar.slider("Max samples per scenario", 50, 500, 150, 50)

    if st.button("Run atlas smoke", type="primary", key="run_atlas_smoke"):
        cfg = load_yaml_config("configs/atlas_smoke.yaml")
        cfg["n_sim"] = n_sim
        for section in ("one_sample", "two_sample"):
            if section in cfg:
                for sc in cfg[section].get("scenarios", []):
                    sc["n_max"] = n_max

        with st.spinner("Running atlas smoke..."):
            report_one, report_two = run_atlas_from_config(cfg)

        if report_one:
            st.subheader("One-sample report")
            st.markdown(report_one)

        if report_two:
            st.subheader("Two-sample report")
            st.markdown(report_two)

# Explanation
st.markdown("---")
st.subheader("How it works")

st.markdown(
    """
### The peeking problem

Traditional p-values assume a fixed sample size and a single look at the data.
If you continuously monitor and stop early when you see a significant result,
your false positive rate inflates dramatically.

### The anytime solution

Confidence sequences and e-values maintain valid guarantees even with:
- Continuous monitoring
- Early stopping
- Optional stopping

Guarantees:
- Confidence sequence: P(theta is in C_t for all t) >= 1 - alpha
- E-values: P(exists t: E_t >= 1/alpha) <= alpha under H0
"""
)
