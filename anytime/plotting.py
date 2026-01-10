"""Plotting utilities for anytime inference."""

from typing import Any

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np


def plot_interval_band(
    times: list[int],
    estimates: list[float],
    los: list[float],
    his: list[float],
    true_value: float | None = None,
    title: str = "Confidence Sequence",
    alpha: float = 0.05,
) -> plt.Figure:
    """Plot confidence sequence as a shaded band.

    Args:
        times: Time points
        estimates: Point estimates
        los: Lower bounds
        his: Upper bounds
        true_value: Optional true value for reference line
        title: Plot title
        alpha: Significance level (for title)

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot confidence band
    ax.fill_between(times, los, his, alpha=0.3, label=f"{1-alpha:.0%} confidence band")

    # Plot estimate
    ax.plot(times, estimates, "k-", label="Estimate", linewidth=1.5)

    # Plot true value if provided
    if true_value is not None:
        ax.axhline(y=true_value, color="r", linestyle="--", label="True value")

    ax.set_xlabel("Time (t)")
    ax.set_ylabel("Value")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig


def plot_evalue_series(
    times: list[int],
    evalues: list[float],
    threshold: float,
    title: str = "E-value over time",
) -> plt.Figure:
    """Plot e-value time series with decision threshold.

    Args:
        times: Time points
        evalues: E-values
        threshold: Decision threshold (1/alpha)
        title: Plot title

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(times, evalues, "b-", label="E-value", linewidth=1.5)
    ax.axhline(y=threshold, color="r", linestyle="--", label=f"Threshold = {threshold:.2f}")

    # Shade region above threshold
    ax.fill_between(times, 0, evalues, where=np.array(evalues) >= threshold,
                    alpha=0.3, color="green", label="Decision region")

    ax.set_xlabel("Time (t)")
    ax.set_ylabel("E-value")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_yscale("log")

    return fig


def plot_stopping_time_histogram(
    stopping_times: list[int],
    max_time: int,
    title: str = "Stopping time distribution",
) -> plt.Figure:
    """Plot histogram of stopping times.

    Args:
        stopping_times: List of stopping times from simulations
        max_time: Maximum possible stopping time (for censoring)
        title: Plot title

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Count censored observations
    censored = sum(t >= max_time for t in stopping_times)

    ax.hist(stopping_times, bins=50, alpha=0.7, edgecolor="black")
    ax.axvline(x=max_time, color="r", linestyle="--", label=f"Max time ({censored} censored)")

    ax.set_xlabel("Stopping time")
    ax.set_ylabel("Frequency")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig
