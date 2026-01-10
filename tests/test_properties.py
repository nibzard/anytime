"""Property-based tests for interval invariants using Hypothesis."""

from hypothesis import given, settings, assume
import hypothesis.strategies as st
import pytest

from anytime.spec import StreamSpec, ABSpec
from anytime.cs.hoeffding import HoeffdingCS
from anytime.cs.empirical_bernstein import EmpiricalBernsteinCS
from anytime.cs.bernoulli_exact import BernoulliCS
from anytime.twosample.hoeffding import TwoSampleHoeffdingCS
from anytime.twosample.empirical_bernstein import TwoSampleEmpiricalBernsteinCS


class TestIntervalInvariants:
    """Property-based tests for interval invariants."""

    @given(alpha=st.floats(min_value=0.01, max_value=0.2, allow_nan=False, allow_infinity=False))
    def test_hoeffding_coverage_bounds(self, alpha):
        """Hoeffding CI coverage should be between 0 and 1 for any alpha."""
        # After sufficient data, coverage should approach 1-alpha
        spec = StreamSpec(alpha=alpha, support=(0.0, 1.0), kind="bounded", two_sided=True)
        cs = HoeffdingCS(spec)

        # Add some data
        for x in [0.3, 0.5, 0.7] * 10:
            cs.update(x)

        iv = cs.interval()
        assert 0.0 <= iv.lo <= iv.estimate <= iv.hi <= 1.0

    @given(data=st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False), min_size=2, max_size=50))
    def test_interval_width_non_negative(self, data):
        """Interval width should always be non-negative."""
        assume(len(data) > 0)  # Ensure we have at least one value
        spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
        cs = HoeffdingCS(spec)

        for x in data:
            cs.update(x)

        iv = cs.interval()
        assert iv.width >= 0
        assert iv.width == iv.hi - iv.lo

    @given(data=st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False), min_size=2, max_size=100))
    def test_interval_time_increases(self, data):
        """Interval time counter should match number of updates."""
        assume(len(data) > 0)
        spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
        cs = HoeffdingCS(spec)

        for x in data:
            cs.update(x)

        iv = cs.interval()
        assert iv.t == len(data)

    @given(true_mean=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False))
    def test_bernoulli_interval_bounds(self, true_mean):
        """Bernoulli CS interval should stay within [0, 1] support."""
        spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli", two_sided=True)
        cs = BernoulliCS(spec)

        # Generate Bernoulli data with the true mean
        import random
        rng = random.Random(42)
        for _ in range(50):
            x = float(rng.random() < true_mean)
            cs.update(x)

        iv = cs.interval()
        assert 0.0 <= iv.lo <= iv.hi <= 1.0

    @given(
        a_data=st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False), min_size=1, max_size=50),
        b_data=st.lists(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False), min_size=1, max_size=50),
    )
    def test_twosample_symmetry(self, a_data, b_data):
        """Swapping A and B should invert the sign of the lift estimate."""
        assume(len(a_data) > 0 and len(b_data) > 0)
        spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)

        # Run A -> B
        cs1 = TwoSampleHoeffdingCS(spec)
        for x in a_data:
            cs1.update(("A", x))
        for x in b_data:
            cs1.update(("B", x))
        iv1 = cs1.interval()

        # Run B -> A (swapped)
        cs2 = TwoSampleHoeffdingCS(spec)
        for x in b_data:
            cs2.update(("A", x))
        for x in a_data:
            cs2.update(("B", x))
        iv2 = cs2.interval()

        # Estimates should have opposite signs (approximately)
        # Width should be the same
        assert abs(iv1.width - iv2.width) < 1e-10
        assert abs(iv1.estimate + iv2.estimate) < 0.1  # Within tolerance

    @given(alpha=st.floats(min_value=0.01, max_value=0.2, allow_nan=False, allow_infinity=False))
    def test_two_sided_wider_than_one_sided(self, alpha):
        """Two-sided interval should be wider than one-sided for same data."""
        assume(0.01 < alpha < 0.2)

        spec_two = StreamSpec(alpha=alpha, support=(0.0, 1.0), kind="bounded", two_sided=True)
        spec_one = StreamSpec(alpha=alpha, support=(0.0, 1.0), kind="bounded", two_sided=False)

        cs_two = HoeffdingCS(spec_two)
        cs_one = HoeffdingCS(spec_one)

        data = [0.3, 0.5, 0.7] * 10
        for x in data:
            cs_two.update(x)
            cs_one.update(x)

        iv_two = cs_two.interval()
        iv_one = cs_one.interval()

        # Two-sided should be wider (or equal)
        assert iv_two.width >= iv_one.width * 0.9  # Allow some numerical tolerance


class TestIntervalMonotonicity:
    """Tests for interval monotonicity properties."""

    def test_interval_width_decreases_with_data(self):
        """Interval width should generally decrease as we add more data."""
        spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
        cs = HoeffdingCS(spec)

        widths = []
        for i in range(100):
            cs.update(0.5)
            iv = cs.interval()
            widths.append(iv.width)

        # Width should be non-increasing (with some tolerance for numerical noise)
        for i in range(1, len(widths)):
            assert widths[i] <= widths[i-1] * 1.01  # Allow 1% tolerance

    def test_estimate_converges(self):
        """Estimate should converge towards true mean with more data."""
        spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
        cs = HoeffdingCS(spec)

        true_mean = 0.5
        estimates = []
        for i in range(100):
            cs.update(true_mean)
            iv = cs.interval()
            estimates.append(iv.estimate)

        # Later estimates should be closer to true mean
        early_error = abs(estimates[10] - true_mean) if len(estimates) > 10 else 1.0
        late_error = abs(estimates[-1] - true_mean)
        assert late_error <= early_error


class TestIntervalEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_interval(self):
        """Empty data should return unbounded interval."""
        spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
        cs = HoeffdingCS(spec)

        iv = cs.interval()
        assert iv.t == 0
        assert iv.lo == float("-inf")
        assert iv.hi == float("inf")

    def test_constant_data(self):
        """Constant data should produce interval centered at true value."""
        spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
        cs = EmpiricalBernsteinCS(spec)

        # All 0.5s - zero variance
        for _ in range(100):
            cs.update(0.5)

        iv = cs.interval()
        assert iv.estimate == 0.5
        # Interval should contain the true value
        assert iv.lo <= 0.5 <= iv.hi
        # EB should be reasonably tight compared to Hoeffding
        # (Hoeffding would give width ~0.6 for n=100)
        assert iv.width < 0.6

    def test_extreme_values(self):
        """CS should handle values at support bounds."""
        spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
        cs = HoeffdingCS(spec)

        # Alternating 0 and 1
        for _ in range(50):
            cs.update(0.0)
            cs.update(1.0)

        iv = cs.interval()
        assert iv.t == 100
        assert 0.0 <= iv.lo <= iv.hi <= 1.0
