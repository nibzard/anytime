"""Tests for two-sample confidence sequences."""

import pytest
from anytime.spec import ABSpec
from anytime.twosample.hoeffding import TwoSampleHoeffdingCS
from anytime.twosample.empirical_bernstein import TwoSampleEmpiricalBernsteinCS


@pytest.fixture
def ab_spec():
    return ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)


def test_twosample_hoeffding_basic(ab_spec):
    """Two-sample Hoeffding should produce valid intervals."""
    cs = TwoSampleHoeffdingCS(ab_spec)

    # Add data from both arms
    for i in range(50):
        cs.update(("A", 0.5))
        cs.update(("B", 0.6))

    iv = cs.interval()
    assert iv.t == 100
    assert iv.lo < iv.estimate < iv.hi


def test_twosample_symmetry(ab_spec):
    """Swapping A and B should flip the estimate sign."""
    cs = TwoSampleHoeffdingCS(ab_spec)

    data = [("A", 0.4), ("B", 0.6)] * 25
    for pair in data:
        cs.update(pair)

    iv1 = cs.interval()

    cs2 = TwoSampleHoeffdingCS(ab_spec)
    for arm, x in data:
        cs2.update(("B" if arm == "A" else "A", x))

    iv2 = cs2.interval()

    # Estimates should have opposite signs
    assert abs(iv1.estimate + iv2.estimate) < 0.01


def test_twosample_empirical_bernstein_no_nans(ab_spec):
    """Two-sample EB should not produce NaNs."""
    cs = TwoSampleEmpiricalBernsteinCS(ab_spec)

    for i in range(50):
        cs.update(("A", 0.5))
        cs.update(("B", 0.6))

    iv = cs.interval()
    assert iv.t == 100
    assert not __import__("math").isnan(iv.lo)
    assert not __import__("math").isnan(iv.hi)
    assert not __import__("math").isnan(iv.estimate)


def test_twosample_reset(ab_spec):
    """Reset should clear state."""
    cs = TwoSampleHoeffdingCS(ab_spec)
    cs.update(("A", 0.5))
    cs.update(("B", 0.6))

    assert cs.interval().t == 2

    cs.reset()
    assert cs.interval().t == 0


def test_invalid_arm(ab_spec):
    """Invalid arm should raise."""
    cs = TwoSampleHoeffdingCS(ab_spec)
    with pytest.raises(ValueError):
        cs.update(("C", 0.5))


def test_twosample_hoeffding_one_sided():
    """One-sided two-sample Hoeffding should produce valid intervals."""
    spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=False)
    cs = TwoSampleHoeffdingCS(spec)

    for i in range(50):
        cs.update(("A", 0.5))
        cs.update(("B", 0.6))

    iv = cs.interval()
    assert iv.t == 100
    # One-sided should be narrower (tighter) than two-sided
    spec_two = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
    cs_two = TwoSampleHoeffdingCS(spec_two)
    for i in range(50):
        cs_two.update(("A", 0.5))
        cs_two.update(("B", 0.6))
    iv_two = cs_two.interval()
    # One-sided width should be <= two-sided width (at same alpha)
    assert (iv.hi - iv.lo) <= (iv_two.hi - iv_two.lo)


def test_twosample_empirical_bernstein_one_sided():
    """One-sided two-sample EB should produce valid intervals."""
    spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=False)
    cs = TwoSampleEmpiricalBernsteinCS(spec)

    for i in range(50):
        cs.update(("A", 0.5))
        cs.update(("B", 0.6))

    iv = cs.interval()
    assert iv.t == 100
    assert not __import__("math").isnan(iv.lo)
    assert not __import__("math").isnan(iv.hi)
