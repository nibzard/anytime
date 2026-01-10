"""Hoeffding-style confidence sequences."""

import math
from anytime.spec import StreamSpec
from anytime.types import Interval, GuaranteeTier
from anytime.core.estimators import OnlineMean
from anytime.diagnostics.checks import (
    Diagnostics,
    RangeChecker,
    MissingnessTracker,
    DriftDetector,
    apply_diagnostics,
)


class HoeffdingCS:
    """Hoeffding-style confidence sequence for bounded data.

    Based on the Hoeffding inequality with a time-uniform martingale.
    Conservative but valid for bounded data.

    For support [a, b], the confidence interval at time t uses a
    time-uniform (stitched) Hoeffding bound:
        mean_t ± (b-a) * sqrt(log((pi^2 * t^2) / (3*alpha)) / (2*t))
    for two-sided intervals.
    """

    def __init__(self, spec: StreamSpec):
        if spec.kind not in {"bounded", "bernoulli"}:
            raise ValueError("HoeffdingCS requires bounded or bernoulli data")
        lo, hi = spec.support
        if lo is None or hi is None:
            raise ValueError("HoeffdingCS requires finite support bounds")
        self.spec = spec
        self._estimator = OnlineMean()
        self._range = hi - lo  # (b - a)
        self._diagnostics = Diagnostics()
        self._range_checker = RangeChecker(spec.support, spec.clip_mode, self._diagnostics)
        self._missingness = MissingnessTracker()
        self._drift_detector = DriftDetector()

    def update(self, x: float) -> None:
        """Update with new observation."""
        x_checked = apply_diagnostics(
            x, self._range_checker, self._missingness, self._drift_detector
        )
        if x_checked is None:
            return
        self._estimator.update(x_checked)

    def interval(self) -> Interval:
        """Get current confidence interval."""
        t = self._estimator.n
        mean = self._estimator.mean

        if t == 0:
            return Interval(
                t=0,
                estimate=0.0,
                lo=float("-inf"),
                hi=float("inf"),
                alpha=self.spec.alpha,
                tier=self._diagnostics.tier,
                diagnostics=self._diagnostics,
            )

        # Time-uniform Hoeffding bound via union over t with 1/t^2 schedule.
        if self.spec.two_sided:
            log_term = math.log((math.pi**2 * t**2) / (3 * self.spec.alpha))
        else:
            log_term = math.log((math.pi**2 * t**2) / (6 * self.spec.alpha))
        margin = self._range * math.sqrt(log_term / (2 * t))

        lo = mean - margin
        hi = mean + margin

        return Interval(
            t=t,
            estimate=mean,
            lo=lo,
            hi=hi,
            alpha=self.spec.alpha,
            tier=self._diagnostics.tier,
            diagnostics=self._diagnostics,
        )

    def reset(self) -> None:
        """Reset to initial state."""
        self._estimator.reset()
