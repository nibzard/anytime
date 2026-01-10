"""Online estimators for mean and variance."""

import math
from dataclasses import dataclass


@dataclass
class OnlineMean:
    """Welford's online mean estimator.

    Provides numerically stable online mean computation.
    """

    n: int = 0
    _mean: float = 0.0

    def update(self, x: float) -> None:
        """Update with new observation."""
        self.n += 1
        delta = x - self._mean
        self._mean += delta / self.n

    @property
    def mean(self) -> float:
        return self._mean

    def reset(self) -> None:
        """Reset to initial state."""
        self.n = 0
        self._mean = 0.0


@dataclass
class OnlineVariance:
    """Welford's online variance estimator.

    Provides numerically stable online mean and variance computation.
    Uses the corrected two-pass algorithm (similar to Welford's method).
    """

    n: int = 0
    _mean: float = 0.0
    _m2: float = 0.0  # Sum of squared deviations

    def update(self, x: float) -> None:
        """Update with new observation."""
        self.n += 1
        delta = x - self._mean
        self._mean += delta / self.n
        delta2 = x - self._mean
        self._m2 += delta * delta2

    @property
    def mean(self) -> float:
        return self._mean

    @property
    def variance(self) -> float:
        """Sample variance (unbiased estimator)."""
        if self.n <= 1:
            return 0.0
        return self._m2 / (self.n - 1)

    @property
    def var_pop(self) -> float:
        """Population variance (MLE estimator)."""
        if self.n == 0:
            return 0.0
        return self._m2 / self.n

    def reset(self) -> None:
        """Reset to initial state."""
        self.n = 0
        self._mean = 0.0
        self._m2 = 0.0
