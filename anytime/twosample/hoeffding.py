"""Two-sample Hoeffding-style confidence sequences."""

from anytime.spec import ABSpec
from anytime.cs.hoeffding import HoeffdingCS
from anytime.twosample.base import TwoSampleCSBase


class TwoSampleHoeffdingCS(TwoSampleCSBase):
    """Two-sample Hoeffding confidence sequence for mean difference.

    Uses a union bound over two one-sample Hoeffding confidence sequences.
    """

    def __init__(self, spec: ABSpec):
        if spec.kind not in {"bounded", "bernoulli"}:
            raise ValueError("TwoSampleHoeffdingCS requires bounded or bernoulli data")
        super().__init__(spec, HoeffdingCS)
