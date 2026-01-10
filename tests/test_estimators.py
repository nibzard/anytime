"""Tests for online estimators."""

import pytest
import numpy as np
from anytime.core.estimators import OnlineMean, OnlineVariance


def test_online_mean_matches_numpy():
    """Online mean should match numpy mean."""
    data = [1.0, 2.0, 3.0, 4.0, 5.0]

    om = OnlineMean()
    for x in data:
        om.update(x)

    assert om.mean == pytest.approx(np.mean(data))
    assert om.n == len(data)


def test_online_variance_matches_numpy():
    """Online variance should match numpy variance."""
    data = [1.0, 2.0, 3.0, 4.0, 5.0]

    ov = OnlineVariance()
    for x in data:
        ov.update(x)

    assert ov.mean == pytest.approx(np.mean(data))
    assert ov.variance == pytest.approx(np.var(data, ddof=1))
    assert ov.var_pop == pytest.approx(np.var(data, ddof=0))


def test_variance_stability_small_t():
    """Variance should be stable for small t (n <= 1)."""
    ov = OnlineVariance()

    # n=0
    assert ov.variance == 0.0
    assert ov.var_pop == 0.0

    # n=1
    ov.update(5.0)
    assert ov.variance == 0.0  # Undefined, returns 0
    assert ov.var_pop == 0.0

    # n=2
    ov.update(7.0)
    assert ov.variance > 0
    assert ov.variance == pytest.approx(2.0)  # var of [5, 7]


def test_reset():
    """Reset should clear estimator state."""
    om = OnlineMean()
    om.update(5.0)
    om.reset()
    assert om.n == 0
    assert om.mean == 0.0

    ov = OnlineVariance()
    ov.update(5.0)
    ov.update(7.0)
    ov.reset()
    assert ov.n == 0
    assert ov.mean == 0.0
    assert ov._m2 == 0.0
