"""Two-sample e-values for mean difference."""

import math
from collections import deque

from anytime.spec import ABSpec
from anytime.types import EValue
from anytime.diagnostics.checks import DiagnosticsSetup, apply_diagnostics, merge_diagnostics


class TwoSampleMeanMixtureE:
    """Two-sample e-value for bounded mean difference.

    Forms independent pairs and applies a one-sample bounded e-process to
    the paired differences. For H0: E[B] - E[A] <= delta0, define
    Y = (B - A - delta0) with range width 2(b-a).
    """

    def __init__(
        self,
        spec: ABSpec,
        delta0: float = 0.0,
        side: str = "ge",
        tau: float | None = None,
    ):
        if side not in ("ge", "le", "two"):
            raise ValueError(f"side must be 'ge', 'le', or 'two', got {side}")
        if spec.kind not in {"bounded", "bernoulli"}:
            raise ValueError("TwoSampleMeanMixtureE requires bounded or bernoulli data")
        lo, hi = spec.support
        if lo is None or hi is None:
            raise ValueError("TwoSampleMeanMixtureE requires finite support bounds")

        self.spec = spec
        self.delta0 = delta0
        self.side = side
        self._queue_a = deque()
        self._queue_b = deque()
        self._sum = 0.0
        self._pairs = 0

        self._range = hi - lo
        self._width = 2.0 * self._range
        self._c = (self._width ** 2) / 8.0
        self.tau = tau if tau is not None else 1.0 / self._width

        from anytime.spec import StreamSpec
        stream_spec = StreamSpec(
            alpha=spec.alpha,
            support=spec.support,
            kind=spec.kind,
            two_sided=spec.two_sided,
            name=spec.name,
            clip_mode=spec.clip_mode,
        )
        self._diag_a = DiagnosticsSetup(stream_spec)
        self._diag_b = DiagnosticsSetup(stream_spec)
        self._range_checker_a = self._diag_a.range_checker
        self._range_checker_b = self._diag_b.range_checker
        self._missingness_a = self._diag_a.missingness
        self._missingness_b = self._diag_b.missingness
        self._drift_a = self._diag_a.drift_detector
        self._drift_b = self._diag_b.drift_detector

    def update(self, pair: tuple[str, float]) -> None:
        """Update with new (arm, value) observation."""
        arm, x = pair
        if arm == "A":
            x_checked = apply_diagnostics(
                x, self._range_checker_a, self._missingness_a, self._drift_a
            )
            if x_checked is None:
                return
            self._queue_a.append(x_checked)
        elif arm == "B":
            x_checked = apply_diagnostics(
                x, self._range_checker_b, self._missingness_b, self._drift_b
            )
            if x_checked is None:
                return
            self._queue_b.append(x_checked)
        else:
            raise ValueError(f"Invalid arm: {arm}. Must be 'A' or 'B'")

        while self._queue_a and self._queue_b:
            a = self._queue_a.popleft()
            b = self._queue_b.popleft()
            self._sum += (b - a - self.delta0)
            self._pairs += 1

    def _e_from_sum(self, s: float, t: int) -> float:
        a = self._c * t + 1.0 / (2.0 * self.tau * self.tau)
        sqrt_a = math.sqrt(a)
        z = s / (2.0 * sqrt_a)

        # Compute in log space to prevent overflow
        # log_e = s^2/(4a) + log(1 + erf(z)) - log(tau) - 0.5*log(2a)
        log_exp_term = (s * s) / (4.0 * a)
        # Clamp log_exp_term to prevent overflow (exp(709) is near float64 limit)
        if log_exp_term > 700:
            log_exp_term = 700

        return (
            math.exp(log_exp_term)
            * (1.0 + math.erf(z))
            / (self.tau * math.sqrt(2.0 * a))
        )

    def evalue(self) -> EValue:
        """Get current e-value."""
        t = self._pairs

        diagnostics = merge_diagnostics(self._diag_a.diagnostics, self._diag_b.diagnostics)

        if t == 0:
            return EValue(
                t=0,
                e=1.0,
                decision=False,
                alpha=self.spec.alpha,
                tier=diagnostics.tier,
                diagnostics=diagnostics,
            )

        if self.side == "ge":
            e = self._e_from_sum(self._sum, t)
        elif self.side == "le":
            e = self._e_from_sum(-self._sum, t)
        else:
            e_ge = self._e_from_sum(self._sum, t)
            e_le = self._e_from_sum(-self._sum, t)
            e = 0.5 * (e_ge + e_le)

        decision = e >= 1 / self.spec.alpha

        return EValue(
            t=t,
            e=e,
            decision=decision,
            alpha=self.spec.alpha,
            tier=diagnostics.tier,
            diagnostics=diagnostics.snapshot(),
        )

    def reset(self) -> None:
        """Reset to initial state."""
        self._queue_a.clear()
        self._queue_b.clear()
        self._sum = 0.0
        self._pairs = 0
        self._diag_a.reset()
        self._diag_b.reset()
