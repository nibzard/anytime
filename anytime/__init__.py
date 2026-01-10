"""Anytime: Peeking-safe streaming inference for A/B tests and online metrics."""

__version__ = "0.0.0"

# Core types and specs
from anytime.spec import StreamSpec, ABSpec
from anytime.types import GuaranteeTier, Interval, EValue

# Public API
__all__ = [
    "__version__",
    "StreamSpec",
    "ABSpec",
    "GuaranteeTier",
    "Interval",
    "EValue",
]
