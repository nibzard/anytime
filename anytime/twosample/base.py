"""Base class for two-sample confidence sequences."""

from abc import abstractmethod

from anytime.spec import ABSpec, StreamSpec
from anytime.types import Interval, GuaranteeTier
from anytime.diagnostics.checks import Diagnostics, merge_diagnostics


class TwoSampleCSBase:
    """Base class for two-sample confidence sequences.

    Reduces duplication between TwoSampleHoeffdingCS and TwoSampleEmpiricalBernsteinCS.
    """

    def __init__(self, spec: ABSpec, cs_class: type):
        """Initialize two-sample CS.

        Args:
            spec: A/B test specification
            cs_class: One-sample confidence sequence class to use for each arm
        """
        self.spec = spec
        # For two-sided: split alpha between two one-sample two-sided CS
        # For one-sided: use full alpha on each one-sample one-sided CS
        alpha = spec.alpha / 2.0 if spec.two_sided else spec.alpha
        stream_spec = StreamSpec(
            alpha=alpha,
            support=spec.support,
            kind=spec.kind,
            two_sided=spec.two_sided,
            name=spec.name,
            clip_mode=spec.clip_mode,
        )
        self._cs_a = cs_class(stream_spec)
        self._cs_b = cs_class(stream_spec)

    def update(self, pair: tuple[str, float]) -> None:
        """Update with new (arm, value) observation.

        Args:
            pair: (arm, value) where arm is "A" or "B"
        """
        arm, x = pair
        if arm == "A":
            self._cs_a.update(x)
        elif arm == "B":
            self._cs_b.update(x)
        else:
            raise ValueError(f"Invalid arm: {arm}. Must be 'A' or 'B'")

    def interval(self) -> Interval:
        """Get current confidence interval for mean difference."""
        iv_a = self._cs_a.interval()
        iv_b = self._cs_b.interval()
        t = iv_a.t + iv_b.t

        diagnostics = None
        if iv_a.diagnostics or iv_b.diagnostics:
            diagnostics = merge_diagnostics(iv_a.diagnostics, iv_b.diagnostics)

        if iv_a.t == 0 or iv_b.t == 0:
            tier = GuaranteeTier.GUARANTEED
            if diagnostics and diagnostics.tier == GuaranteeTier.DIAGNOSTIC:
                tier = GuaranteeTier.DIAGNOSTIC
            elif diagnostics and diagnostics.tier == GuaranteeTier.CLIPPED:
                tier = GuaranteeTier.CLIPPED
            return Interval(
                t=t,
                estimate=0.0,
                lo=float("-inf"),
                hi=float("inf"),
                alpha=self.spec.alpha,
                tier=tier,
                diagnostics=diagnostics,
            )

        diff = iv_b.estimate - iv_a.estimate
        lo = iv_b.lo - iv_a.hi
        hi = iv_b.hi - iv_a.lo
        tier = GuaranteeTier.GUARANTEED
        if GuaranteeTier.DIAGNOSTIC in (iv_a.tier, iv_b.tier):
            tier = GuaranteeTier.DIAGNOSTIC
        elif GuaranteeTier.CLIPPED in (iv_a.tier, iv_b.tier):
            tier = GuaranteeTier.CLIPPED

        return Interval(
            t=t,
            estimate=diff,
            lo=lo,
            hi=hi,
            alpha=self.spec.alpha,
            tier=tier,
            diagnostics=diagnostics,
        )

    def reset(self) -> None:
        """Reset to initial state."""
        self._cs_a.reset()
        self._cs_b.reset()
