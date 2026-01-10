"""Core data types for anytime inference."""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anytime.diagnostics.checks import Diagnostics


class GuaranteeTier(Enum):
    """Guarantee level based on assumption satisfaction."""

    GUARANTEED = "guaranteed"  # All assumptions satisfied
    CLIPPED = "clipped"  # Out-of-range values clipped
    DIAGNOSTIC = "diagnostic"  # Assumptions violated; no guarantee


@dataclass(frozen=True)
class Interval:
    """Confidence interval with metadata.

    Attributes:
        t: Current time step
        estimate: Point estimate (mean or mean difference)
        lo: Lower bound
        hi: Upper bound
        alpha: Significance level
        tier: Guarantee tier
        diagnostics: Optional diagnostics metadata
    """

    t: int
    estimate: float
    lo: float
    hi: float
    alpha: float
    tier: GuaranteeTier
    diagnostics: "Diagnostics | None" = None

    @property
    def width(self) -> float:
        return self.hi - self.lo


@dataclass(frozen=True)
class EValue:
    """E-value with metadata.

    Attributes:
        t: Current time step
        e: E-value
        decision: Whether to reject (e >= 1/alpha)
        alpha: Original significance level
        tier: Guarantee tier
        diagnostics: Optional diagnostics metadata
    """

    t: int
    e: float
    decision: bool
    alpha: float
    tier: GuaranteeTier
    diagnostics: "Diagnostics | None" = None
