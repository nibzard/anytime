"""Tests for one-sample confidence sequences."""

import math
import pytest
from anytime.spec import StreamSpec
from anytime.cs.hoeffding import HoeffdingCS
from anytime.cs.empirical_bernstein import EmpiricalBernsteinCS
from anytime.cs.bernoulli_exact import BernoulliCS


@pytest.fixture
def bounded_spec():
    return StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)


@pytest.fixture
def bernoulli_spec():
    return StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli", two_sided=True)


def test_hoeffding_interval_valid(bounded_spec):
    """Hoeffding CS should produce valid intervals."""
    cs = HoeffdingCS(bounded_spec)

    # Before any data
    iv = cs.interval()
    assert iv.t == 0

    # After data
    for x in [0.5, 0.6, 0.4, 0.55]:
        cs.update(x)

    iv = cs.interval()
    assert iv.t == 4
    assert iv.lo < iv.estimate < iv.hi
    # Hoeffding intervals may exceed bounds - that's expected for conservative bounds


def test_hoeffding_alpha_monotonicity(bounded_spec):
    """Lower alpha should give wider intervals."""
    cs1 = HoeffdingCS(StreamSpec(alpha=0.01, support=(0.0, 1.0), kind="bounded", two_sided=True))
    cs2 = HoeffdingCS(StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True))

    data = [0.3, 0.5, 0.7, 0.4, 0.6]
    for x in data:
        cs1.update(x)
        cs2.update(x)

    iv1 = cs1.interval()
    iv2 = cs2.interval()

    # Lower alpha (stricter) -> wider interval
    assert iv1.width >= iv2.width


def test_empirical_bernstein_no_nans(bounded_spec):
    """Empirical Bernstein should not produce NaNs."""
    cs = EmpiricalBernsteinCS(bounded_spec)

    data = [0.5] * 100
    for x in data:
        cs.update(x)
        iv = cs.interval()
        assert not math.isnan(iv.lo)
        assert not math.isnan(iv.hi)
        assert not math.isnan(iv.estimate)


def test_empirical_bernstein_narrower_when_low_variance(bounded_spec):
    """EB should be narrower than Hoeffding when variance is low."""
    # Low variance data
    data = [0.5] * 50

    cs_h = HoeffdingCS(bounded_spec)
    cs_eb = EmpiricalBernsteinCS(bounded_spec)

    for x in data:
        cs_h.update(x)
        cs_eb.update(x)

    iv_h = cs_h.interval()
    iv_eb = cs_eb.interval()

    # EB should be narrower (or equal) for low variance
    assert iv_eb.width <= iv_h.width


def test_bernoulli_binary_only(bernoulli_spec):
    """Bernoulli CS should work with 0/1 data."""
    cs = BernoulliCS(bernoulli_spec)

    data = [0, 1, 1, 0, 1, 1, 1, 0]
    for x in data:
        cs.update(float(x))

    iv = cs.interval()
    assert iv.t == 8
    assert 0.0 <= iv.lo <= iv.estimate <= iv.hi <= 1.0


def test_bernoulli_edge_cases(bernoulli_spec):
    """Bernoulli CS should handle all zeros and all ones."""
    # All zeros
    cs = BernoulliCS(bernoulli_spec)
    for _ in range(10):
        cs.update(0.0)
    iv = cs.interval()
    assert iv.estimate == 0.0
    assert iv.lo == 0.0

    # All ones
    cs = BernoulliCS(bernoulli_spec)
    for _ in range(10):
        cs.update(1.0)
    iv = cs.interval()
    assert iv.estimate == 1.0
    assert iv.hi == 1.0


def test_reset(bounded_spec):
    """Reset should clear state."""
    cs = HoeffdingCS(bounded_spec)
    cs.update(0.5)
    cs.update(0.6)

    assert cs.interval().t == 2

    cs.reset()
    assert cs.interval().t == 0
