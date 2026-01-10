"""Tests for plotting utilities."""

import tempfile
from pathlib import Path

from anytime.plotting import (
    plot_interval_band,
    plot_evalue_series,
    plot_stopping_time_histogram,
)


def test_plot_interval_band_headless():
    """Interval band plot should work in headless mode."""
    times = list(range(1, 101))
    estimates = [0.5 + 0.01 * t / 100 for t in times]
    los = [e - 0.1 for e in estimates]
    his = [e + 0.1 for e in estimates]

    fig = plot_interval_band(times, estimates, los, his, true_value=0.5)

    assert fig is not None
    # Verify Agg backend is being used
    import matplotlib
    assert matplotlib.get_backend() == 'Agg'


def test_plot_evalue_series_headless():
    """E-value plot should work in headless mode."""
    times = list(range(1, 101))
    evalues = [1.0 + 0.1 * t for t in times]
    threshold = 20.0

    fig = plot_evalue_series(times, evalues, threshold)

    assert fig is not None
    import matplotlib
    assert matplotlib.get_backend() == 'Agg'


def test_plot_stopping_time_histogram_headless():
    """Stopping time histogram should work in headless mode."""
    stopping_times = [50, 75, 100, 100, 100, 60, 80, 90, 100, 70]
    max_time = 100

    fig = plot_stopping_time_histogram(stopping_times, max_time)

    assert fig is not None
    import matplotlib
    assert matplotlib.get_backend() == 'Agg'


def test_plot_save_and_close():
    """Plots should be saveable and closeable."""
    times = [1, 2, 3, 4, 5]
    estimates = [0.5, 0.6, 0.55, 0.65, 0.6]
    los = [e - 0.1 for e in estimates]
    his = [e + 0.1 for e in estimates]

    fig = plot_interval_band(times, estimates, los, his)

    with tempfile.NamedTemporaryFile(suffix='.png') as tmp:
        fig.savefig(tmp.name)
        assert Path(tmp.name).stat().st_size > 0

    # Close figure to free memory
    import matplotlib.pyplot as plt
    plt.close(fig)
