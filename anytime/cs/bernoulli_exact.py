"""Bernoulli (binary) confidence sequences.

References:
    - The beta-binomial mixture e-process is a special case of the
      "Universal inference" approach by Wasserman et al. (2020).
    - Related to the "clopper-Pearson" style time-uniform bounds using
      beta conjugate priors.

E-process formula:
    E_t(p) = Beta(S_t+a, t-S_t+b) / (Beta(a,b) * p^{S_t} * (1-p)^{t-S_t})

    where S_t is the number of successes, t is total trials, and a,b are
    beta prior parameters (default a=b=0.5 gives Jeffreys prior).

The confidence sequence inverts this e-process: {p: E_t(p) < 1/alpha}.

For one-sided intervals, we use 2*alpha in the threshold, giving a tighter
bound that's valid for one-sided inference.
"""

import math
from scipy.optimize import brentq
from scipy.special import betaln

from anytime.spec import StreamSpec
from anytime.types import Interval, GuaranteeTier
from anytime.core.estimators import OnlineMean
from anytime.errors import AssumptionViolationError
from anytime.diagnostics.checks import DiagnosticsSetup, apply_diagnostics


class BernoulliCS:
    """Time-uniform confidence sequence for Bernoulli (0/1) data.

    Uses a beta-binomial mixture martingale and inverts the e-process:
        E_t(p) = Beta(S_t+a, t-S_t+b) / (Beta(a,b) * p^{S_t} * (1-p)^{t-S_t})
    The confidence sequence is {p: E_t(p) < 1/alpha}.

    For one-sided intervals, uses 2*alpha in the threshold, producing
    tighter bounds valid for one-sided inference.

    Parameters:
        a, b: Beta prior parameters (default 0.5, 0.5 for Jeffreys prior)
    """

    def __init__(self, spec: StreamSpec, a: float = 0.5, b: float = 0.5):
        if spec.kind != "bernoulli" or spec.support != (0.0, 1.0):
            raise ValueError("BernoulliCS requires kind='bernoulli' and support=(0.0, 1.0)")
        if a <= 0 or b <= 0:
            raise ValueError("Beta prior parameters must be positive")
        self.spec = spec
        self.a = a
        self.b = b
        self._estimator = OnlineMean()
        self._sum = 0.0  # Sum of observations (number of successes)
        self._diag = DiagnosticsSetup(spec)

    def update(self, x: float) -> None:
        """Update with new observation (should be 0 or 1)."""
        x_checked = apply_diagnostics(
            x, self._diag.range_checker, self._diag.missingness, self._diag.drift_detector
        )
        if x_checked is None:
            return
        if x_checked not in (0.0, 1.0):
            self._diag.diagnostics.out_of_range_count += 1
            from anytime.types import GuaranteeTier
            self._diag.diagnostics.tier = GuaranteeTier.DIAGNOSTIC
            raise AssumptionViolationError(
                f"Bernoulli data must be 0 or 1, got {x_checked}"
            )
        self._sum += x_checked
        self._estimator.update(x_checked)

    def _log_evalue(self, p: float, t: int) -> float:
        s = self._sum
        if p <= 0.0 or p >= 1.0:
            return float("inf")
        return (
            betaln(s + self.a, t - s + self.b)
            - betaln(self.a, self.b)
            - s * math.log(p)
            - (t - s) * math.log1p(-p)
        )

    def interval(self) -> Interval:
        """Get current confidence interval."""
        t = self._estimator.n
        mean = self._estimator.mean

        if t == 0:
            return Interval(
                t=0,
                estimate=0.0,
                lo=0.0,
                hi=1.0,
                alpha=self.spec.alpha,
                tier=self._diag.diagnostics.tier,
                diagnostics=self._diag.diagnostics,
            )

        # For one-sided, use 2*alpha in the e-value threshold (gives tighter bound)
        target = math.log(1.0 / (2.0 * self.spec.alpha if not self.spec.two_sided else self.spec.alpha))
        eps = 1e-12

        def f(p: float) -> float:
            return self._log_evalue(p, t) - target

        # Handle edge cases explicitly.
        if self._sum == 0:
            lo = 0.0
            hi = self._find_upper_root(f, eps, 1.0 - eps, mean)
        elif self._sum == t:
            hi = 1.0
            lo = self._find_lower_root(f, eps, 1.0 - eps, mean)
        else:
            lo = self._find_lower_root(f, eps, 1.0 - eps, mean)
            hi = self._find_upper_root(f, eps, 1.0 - eps, mean)

        return Interval(
            t=t,
            estimate=mean,
            lo=lo,
            hi=hi,
            alpha=self.spec.alpha,
            tier=self._diag.diagnostics.tier,
            diagnostics=self._diag.diagnostics.snapshot(),
        )

    @staticmethod
    def _find_lower_root(f, eps: float, hi: float, mean: float) -> float:
        if mean <= eps:
            return 0.0
        left = eps
        right = min(mean, hi)
        if f(left) <= 0:
            return 0.0
        if f(right) >= 0:
            return right
        return brentq(f, left, right)

    @staticmethod
    def _find_upper_root(f, eps: float, hi: float, mean: float) -> float:
        if mean >= hi:
            return 1.0
        left = max(mean, eps)
        right = hi
        if f(right) <= 0:
            return 1.0
        if f(left) >= 0:
            return left
        return brentq(f, left, right)

    def reset(self) -> None:
        """Reset to initial state."""
        self._estimator.reset()
        self._sum = 0.0
        self._diag.reset()
