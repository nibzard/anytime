"""Common types for atlas benchmarking."""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Scenario:
    """A benchmark scenario.

    Attributes:
        name: Scenario name
        true_mean: True mean for one-sample
        true_lift: True lift for two-sample (mean_B - mean_A)
        distribution: "bernoulli", "uniform", or "normal"
        support: (low, high) bounds
        n_max: Maximum sample size
        seed: Random seed
        is_null: Whether this scenario represents a null hypothesis
    """

    name: str
    true_mean: float | None = None
    true_lift: float | None = None
    distribution: str = "bernoulli"
    support: tuple[float, float] = (0.0, 1.0)
    n_max: int = 1000
    seed: int = 42
    is_null: bool = False

    def __post_init__(self):
        if self.distribution == "bernoulli" and self.support != (0.0, 1.0):
            raise ValueError("Bernoulli requires support=(0.0, 1.0)")


@dataclass
class StoppingRule:
    """A stopping rule for sequential tests.

    Attributes:
        name: Rule name
        fn: Function that takes (interval, t) and returns bool (stop)
    """

    name: str
    fn: Callable[[Any, int], bool]
