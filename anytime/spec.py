"""Specification classes for anytime inference."""

from dataclasses import dataclass
from anytime.errors import ConfigError


@dataclass(frozen=True)
class StreamSpec:
    """Specification for one-sample streaming inference.

    Attributes:
        alpha: Significance level (e.g., 0.05)
        support: (lower, upper) bounds for data (None for unbounded)
        kind: "bounded", "subgaussian", or "bernoulli"
        two_sided: Whether to compute two-sided interval
        name: Optional name for this stream
        clip_mode: "error" or "clip" for out-of-range values
    """

    alpha: float
    support: tuple[float | None, float | None]
    kind: str
    two_sided: bool
    name: str = ""
    clip_mode: str = "error"

    def __post_init__(self):
        # Validate alpha
        if not 0 < self.alpha < 1:
            raise ConfigError(f"alpha must be in (0,1), got {self.alpha}")

        # Validate support
        lo, hi = self.support
        if lo is not None and hi is not None and lo >= hi:
            raise ConfigError(f"support lower >= upper: {self.support}")

        # Validate kind
        valid_kinds = {"bounded", "subgaussian", "bernoulli"}
        if self.kind not in valid_kinds:
            raise ConfigError(f"kind must be one of {valid_kinds}, got {self.kind}")

        # Validate clip_mode
        if self.clip_mode not in {"error", "clip"}:
            raise ConfigError(f"clip_mode must be 'error' or 'clip', got {self.clip_mode}")

        # Validate kind-specific requirements
        if self.kind == "bounded" and (lo is None or hi is None):
            raise ConfigError("bounded kind requires support=(lo, hi) with finite bounds")

        if self.kind == "bernoulli" and self.support != (0.0, 1.0):
            raise ConfigError("bernoulli kind requires support=(0.0, 1.0)")


@dataclass(frozen=True)
class ABSpec:
    """Specification for two-sample A/B testing.

    Attributes:
        alpha: Significance level (e.g., 0.05)
        support: (lower, upper) bounds for both arms (None for unbounded)
        kind: "bounded", "subgaussian", or "bernoulli"
        two_sided: Whether to compute two-sided interval
        name: Optional name for this test
        clip_mode: "error" or "clip" for out-of-range values
    """

    alpha: float
    support: tuple[float | None, float | None]
    kind: str
    two_sided: bool
    name: str = ""
    clip_mode: str = "error"

    def __post_init__(self):
        # Validate alpha
        if not 0 < self.alpha < 1:
            raise ConfigError(f"alpha must be in (0,1), got {self.alpha}")

        # Validate support
        lo, hi = self.support
        if lo is not None and hi is not None and lo >= hi:
            raise ConfigError(f"support lower >= upper: {self.support}")

        # Validate kind
        valid_kinds = {"bounded", "subgaussian", "bernoulli"}
        if self.kind not in valid_kinds:
            raise ConfigError(f"kind must be one of {valid_kinds}, got {self.kind}")

        # Validate clip_mode
        if self.clip_mode not in {"error", "clip"}:
            raise ConfigError(f"clip_mode must be 'error' or 'clip', got {self.clip_mode}")

        # Validate kind-specific requirements
        if self.kind == "bounded" and (lo is None or hi is None):
            raise ConfigError("bounded kind requires support=(lo, hi) with finite bounds")

        if self.kind == "bernoulli" and self.support != (0.0, 1.0):
            raise ConfigError("bernoulli kind requires support=(0.0, 1.0)")
