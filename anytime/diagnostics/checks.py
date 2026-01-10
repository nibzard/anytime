"""Diagnostic utilities for assumption validation."""

import math
from dataclasses import dataclass, field
from collections import deque
from typing import Deque, TYPE_CHECKING

from anytime.errors import AssumptionViolationError
from anytime.types import GuaranteeTier

if TYPE_CHECKING:
    from anytime.spec import StreamSpec


@dataclass
class Diagnostics:
    """Diagnostic metadata for statistical outputs.

    Attributes:
        tier: Guarantee tier based on assumption satisfaction
        out_of_range_count: Number of out-of-range values seen
        missing_count: Number of missing values seen
        clipped_count: Number of values that were clipped
        drift_detected: Whether drift was detected
        drift_score: Drift score (higher = more drift)
    """

    tier: GuaranteeTier = GuaranteeTier.GUARANTEED
    out_of_range_count: int = 0
    missing_count: int = 0
    clipped_count: int = 0
    drift_detected: bool = False
    drift_score: float = 0.0

    def to_dict(self) -> dict[str, float | int | bool | str]:
        return {
            "tier": self.tier.value,
            "out_of_range_count": self.out_of_range_count,
            "missing_count": self.missing_count,
            "clipped_count": self.clipped_count,
            "drift_detected": self.drift_detected,
            "drift_score": self.drift_score,
        }

    def snapshot(self) -> "Diagnostics":
        """Create a snapshot copy for storing in outputs."""
        return Diagnostics(
            tier=self.tier,
            out_of_range_count=self.out_of_range_count,
            missing_count=self.missing_count,
            clipped_count=self.clipped_count,
            drift_detected=self.drift_detected,
            drift_score=self.drift_score,
        )


@dataclass
class RangeChecker:
    """Check if values are within declared support.

    Can be configured to error on out-of-range values or clip them.
    """

    support: tuple[float | None, float | None]
    clip_mode: str = "error"  # "error" or "clip"
    diagnostics: Diagnostics = field(default_factory=Diagnostics)

    def check(self, x: float) -> float:
        """Check value and return (possibly clipped) value."""
        lo, hi = self.support

        # Check missing
        if not math.isfinite(x):
            self.diagnostics.missing_count += 1
            self.diagnostics.tier = GuaranteeTier.DIAGNOSTIC
            return x

        # Check bounds
        out_of_range = False
        if lo is not None and x < lo:
            out_of_range = True
        if hi is not None and x > hi:
            out_of_range = True

        if out_of_range:
            self.diagnostics.out_of_range_count += 1
            if self.clip_mode == "clip":
                self.diagnostics.clipped_count += 1
                self.diagnostics.tier = GuaranteeTier.CLIPPED
                # Clip to bounds
                if lo is not None and x < lo:
                    return lo
                if hi is not None and x > hi:
                    return hi
            else:
                self.diagnostics.tier = GuaranteeTier.DIAGNOSTIC
                raise AssumptionViolationError(f"Value {x} out of range {self.support}")

        return x

    def reset(self) -> None:
        """Reset diagnostics state."""
        self.diagnostics = Diagnostics()


@dataclass
class MissingnessTracker:
    """Track missing values in the stream."""

    total_count: int = 0
    missing_count: int = 0

    def update(self, x: float) -> None:
        """Update with new observation."""
        self.total_count += 1
        if x != x:  # NaN check
            self.missing_count += 1

    @property
    def missing_rate(self) -> float:
        """Proportion of missing values."""
        if self.total_count == 0:
            return 0.0
        return self.missing_count / self.total_count

    def reset(self) -> None:
        """Reset tracking state."""
        self.total_count = 0
        self.missing_count = 0


@dataclass
class DriftDetector:
    """Detect drift using a rolling mean change heuristic.

    Uses a simple CUSUM-like approach: tracks if the recent mean
    deviates significantly from the historical mean.
    """

    window_size: int = 50
    threshold: float = 2.0  # Standard deviations
    _window: Deque[float] = field(default_factory=deque)
    _global_mean: float = 0.0
    _global_var: float = 0.0
    _n: int = 0
    drift_detected: bool = False

    def update(self, x: float) -> bool:
        """Update with new observation and return if drift detected."""
        # Update global statistics
        self._n += 1
        delta = x - self._global_mean
        self._global_mean += delta / self._n
        delta2 = x - self._global_mean
        self._global_var += delta * delta2

        # Update window
        self._window.append(x)
        if len(self._window) > self.window_size:
            self._window.popleft()

        # Check drift if we have enough data
        if len(self._window) >= self.window_size and self._n > self.window_size * 2:
            window_mean = sum(self._window) / len(self._window)
            global_sd = (self._global_var / self._n) ** 0.5 if self._n > 1 else 0

            if global_sd > 0:
                z = abs(window_mean - self._global_mean) / global_sd
                if z > self.threshold:
                    self.drift_detected = True

        return self.drift_detected

    @property
    def drift_score(self) -> float:
        """Current drift score (z-statistic)."""
        if len(self._window) < self.window_size:
            return 0.0

        window_mean = sum(self._window) / len(self._window)
        global_sd = (self._global_var / self._n) ** 0.5 if self._n > 1 else 0

        if global_sd == 0:
            return 0.0

        return abs(window_mean - self._global_mean) / global_sd

    def reset(self) -> None:
        """Reset drift detection state."""
        self._window.clear()
        self._global_mean = 0.0
        self._global_var = 0.0
        self._n = 0
        self.drift_detected = False


class DiagnosticsSetup:
    """Container for standard diagnostics components.

    Reduces duplication across CS and e-value classes.
    """

    def __init__(self, spec: "StreamSpec"):
        self.diagnostics = Diagnostics()
        self.range_checker = RangeChecker(spec.support, spec.clip_mode, self.diagnostics)
        self.missingness = MissingnessTracker()
        self.drift_detector = DriftDetector()

    def reset(self) -> None:
        """Reset all diagnostics to initial state."""
        self.diagnostics = Diagnostics()
        self.range_checker = RangeChecker(
            self.range_checker.support, self.range_checker.clip_mode, self.diagnostics
        )
        self.missingness.reset()
        self.drift_detector.reset()


def merge_diagnostics(
    diag_a: Diagnostics | None,
    diag_b: Diagnostics | None,
) -> Diagnostics:
    """Merge two Diagnostics objects into one.

    The merged result combines counts from both and uses the worst tier.
    """
    merged = Diagnostics()
    for diag in (diag_a, diag_b):
        if diag is None:
            continue
        merged.out_of_range_count += diag.out_of_range_count
        merged.missing_count += diag.missing_count
        merged.clipped_count += diag.clipped_count
        merged.drift_detected = merged.drift_detected or diag.drift_detected
        merged.drift_score = max(merged.drift_score, diag.drift_score)
        if diag.tier == GuaranteeTier.DIAGNOSTIC:
            merged.tier = GuaranteeTier.DIAGNOSTIC
        elif diag.tier == GuaranteeTier.CLIPPED and merged.tier != GuaranteeTier.DIAGNOSTIC:
            merged.tier = GuaranteeTier.CLIPPED
    return merged


def apply_diagnostics(
    x: float,
    range_checker: RangeChecker,
    missingness_tracker: MissingnessTracker,
    drift_detector: DriftDetector,
) -> float | None:
    """Apply diagnostics and return sanitized value, or None if skipped."""
    if not math.isfinite(x):
        missingness_tracker.update(float("nan"))
        range_checker.diagnostics.missing_count += 1
        range_checker.diagnostics.tier = GuaranteeTier.DIAGNOSTIC
        return None

    missingness_tracker.update(x)
    x_checked = range_checker.check(x)

    if x_checked != x_checked:  # NaN
        return None

    drift_detector.update(x_checked)
    range_checker.diagnostics.drift_score = max(
        range_checker.diagnostics.drift_score, drift_detector.drift_score
    )
    if drift_detector.drift_detected:
        range_checker.diagnostics.drift_detected = True
        range_checker.diagnostics.tier = GuaranteeTier.DIAGNOSTIC

    return x_checked
