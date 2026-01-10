"""Two-sample Empirical Bernstein confidence sequences."""

from anytime.spec import ABSpec, StreamSpec
from anytime.types import Interval, GuaranteeTier
from anytime.diagnostics.checks import Diagnostics
from anytime.cs.empirical_bernstein import EmpiricalBernsteinCS


class TwoSampleEmpiricalBernsteinCS:
    """Two-sample Empirical Bernstein confidence sequence.

    Uses a union bound over two one-sample empirical Bernstein sequences.
    """

    def __init__(self, spec: ABSpec):
        if spec.kind not in {"bounded", "bernoulli"}:
            raise ValueError("TwoSampleEmpiricalBernsteinCS requires bounded or bernoulli data")
        if not spec.two_sided:
            raise ValueError("TwoSampleEmpiricalBernsteinCS supports two-sided intervals only")
        alpha = spec.alpha / 2.0
        stream_spec = StreamSpec(
            alpha=alpha,
            support=spec.support,
            kind=spec.kind,
            two_sided=True,
            name=spec.name,
            clip_mode=spec.clip_mode,
        )
        self.spec = spec
        self._cs_a = EmpiricalBernsteinCS(stream_spec)
        self._cs_b = EmpiricalBernsteinCS(stream_spec)

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
            diagnostics = self._merge_diagnostics(iv_a.diagnostics, iv_b.diagnostics)

        if iv_a.t == 0 or iv_b.t == 0:
            return Interval(
                t=t,
                estimate=0.0,
                lo=float("-inf"),
                hi=float("inf"),
                alpha=self.spec.alpha,
                tier=GuaranteeTier.GUARANTEED,
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

    @staticmethod
    def _merge_diagnostics(
        diag_a: Diagnostics | None,
        diag_b: Diagnostics | None,
    ) -> Diagnostics:
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
