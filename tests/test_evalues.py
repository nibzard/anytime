"""Tests for e-value implementations."""

import math
import random

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


def test_twosample_evalue_null_smoke():
    """Smoke test: e-value under null should rarely exceed threshold."""
    spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
    eproc = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")

    # Under null: both arms have same distribution
    random.seed(42)
    for _ in range(100):
        a = random.random()
        b = random.random()
        eproc.update(("A", a))
        eproc.update(("B", b))

    ev = eproc.evalue()
    # Under null, e-value should usually be small (rarely exceed 1/alpha = 20)
    assert ev.e < 100  # Very loose bound for smoke test
    assert math.isfinite(ev.e)


def test_twosample_evalue_power_smoke():
    """Smoke test: e-value under alternative should tend to grow."""
    spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
    eproc = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")

    # Under alternative: B is consistently higher than A
    random.seed(42)
    for _ in range(100):
        a = 0.3 + random.random() * 0.1  # A ~ Uniform(0.3, 0.4)
        b = 0.6 + random.random() * 0.1  # B ~ Uniform(0.6, 0.7)
        eproc.update(("A", a))
        eproc.update(("B", b))

    ev = eproc.evalue()
    # Under alternative with large effect, e-value should be large
    assert ev.e > 1.0  # Should show evidence against null
    assert math.isfinite(ev.e)


def test_twosample_evalue_no_overflow():
    """E-value should not overflow even with many samples."""
    spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
    eproc = TwoSampleMeanMixtureE(spec, delta0=0.0, side="ge")

    # Extreme alternative: max separation for many samples
    for _ in range(1000):
        eproc.update(("A", 0.0))
        eproc.update(("B", 1.0))

    ev = eproc.evalue()
    # Should be large but finite (not inf or nan)
    assert math.isfinite(ev.e)
    assert ev.e > 0
