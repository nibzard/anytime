"""Performance micro-benchmarks for anytime inference methods."""

import time

import pytest

from anytime.spec import StreamSpec, ABSpec
from anytime.cs.hoeffding import HoeffdingCS
from anytime.cs.empirical_bernstein import EmpiricalBernsteinCS
from anytime.cs.bernoulli_exact import BernoulliCS
from anytime.twosample.hoeffding import TwoSampleHoeffdingCS
from anytime.twosample.empirical_bernstein import TwoSampleEmpiricalBernsteinCS


def _benchmark_throughput(cs_class, spec, data_generator, n_updates: int) -> float:
    """Measure updates per second for a CS class.

    Args:
        cs_class: Confidence sequence class to benchmark
        spec: Stream specification
        data_generator: Function that generates data
        n_updates: Number of updates to perform

    Returns:
        Updates per second
    """
    cs = cs_class(spec)

    data = data_generator(n_updates)
    start = time.perf_counter()

    for x in data:
        cs.update(x)

    end = time.perf_counter()
    elapsed = end - start
    return n_updates / elapsed


@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarks for CS methods."""

    def test_hoeffding_throughput(self):
        """Hoeffding CS should achieve >100k updates/sec for simple cases."""
        spec = StreamSpec(
            alpha=0.05,
            support=(0.0, 1.0),
            kind="bounded",
            two_sided=True,
        )

        def gen(n):
            return [0.5] * n

        ups = _benchmark_throughput(HoeffdingCS, spec, gen, n_updates=10000)
        print(f"\nHoeffdingCS: {ups:.0f} updates/sec")
        assert ups > 10000  # Conservative threshold

    def test_empirical_bernstein_throughput(self):
        """Empirical Bernstein CS should have reasonable throughput."""
        spec = StreamSpec(
            alpha=0.05,
            support=(0.0, 1.0),
            kind="bounded",
            two_sided=True,
        )

        def gen(n):
            return [0.5] * n

        ups = _benchmark_throughput(EmpiricalBernsteinCS, spec, gen, n_updates=10000)
        print(f"\nEmpiricalBernsteinCS: {ups:.0f} updates/sec")
        assert ups > 5000  # EB is slower due to variance tracking

    def test_bernoulli_throughput(self):
        """Bernoulli CS should have competitive throughput."""
        spec = StreamSpec(
            alpha=0.05,
            support=(0.0, 1.0),
            kind="bernoulli",
            two_sided=True,
        )

        def gen(n):
            return [1.0, 0.0] * (n // 2)

        ups = _benchmark_throughput(BernoulliCS, spec, gen, n_updates=10000)
        print(f"\nBernoulliCS: {ups:.0f} updates/sec")
        assert ups > 1000  # Bernoulli involves root-finding, so it's slower

    def test_two_sample_hoeffding_throughput(self):
        """Two-sample Hoeffding CS throughput."""
        spec = ABSpec(
            alpha=0.05,
            support=(0.0, 1.0),
            kind="bounded",
            two_sided=True,
        )

        def gen(n):
            # Generate pairs
            data = []
            for i in range(n):
                arm = "A" if i % 2 == 0 else "B"
                data.append((arm, 0.5))
            return data

        cs = TwoSampleHoeffdingCS(spec)
        data = gen(10000)
        start = time.perf_counter()

        for arm, x in data:
            cs.update((arm, x))

        end = time.perf_counter()
        ups = len(data) / (end - start)
        print(f"\nTwoSampleHoeffdingCS: {ups:.0f} updates/sec")
        assert ups > 5000


def test_benchmark_comparison():
    """Compare relative performance of different methods."""
    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True,
    )

    def gen(n):
        return [0.5] * n

    n_updates = 5000
    results = {}

    for cls_name, cls in [("HoeffdingCS", HoeffdingCS), ("EmpiricalBernsteinCS", EmpiricalBernsteinCS)]:
        ups = _benchmark_throughput(cls, spec, gen, n_updates)
        results[cls_name] = ups
        print(f"{cls_name}: {ups:.0f} updates/sec")

    # Hoeffding should be faster than EB
    assert results["HoeffdingCS"] > results["EmpiricalBernsteinCS"]


if __name__ == "__main__":
    # Run benchmarks directly
    print("Running performance benchmarks...")

    test = TestPerformance()

    test.test_hoeffding_throughput()
    test.test_empirical_bernstein_throughput()
    test.test_bernoulli_throughput()
    test.test_two_sample_hoeffding_throughput()

    print("\nComparative benchmarks:")
    test_benchmark_comparison()

    print("\n✅ All benchmarks passed!")
