"""Two-sample Empirical Bernstein confidence sequences."""

from anytime.spec import ABSpec
from anytime.cs.empirical_bernstein import EmpiricalBernsteinCS
from anytime.twosample.base import TwoSampleCSBase


class TwoSampleEmpiricalBernsteinCS(TwoSampleCSBase):
    """Two-sample Empirical Bernstein confidence sequence.

    Uses a union bound over two one-sample empirical Bernstein sequences.
    """

    def __init__(self, spec: ABSpec):
        if spec.kind not in {"bounded", "bernoulli"}:
            raise ValueError("TwoSampleEmpiricalBernsteinCS requires bounded or bernoulli data")
        super().__init__(spec, EmpiricalBernsteinCS)
