"""Tests for e-value implementations."""

import math

from anytime.spec import StreamSpec, ABSpec
from anytime.evalues.bernoulli import BernoulliMixtureE
from anytime.evalues.twosample import TwoSampleMeanMixtureE


def test_bernoulli_evalue_basic():
    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli", two_sided=True)
    eproc = BernoulliMixtureE(spec, p0=0.5, side="ge")

    ev = eproc.evalue()
    assert ev.t == 0
    assert ev.e == 1.0
    assert not ev.decision

    for _ in range(10):
        eproc.update(1.0)

    ev = eproc.evalue()
    assert ev.t == 10
    assert ev.e > 0.0
    assert math.isfinite(ev.e)


def test_twosample_evalue_pairing():
    spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
    eproc = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")

    # Unbalanced updates should not form pairs yet.
    eproc.update(("A", 0.0))
    ev = eproc.evalue()
    assert ev.t == 0
    assert ev.e == 1.0

    # Now add matching B observations.
    for _ in range(5):
        eproc.update(("A", 0.0))
        eproc.update(("B", 1.0))

    ev = eproc.evalue()
    assert ev.t == 5
    assert ev.e > 0.0
    assert math.isfinite(ev.e)
