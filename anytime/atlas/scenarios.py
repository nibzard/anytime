"""Scenario generators for anytime inference benchmarking.

Provides predefined scenarios covering various distributions, effect sizes,
and data pathologies to stress-test confidence sequences and e-values.

Scenarios are based on idea.md Section 6:
- One-sample: 8 scenarios (Bernoulli variants, bounded continuous, drift, out-of-range)
- Two-sample: 8 scenarios (Bernoulli A/B, continuous, heteroscedastic, small/large effects)
"""

import random
from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy import stats

from anytime.atlas.types import Scenario, StoppingRule
from anytime.errors import ConfigError


def _validate_bernoulli_probability(p: float, name: str = "probability") -> None:
    """Validate that a probability is in valid range for Bernoulli.

    Args:
        p: Probability to validate
        name: Parameter name for error message

    Raises:
        ConfigError: If probability is outside [0, 1]
    """
    if not 0.0 <= p <= 1.0:
        raise ConfigError(
            f"Invalid Bernoulli {name}: {p}. Must be in [0, 1]."
        )


def _beta_params_from_mean(mean: float, concentration: float) -> tuple[float, float]:
    """Convert mean and concentration to Beta(alpha, beta)."""
    if not 0.0 < mean < 1.0:
        raise ConfigError(f"Beta mean must be in (0, 1), got {mean}")
    if concentration <= 0:
        raise ConfigError(f"Beta concentration must be positive, got {concentration}")
    alpha = mean * concentration
    beta = (1.0 - mean) * concentration
    return alpha, beta


def validate_bernoulli_ab_scenario(p_a: float, p_b: float) -> None:
    """Validate Bernoulli A/B scenario parameters.

    Args:
        p_a: Probability for arm A
        p_b: Probability for arm B

    Raises:
        ConfigError: If probabilities are invalid
    """
    _validate_bernoulli_probability(p_a, "p_a")
    _validate_bernoulli_probability(p_b, "p_b")

    # Additional bounds checks for realistic scenarios
    if p_a < 0.001 or p_a > 0.999:
        raise ConfigError(
            f"Bernoulli p_a={p_a} is too close to 0 or 1. "
            f"Use range [0.001, 0.999] for stable computation."
        )
    if p_b < 0.001 or p_b > 0.999:
        raise ConfigError(
            f"Bernoulli p_b={p_b} is too close to 0 or 1. "
            f"Use range [0.001, 0.999] for stable computation."
        )


def generate_bernoulli(p: float, n: int, seed: int) -> list[float]:
    """Generate Bernoulli samples."""
    rng = random.Random(seed)
    return [float(rng.random() < p) for _ in range(n)]


def generate_uniform(a: float, b: float, n: int, seed: int) -> list[float]:
    """Generate uniform samples."""
    rng = random.Random(seed)
    return [a + (b - a) * rng.random() for _ in range(n)]


def generate_beta_scaled(alpha: float, beta_param: float, n: int, seed: int) -> list[float]:
    """Generate samples from Beta distribution scaled to [0,1]."""
    rng = np.random.default_rng(seed)
    return list(rng.beta(alpha, beta_param, n))


def generate_bimodal_mixture(
    mu1: float,
    mu2: float,
    w1: float,
    n: int,
    seed: int,
    concentration: float = 50.0,
) -> list[float]:
    """Generate bimodal mixture with two Beta components.

    Args:
        mu1: Mean for first cluster in (0, 1)
        mu2: Mean for second cluster in (0, 1)
        w1: Weight for first cluster (probability of choosing cluster 1)
        n: Number of samples
        seed: Random seed
        concentration: Beta concentration (higher -> tighter clusters)
    """
    rng = np.random.default_rng(seed)
    alpha1, beta1 = _beta_params_from_mean(mu1, concentration)
    alpha2, beta2 = _beta_params_from_mean(mu2, concentration)
    pick_first = rng.random(n) < w1
    samples = np.empty(n, dtype=float)
    n_first = int(pick_first.sum())
    n_second = n - n_first
    if n_first:
        samples[pick_first] = rng.beta(alpha1, beta1, n_first)
    if n_second:
        samples[~pick_first] = rng.beta(alpha2, beta2, n_second)
    return list(samples)


def generate_drift_bernoulli(
    p_start: float, p_end: float, n: int, seed: int
) -> list[float]:
    """Generate Bernoulli with probability ramping from p_start to p_end.

    Probability linearly interpolates from p_start to p_end over the sequence.
    """
    rng = random.Random(seed)
    samples = []
    for i in range(n):
        t = i / max(1, n - 1)  # Normalized time [0, 1]
        p = p_start + t * (p_end - p_start)
        samples.append(float(rng.random() < p))
    return samples


def generate_ab_bernoulli(
    p_a: float, p_b: float, n: int, seed: int
) -> list[tuple[str, float]]:
    """Generate paired A/B Bernoulli samples.

    Alternates between arms for fair pairing.
    """
    rng = random.Random(seed)
    data = []
    for i in range(n):
        if i % 2 == 0:
            data.append(("A", float(rng.random() < p_a)))
        else:
            data.append(("B", float(rng.random() < p_b)))
    return data


def generate_ab_imbalance(
    p_a: float, p_b: float, n: int, seed: int, ratio_a: float = 0.7
) -> list[tuple[str, float]]:
    """Generate A/B samples with imbalance (70/30 by default)."""
    rng = random.Random(seed)
    data = []
    for i in range(n):
        if rng.random() < ratio_a:
            data.append(("A", float(rng.random() < p_a)))
        else:
            data.append(("B", float(rng.random() < p_b)))
    return data


def generate_ab_beta(
    mean_a: float,
    mean_b: float,
    n: int,
    seed: int,
    concentration_a: float = 10.0,
    concentration_b: float | None = None,
    ratio_a: float = 0.5,
) -> list[tuple[str, float]]:
    """Generate A/B samples from Beta distributions with specified means."""
    if concentration_b is None:
        concentration_b = concentration_a

    alpha_a, beta_a = _beta_params_from_mean(mean_a, concentration_a)
    alpha_b, beta_b = _beta_params_from_mean(mean_b, concentration_b)

    rng = np.random.default_rng(seed)
    data: list[tuple[str, float]] = []

    for i in range(n):
        if ratio_a == 0.5:
            arm = "A" if i % 2 == 0 else "B"
        else:
            arm = "A" if rng.random() < ratio_a else "B"

        if arm == "A":
            value = rng.beta(alpha_a, beta_a)
        else:
            value = rng.beta(alpha_b, beta_b)
        data.append((arm, float(value)))

    return data


# ============================================================================
# One-sample scenarios
# ============================================================================

def one_sample_scenarios(n_max: int = 500) -> list[Scenario]:
    """Generate the 8 one-sample scenarios from idea.md.

    Args:
        n_max: Maximum horizon for scenarios

    Returns:
        List of Scenario objects
    """
    scenarios = [
        # 1. Bernoulli(p=0.1), fixed horizon
        Scenario(
            name="bernoulli_p01_fixed",
            true_mean=0.1,
            distribution="bernoulli",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=42,
            is_null=False,
        ),

        # 2. Bernoulli(p=0.1), stop when CI excludes 0.1
        Scenario(
            name="bernoulli_p01_ci_stop",
            true_mean=0.1,
            distribution="bernoulli",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=43,
            is_null=False,
        ),

        # 3. Bernoulli(p=0.1), periodic looks
        Scenario(
            name="bernoulli_p01_periodic",
            true_mean=0.1,
            distribution="bernoulli",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=44,
            is_null=False,
        ),

        # 4. Bounded Beta(2,8) scaled to [0,1], low variance
        Scenario(
            name="beta_2_8_low_variance",
            true_mean=2.0 / (2.0 + 8.0),  # 0.2
            distribution="uniform",  # Will use beta generator
            support=(0.0, 1.0),
            n_max=n_max,
            seed=45,
            is_null=False,
        ),

        # 5. Bounded uniform [0,1], high variance
        Scenario(
            name="uniform_0_1_high_variance",
            true_mean=0.5,
            distribution="uniform",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=46,
            is_null=False,
        ),

        # 6. Bimodal mixture
        Scenario(
            name="bimodal_mixture",
            true_mean=0.26,  # 90% near 0.2, 10% near 0.8
            distribution="uniform",  # Will use mixture generator
            support=(0.0, 1.0),
            n_max=n_max,
            seed=47,
            is_null=False,
        ),

        # 7. Drift scenario
        Scenario(
            name="drift_ramp",
            true_mean=0.15,  # Average of 0.1 to 0.2
            distribution="bernoulli",  # Will use drift generator
            support=(0.0, 1.0),
            n_max=n_max,
            seed=48,
            is_null=False,
        ),

        # 8. Null scenario for Type I checking
        Scenario(
            name="bernoulli_null",
            true_mean=0.5,
            distribution="bernoulli",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=49,
            is_null=True,
        ),
    ]
    return scenarios


# ============================================================================
# Two-sample scenarios
# ============================================================================

def two_sample_scenarios(n_max: int = 500) -> list[Scenario]:
    """Generate the 8 two-sample scenarios from idea.md.

    Args:
        n_max: Maximum horizon for scenarios

    Returns:
        List of Scenario objects
    """
    scenarios = [
        # 9) Bernoulli A:0.10 vs B:0.11, stop when CI excludes 0
        Scenario(
            name="ab_bernoulli_10_vs_11",
            true_mean=0.105,  # Average of 0.10 and 0.11
            true_lift=0.01,
            distribution="bernoulli",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=42,
            is_null=False,
        ),

        # 10) Bernoulli A:0.10 vs B:0.10 (null)
        Scenario(
            name="ab_bernoulli_null",
            true_mean=0.10,
            true_lift=0.0,
            distribution="bernoulli",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=43,
            is_null=True,
        ),

        # 11) Bounded continuous Beta comparison
        Scenario(
            name="ab_beta_continuous",
            true_mean=0.21,  # Approx average
            true_lift=0.01,
            distribution="uniform",  # Will use beta generators
            support=(0.0, 1.0),
            n_max=n_max,
            seed=44,
            is_null=False,
        ),

        # 12) Heteroscedastic (same mean, different variance)
        Scenario(
            name="ab_heteroscedastic",
            true_mean=0.5,
            true_lift=0.0,
            distribution="uniform",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=45,
            is_null=False,
        ),

        # 13) Small effect regime
        Scenario(
            name="ab_small_effect",
            true_mean=0.25,
            true_lift=0.002,
            distribution="bernoulli",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=46,
            is_null=False,
        ),

        # 14) Strong effect regime
        Scenario(
            name="ab_strong_effect",
            true_mean=0.275,
            true_lift=0.05,
            distribution="bernoulli",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=47,
            is_null=False,
        ),

        # 15) Imbalanced assignment
        Scenario(
            name="ab_imbalanced_70_30",
            true_mean=0.20,
            true_lift=0.01,
            distribution="bernoulli",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=48,
            is_null=False,
        ),

        # 16) Another null for e-value Type I
        Scenario(
            name="ab_bernoulli_null_ev",
            true_mean=0.25,
            true_lift=0.0,
            distribution="bernoulli",
            support=(0.0, 1.0),
            n_max=n_max,
            seed=49,
            is_null=True,
        ),
    ]
    return scenarios


# ============================================================================
# Stopping rules
# ============================================================================

def fixed_horizon_rule() -> StoppingRule | None:
    """Fixed horizon - never stop early (None means run to n_max)."""
    return None


def exclude_threshold_rule(
    threshold: float = 0.0, direction: str = "both"
) -> StoppingRule:
    """Stop when confidence interval excludes threshold.

    Args:
        threshold: Value to check exclusion against (usually 0 for lift)
        direction: "both", "lower", or "upper"
    """

    def fn(iv, t):
        if direction == "lower":
            return iv.lo > threshold
        elif direction == "upper":
            return iv.hi < threshold
        else:  # both
            return iv.lo > threshold or iv.hi < threshold

    return StoppingRule(
        name=f"exclude_{direction}_{threshold}",
        fn=fn,
    )


def periodic_look_rule(every: int = 50) -> StoppingRule:
    """Check stopping condition at periodic intervals.

    This doesn't stop by itself - it's a modifier for other rules.
    For now, returns None (combined with actual stopping in config).
    """
    return None


# ============================================================================
# Custom data generators for special scenarios
# ============================================================================

class OneSampleGenerator:
    """Helper for generating one-sample data with special distributions."""

    @staticmethod
    def get(scenario: Scenario, n: int, offset: int = 0) -> list[float]:
        """Generate data for a one-sample scenario.

        Args:
            scenario: Scenario definition
            n: Number of samples
            offset: Seed offset for Monte Carlo runs

        Returns:
            List of samples
        """
        seed = scenario.seed + offset
        name = scenario.name

        if "beta" in name and "low_variance" in name:
            # Beta(2, 8) scaled
            return generate_beta_scaled(2.0, 8.0, n, seed)
        elif "bimodal" in name:
            # 90% near 0.2, 10% near 0.8
            return generate_bimodal_mixture(0.2, 0.8, 0.9, n, seed)
        elif "drift" in name:
            # Ramp from 0.1 to 0.2
            return generate_drift_bernoulli(0.1, 0.2, n, seed)
        elif scenario.distribution == "bernoulli":
            return generate_bernoulli(scenario.true_mean, n, seed)
        else:  # uniform or default
            return generate_uniform(scenario.support[0], scenario.support[1], n, seed)


class TwoSampleGenerator:
    """Helper for generating two-sample A/B data with special distributions."""

    @staticmethod
    def get(scenario: Scenario, n: int, offset: int = 0) -> list[tuple[str, float]]:
        """Generate data for a two-sample scenario.

        Args:
            scenario: Scenario definition
            n: Number of samples (total, split across arms)
            offset: Seed offset for Monte Carlo runs

        Returns:
            List of (arm, value) tuples
        """
        seed = scenario.seed + offset
        name = scenario.name

        # Compute arm probabilities from mean and lift
        p_a = scenario.true_mean - scenario.true_lift / 2
        p_b = scenario.true_mean + scenario.true_lift / 2

        if scenario.distribution == "bernoulli":
            _validate_bernoulli_probability(p_a, "p_a")
            _validate_bernoulli_probability(p_b, "p_b")
            if "imbalanced" in name:
                return generate_ab_imbalance(p_a, p_b, n, seed, ratio_a=0.7)
            return generate_ab_bernoulli(p_a, p_b, n, seed)

        # Default to bounded continuous Beta distributions for non-Bernoulli scenarios.
        if "heteroscedastic" in name:
            return generate_ab_beta(
                p_a,
                p_b,
                n,
                seed,
                concentration_a=40.0,
                concentration_b=8.0,
            )
        if "beta" in name:
            return generate_ab_beta(p_a, p_b, n, seed, concentration_a=10.0)

        return generate_ab_beta(p_a, p_b, n, seed, concentration_a=12.0)
