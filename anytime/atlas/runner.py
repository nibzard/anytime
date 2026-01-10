"""Benchmarking framework for anytime inference methods."""

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from anytime.spec import StreamSpec, ABSpec
from anytime.cs.hoeffding import HoeffdingCS
from anytime.cs.empirical_bernstein import EmpiricalBernsteinCS
from anytime.cs.bernoulli_exact import BernoulliCS
from anytime.twosample.hoeffding import TwoSampleHoeffdingCS
from anytime.twosample.empirical_bernstein import TwoSampleEmpiricalBernsteinCS
from anytime.atlas.types import Scenario, StoppingRule
from anytime.atlas.scenarios import (
    OneSampleGenerator,
    TwoSampleGenerator,
)


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
        evalue_decision_rate: Proportion of sims where e-value exceeded 1/alpha
        naive_peeking_error: Type I error under naive peeking (invalid baseline)
    """

    coverage: float = 0.0
    final_coverage: float = 0.0
    type_i_error: float = 0.0
    power: float = 0.0
    avg_width: float = 0.0
    median_stop_time: float = 0.0
    avg_runtime: float = 0.0
    evalue_decision_rate: float = 0.0
    naive_peeking_error: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "coverage": self.coverage,
            "final_coverage": self.final_coverage,
            "type_i_error": self.type_i_error,
            "power": self.power,
            "avg_width": self.avg_width,
            "median_stop_time": self.median_stop_time,
            "avg_runtime": self.avg_runtime,
            "evalue_decision_rate": self.evalue_decision_rate,
            "naive_peeking_error": self.naive_peeking_error,
        }


def naive_peeking_test(data: list[float], true_mean: float, alpha: float, check_interval: int = 10) -> tuple[bool, int]:
    """Simulate naive peeking with classical t-tests (INVALID baseline).

    This demonstrates why naive peeking is wrong: it inflates Type I error.

    Args:
        data: Stream of observations
        true_mean: Null hypothesis value
        alpha: Significance level
        check_interval: Check every n observations

    Returns:
        (rejected, stop_time): Whether we rejected and when
    """
    from scipy import stats

    n = len(data)
    for t in range(check_interval, n + 1, check_interval):
        sample = data[:t]
        if len(sample) < 2:
            continue
        # Classical t-test (INVALID under optional stopping!)
        _, pvalue = stats.ttest_1samp(sample, popmean=true_mean)
        if pvalue < alpha:
            return True, t
    return False, n


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
        evalue_class: type | None = None,
        track_naive_peeking: bool = False,
    ) -> Metrics:
        """Run one-sample Monte Carlo benchmark.

        Args:
            scenario: Test scenario
            spec: Stream specification
            cs_class: Confidence sequence class
            stopping_rule: Optional stopping rule (None = run to n_max)
            evalue_class: Optional e-value class for decision tracking
            track_naive_peeking: Whether to track naive peeking baseline

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
        evalue_decision_count = 0
        naive_peeking_count = 0

        for i in range(self.n_sim):
            t0 = time.time()

            # Generate data
            data = OneSampleGenerator.get(scenario, scenario.n_max, offset=i)

            # Track naive peeking (invalid baseline)
            if track_naive_peeking and scenario.is_null:
                rejected, _ = naive_peeking_test(data, scenario.true_mean, spec.alpha)
                if rejected:
                    naive_peeking_count += 1

            # Run CS
            cs = cs_class(spec)
            stopped = False
            covered_all = True

            # Run e-value in parallel if provided
            evalue = evalue_class(spec) if evalue_class else None
            evalue_decided_this_sim = False

            for t, x in enumerate(data, 1):
                cs.update(x)
                iv = cs.interval()

                if not (iv.lo <= scenario.true_mean <= iv.hi):
                    covered_all = False

                if evalue and not evalue_decided_this_sim:
                    evalue.update(x)
                    ev = evalue.evalue()
                    if ev.decision:
                        evalue_decision_count += 1
                        evalue_decided_this_sim = True  # Only count once per sim

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
            evalue_decision_rate=(evalue_decision_count / self.n_sim) if evalue_class else 0.0,
            naive_peeking_error=(naive_peeking_count / self.n_sim) if track_naive_peeking and scenario.is_null else 0.0,
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
            data = TwoSampleGenerator.get(scenario, scenario.n_max, offset=i)

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
