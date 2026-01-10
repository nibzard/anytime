"""Benchmarking framework for anytime inference methods."""

import random
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from anytime.spec import StreamSpec, ABSpec
from anytime.cs.hoeffding import HoeffdingCS
from anytime.cs.empirical_bernstein import EmpiricalBernsteinCS
from anytime.cs.bernoulli_exact import BernoulliCS
from anytime.twosample.hoeffding import TwoSampleHoeffdingCS
from anytime.twosample.empirical_bernstein import TwoSampleEmpiricalBernsteinCS


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


@dataclass
class Metrics:
    """Aggregated metrics from Monte Carlo simulations.

    Attributes:
        coverage: Anytime coverage (true value in CI for all observed t)
        final_coverage: Coverage at final (stop) time
        type_i_error: Proportion of null simulations where we rejected
        power: Proportion of alt simulations where we detected effect
        avg_width: Average final interval width
        median_stop_time: Median stopping time
        avg_runtime: Average runtime per simulation
    """

    coverage: float = 0.0
    final_coverage: float = 0.0
    type_i_error: float = 0.0
    power: float = 0.0
    avg_width: float = 0.0
    median_stop_time: float = 0.0
    avg_runtime: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "coverage": self.coverage,
            "final_coverage": self.final_coverage,
            "type_i_error": self.type_i_error,
            "power": self.power,
            "avg_width": self.avg_width,
            "median_stop_time": self.median_stop_time,
            "avg_runtime": self.avg_runtime,
        }


def generate_bernoulli(p: float, n: int, seed: int) -> list[float]:
    """Generate Bernoulli samples."""
    rng = random.Random(seed)
    return [float(rng.random() < p) for _ in range(n)]


def generate_uniform(a: float, b: float, n: int, seed: int) -> list[float]:
    """Generate uniform samples."""
    rng = random.Random(seed)
    return [a + (b - a) * rng.random() for _ in range(n)]


def generate_ab_bernoulli(p_a: float, p_b: float, n: int, seed: int) -> list[tuple[str, float]]:
    """Generate paired A/B Bernoulli samples."""
    rng = random.Random(seed)
    data = []
    for i in range(n):
        # Alternate between arms
        if i % 2 == 0:
            data.append(("A", float(rng.random() < p_a)))
        else:
            data.append(("B", float(rng.random() < p_b)))
    return data


class AtlasRunner:
    """Run Monte Carlo benchmarks for anytime inference methods."""

    def __init__(self, n_sim: int = 1000):
        self.n_sim = n_sim

    def run_one_sample(
        self,
        scenario: Scenario,
        spec: StreamSpec,
        cs_class: type,
        stopping_rule: StoppingRule | None = None,
    ) -> Metrics:
        """Run one-sample Monte Carlo benchmark.

        Args:
            scenario: Test scenario
            spec: Stream specification
            cs_class: Confidence sequence class
            stopping_rule: Optional stopping rule (None = run to n_max)

        Returns:
            Aggregated metrics
        """
        import time

        anytime_coverage_count = 0
        final_coverage_count = 0
        stop_count = 0
        widths = []
        stop_times = []
        runtimes = []

        for i in range(self.n_sim):
            t0 = time.time()

            # Generate data
            if scenario.distribution == "bernoulli":
                data = generate_bernoulli(scenario.true_mean, scenario.n_max, scenario.seed + i)
            elif scenario.distribution == "uniform":
                data = generate_uniform(scenario.support[0], scenario.support[1], scenario.n_max, scenario.seed + i)
            else:
                raise ValueError(f"Unknown distribution: {scenario.distribution}")

            # Run CS
            cs = cs_class(spec)
            stopped = False
            covered_all = True

            for t, x in enumerate(data, 1):
                cs.update(x)
                iv = cs.interval()

                if not (iv.lo <= scenario.true_mean <= iv.hi):
                    covered_all = False

                if stopping_rule and not stopped:
                    if stopping_rule.fn(iv, t):
                        stop_times.append(t)
                        stop_count += 1
                        stopped = True
                        break

            if not stopped:
                stop_times.append(scenario.n_max)

            iv = cs.interval()
            if covered_all:
                anytime_coverage_count += 1
            if iv.lo <= scenario.true_mean <= iv.hi:
                final_coverage_count += 1

            widths.append(iv.width)
            runtimes.append(time.time() - t0)

        return Metrics(
            coverage=anytime_coverage_count / self.n_sim,
            final_coverage=final_coverage_count / self.n_sim,
            type_i_error=(stop_count / self.n_sim) if scenario.is_null else 0.0,
            power=(stop_count / self.n_sim) if not scenario.is_null else 0.0,
            avg_width=np.mean(widths),
            median_stop_time=np.median(stop_times),
            avg_runtime=np.mean(runtimes),
        )

    def run_two_sample(
        self,
        scenario: Scenario,
        spec: ABSpec,
        cs_class: type,
        stopping_rule: StoppingRule | None = None,
    ) -> Metrics:
        """Run two-sample Monte Carlo benchmark.

        Args:
            scenario: Test scenario
            spec: AB specification
            cs_class: Confidence sequence class
            stopping_rule: Optional stopping rule

        Returns:
            Aggregated metrics
        """
        import time

        anytime_coverage_count = 0
        final_coverage_count = 0
        stop_count = 0
        widths = []
        stop_times = []
        runtimes = []

        for i in range(self.n_sim):
            t0 = time.time()

            # Generate data
            if scenario.distribution == "bernoulli":
                p_a = scenario.true_mean - scenario.true_lift / 2
                p_b = scenario.true_mean + scenario.true_lift / 2
                data = generate_ab_bernoulli(p_a, p_b, scenario.n_max, scenario.seed + i)
            else:
                raise ValueError(f"Unknown distribution for AB: {scenario.distribution}")

            # Run CS
            cs = cs_class(spec)
            stopped = False
            covered_all = True

            for j, (arm, x) in enumerate(data):
                cs.update((arm, x))
                iv = cs.interval()

                if not (iv.lo <= scenario.true_lift <= iv.hi):
                    covered_all = False

                if stopping_rule and not stopped:
                    if stopping_rule.fn(iv, j + 1):
                        stop_times.append(j + 1)
                        stop_count += 1
                        stopped = True
                        break

            if not stopped:
                stop_times.append(len(data))

            iv = cs.interval()
            if covered_all:
                anytime_coverage_count += 1
            if iv.lo <= scenario.true_lift <= iv.hi:
                final_coverage_count += 1

            widths.append(iv.width)
            runtimes.append(time.time() - t0)

        return Metrics(
            coverage=anytime_coverage_count / self.n_sim,
            final_coverage=final_coverage_count / self.n_sim,
            type_i_error=(stop_count / self.n_sim) if scenario.is_null else 0.0,
            power=(stop_count / self.n_sim) if not scenario.is_null else 0.0,
            avg_width=np.mean(widths),
            median_stop_time=np.median(stop_times),
            avg_runtime=np.mean(runtimes),
        )
