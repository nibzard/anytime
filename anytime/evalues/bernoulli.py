"""One-sample e-values for Bernoulli data."""

import math
from scipy.special import betainc, betaln

from anytime.spec import StreamSpec
from anytime.types import EValue, GuaranteeTier
from anytime.core.estimators import OnlineMean
from anytime.errors import AssumptionViolationError
from anytime.diagnostics.checks import DiagnosticsSetup, apply_diagnostics


class BernoulliMixtureE:
    """One-sample e-value for Bernoulli data using beta-binomial mixtures.

    Tests H0: p = p0 (two-sided) or H0: p <= p0 / p >= p0 (one-sided).
    Uses a beta prior mixture over the alternative space.
    """

    def __init__(
        self,
        spec: StreamSpec,
        p0: float = 0.5,
        side: str = "two",
        a: float = 0.5,
        b: float = 0.5,
    ):
        """Initialize Bernoulli e-value test.

        Args:
            spec: StreamSpec for this test
            p0: Null hypothesis value in (0,1)
            side: "two" (p = p0), "ge" (p > p0), or "le" (p < p0)
            a: Beta prior alpha
            b: Beta prior beta
        """
        if spec.kind != "bernoulli" or spec.support != (0.0, 1.0):
            raise ValueError("BernoulliMixtureE requires kind='bernoulli' and support=(0.0, 1.0)")
        if not 0.0 < p0 < 1.0:
            raise ValueError(f"p0 must be in (0,1), got {p0}")
        if side not in ("two", "ge", "le"):
            raise ValueError(f"side must be 'two', 'ge', or 'le', got {side}")
        if a <= 0 or b <= 0:
            raise ValueError("Beta prior parameters must be positive")

        self.spec = spec
        self.p0 = p0
        self.side = side
        self.a = a
        self.b = b
        self._estimator = OnlineMean()
        self._sum = 0.0
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
            self._diag.diagnostics.tier = GuaranteeTier.DIAGNOSTIC
            raise AssumptionViolationError(
                f"Bernoulli data must be 0 or 1, got {x_checked}"
            )
        self._sum += x_checked
        self._estimator.update(x_checked)

    def evalue(self) -> EValue:
        """Get current e-value."""
        t = self._estimator.n

        if t == 0:
            return EValue(
                t=0,
                e=1.0,
                decision=False,
                alpha=self.spec.alpha,
                tier=self._diag.diagnostics.tier,
                diagnostics=self._diag.diagnostics,
            )

        s = self._sum
        log_beta_num = betaln(s + self.a, t - s + self.b)
        log_beta_den = betaln(self.a, self.b)

        if self.side == "two":
            log_tail = 0.0
            log_mass = 0.0
        else:
            inc_den = betainc(self.a, self.b, self.p0)
            inc_num = betainc(s + self.a, t - s + self.b, self.p0)
            if self.side == "ge":
                log_tail = math.log1p(-inc_num)
                log_mass = math.log1p(-inc_den)
            else:
                log_tail = math.log(inc_num)
                log_mass = math.log(inc_den)

        log_e = (
            log_beta_num
            + log_tail
            - log_beta_den
            - log_mass
            - s * math.log(self.p0)
            - (t - s) * math.log1p(-self.p0)
        )

        e = math.exp(log_e) if log_e > -745 else 0.0
        decision = e >= 1 / self.spec.alpha

        return EValue(
            t=t,
            e=e,
            decision=decision,
            alpha=self.spec.alpha,
            tier=self._diag.diagnostics.tier,
            diagnostics=self._diag.diagnostics.snapshot(),
        )

    def reset(self) -> None:
        """Reset to initial state."""
        self._estimator.reset()
        self._sum = 0.0
        self._diag.reset()
