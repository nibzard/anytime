"""Empirical Bernstein confidence sequences."""

import math
from anytime.spec import StreamSpec
from anytime.types import Interval, GuaranteeTier
from anytime.core.estimators import OnlineVariance
from anytime.diagnostics.checks import (
    Diagnostics,
    RangeChecker,
    MissingnessTracker,
    DriftDetector,
    apply_diagnostics,
)


class EmpiricalBernsteinCS:
    """Empirical Bernstein confidence sequence for bounded data.

    Variance-adaptive confidence sequence that uses online variance estimates.
    Narrower than Hoeffding when variance is low.

    Uses a time-uniform union bound over t with an empirical Bernstein
    inequality at each time. This is conservative but valid for bounded data.
    Early-time guard: uses time-uniform Hoeffding for small t.
    """

    def __init__(self, spec: StreamSpec):
        if spec.kind not in {"bounded", "bernoulli"}:
            raise ValueError("EmpiricalBernsteinCS requires bounded or bernoulli data")
        lo, hi = spec.support
        if lo is None or hi is None:
            raise ValueError("EmpiricalBernsteinCS requires finite support bounds")
        self.spec = spec
        self._estimator = OnlineVariance()
        self._range = hi - lo  # (b - a)
        self._v_hat_prev = 0.0  # Previous variance estimate
        self._diagnostics = Diagnostics()
        self._range_checker = RangeChecker(spec.support, spec.clip_mode, self._diagnostics)
        self._missingness = MissingnessTracker()
        self._drift_detector = DriftDetector()

    def update(self, x: float) -> None:
        """Update with new observation."""
        self._v_hat_prev = self._estimator.variance
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
        v_hat = self._estimator.variance

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

        # Early-time guard: use Hoeffding for small t or zero variance.
        if t < 2 or v_hat == 0:
            if self.spec.two_sided:
                log_term = math.log((math.pi**2 * t**2) / (3 * self.spec.alpha))
            else:
                log_term = math.log((math.pi**2 * t**2) / (6 * self.spec.alpha))
            margin = self._range * math.sqrt(log_term / (2 * t))
        else:
            # Time-uniform empirical Bernstein via union bound over t.
            delta_t = (6 * self.spec.alpha) / (math.pi**2 * t**2)
            log_term = math.log(3 / delta_t)
            term1 = 2 * v_hat * log_term / t
            term2 = 7 * self._range * log_term / (3 * (t - 1))
            margin = math.sqrt(term1) + term2

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
        self._v_hat_prev = 0.0
