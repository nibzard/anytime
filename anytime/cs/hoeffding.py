"""Hoeffding-style confidence sequences.

References:
    - Hoeffding, W. (1963). "Probability inequalities for sums of bounded random variables."
      Journal of the American Statistical Association.
    - Maurer, A., & Pontil, M. (2009). "Empirical Bernstein bounds and sample variance."
      ECML PKDD.
    - The time-uniform (stitched) version uses the union bound technique:
      For any alpha-level test at each fixed time t, P(sup_t p-value < alpha) <=
      sum_t P(p-value_t < alpha) with weights 1/t^2.

Constants:
    Two-sided: pi^2 / 3 from sum_{t=1}^inf 1/t^2 = pi^2/6, doubled for two tails
    One-sided: pi^2 / 6 for a single tail
    Formula: (b-a) * sqrt(log((pi^2 * t^2) / (c * alpha)) / (2*t))
      where c = 3 for two-sided, c = 6 for one-sided
"""

import math

from anytime.spec import StreamSpec
from anytime.types import Interval
from anytime.core.estimators import OnlineMean
from anytime.diagnostics.checks import DiagnosticsSetup, apply_diagnostics


class HoeffdingCS:
    """Hoeffding-style confidence sequence for bounded data.

    Based on the Hoeffding inequality with a time-uniform martingale.
    Conservative but valid for bounded data.

    For support [a, b], the confidence interval at time t uses a
    time-uniform (stitched) Hoeffding bound:
        mean_t ± (b-a) * sqrt(log((pi^2 * t^2) / (c*alpha)) / (2*t))
    where c = 3 for two-sided, c = 6 for one-sided.

    The constant pi^2/6 comes from sum_{t=1}^inf 1/t^2 = pi^2/6.
    For two-sided intervals, we use 3 = 6/2 in the denominator since
    we need alpha/2 per tail.
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
        self._diag = DiagnosticsSetup(spec)

    def update(self, x: float) -> None:
        """Update with new observation."""
        x_checked = apply_diagnostics(
            x, self._diag.range_checker, self._diag.missingness, self._diag.drift_detector
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
                tier=self._diag.diagnostics.tier,
                diagnostics=self._diag.diagnostics,
            )

        # Time-uniform Hoeffding bound via union over t with 1/t^2 schedule.
        # pi^2/6 = sum_{t=1}^inf 1/t^2. For two-sided: use alpha/2 per tail -> 3 instead of 6.
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
            tier=self._diag.diagnostics.tier,
            diagnostics=self._diag.diagnostics.snapshot(),
        )

    def reset(self) -> None:
        """Reset to initial state."""
        self._estimator.reset()
        self._diag.reset()
