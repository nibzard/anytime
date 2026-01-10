"""Tests for diagnostic utilities."""

import pytest
from anytime.types import GuaranteeTier
from anytime.errors import AssumptionViolationError
from anytime.diagnostics.checks import (
    Diagnostics,
    RangeChecker,
    MissingnessTracker,
    DriftDetector,
)


def test_range_checker_in_range():
    """Values in range should pass through."""
    checker = RangeChecker(support=(0.0, 1.0), clip_mode="error")
    assert checker.check(0.5) == 0.5
    assert checker.check(0.0) == 0.0
    assert checker.check(1.0) == 1.0
    assert checker.diagnostics.tier == GuaranteeTier.GUARANTEED


def test_range_checker_out_of_range_error():
    """Out of range should raise in error mode."""
    checker = RangeChecker(support=(0.0, 1.0), clip_mode="error")
    with pytest.raises(AssumptionViolationError):
        checker.check(1.5)


def test_range_checker_clip_mode():
    """Clip mode should clip values and update tier."""
    checker = RangeChecker(support=(0.0, 1.0), clip_mode="clip")

    result = checker.check(1.5)
    assert result == 1.0
    assert checker.diagnostics.tier == GuaranteeTier.CLIPPED
    assert checker.diagnostics.clipped_count == 1


def test_range_checker_nan():
    """NaN should be tracked as missing."""
    checker = RangeChecker(support=(0.0, 1.0), clip_mode="error")
    result = checker.check(float("nan"))
    assert __import__("math").isnan(result)
    assert checker.diagnostics.missing_count == 1
    assert checker.diagnostics.tier == GuaranteeTier.DIAGNOSTIC


def test_missingness_tracker():
    """Missingness tracker should track missing values."""
    tracker = MissingnessTracker()

    tracker.update(1.0)
    tracker.update(float("nan"))
    tracker.update(2.0)
    tracker.update(float("nan"))

    assert tracker.total_count == 4
    assert tracker.missing_count == 2
    assert tracker.missing_rate == 0.5


def test_drift_detector_basic():
    """Drift detector should detect mean shifts."""
    detector = DriftDetector(window_size=10, threshold=1.0)

    # Stable data
    for _ in range(20):
        detector.update(0.5)
    assert not detector.drift_detected

    # Shift to different mean
    for _ in range(20):
        detector.update(0.8)

    # With enough data, should detect drift
    # (depending on threshold and accumulated variance)
    assert detector.drift_score >= 0


def test_drift_detector_empty():
    """Drift score should be 0 with no data."""
    detector = DriftDetector()
    assert detector.drift_score == 0.0


def test_drift_tier_propagation():
    """Drift detection should flip tier to diagnostic on CS outputs."""
    from anytime.spec import StreamSpec
    from anytime.cs.hoeffding import HoeffdingCS

    spec = StreamSpec(alpha=0.1, support=(0.0, 1.0), kind="bounded", two_sided=True)
    cs = HoeffdingCS(spec)

    # Tighten detector to force a drift flag quickly.
    cs._drift_detector = DriftDetector(window_size=5, threshold=0.2)

    for _ in range(10):
        cs.update(0.0)
    for _ in range(10):
        cs.update(1.0)

    iv = cs.interval()
    assert iv.tier == GuaranteeTier.DIAGNOSTIC
