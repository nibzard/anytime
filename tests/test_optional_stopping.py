"""Optional-stopping smoke tests."""

import random

from anytime.spec import StreamSpec
from anytime.cs.bernoulli_exact import BernoulliCS
from anytime.evalues.bernoulli import BernoulliMixtureE


def test_bernoulli_cs_anytime_coverage_smoke():
    """Anytime coverage should be high under the null."""
    alpha = 0.1
    p = 0.5
    n_sim = 60
    n_max = 100
    covered = 0

    spec = StreamSpec(alpha=alpha, support=(0.0, 1.0), kind="bernoulli", two_sided=True)

    for i in range(n_sim):
        rng = random.Random(1000 + i)
        cs = BernoulliCS(spec)
        covered_all = True
        for _ in range(n_max):
            x = 1.0 if rng.random() < p else 0.0
            cs.update(x)
            iv = cs.interval()
            if not (iv.lo <= p <= iv.hi):
                covered_all = False
        if covered_all:
            covered += 1

    rate = covered / n_sim
    assert rate >= 0.75


def test_bernoulli_evalue_optional_stopping_smoke():
    """E-values should not reject too often under the null."""
    alpha = 0.1
    p0 = 0.5
    n_sim = 200
    n_max = 200
    rejects = 0

    spec = StreamSpec(alpha=alpha, support=(0.0, 1.0), kind="bernoulli", two_sided=True)

    for i in range(n_sim):
        rng = random.Random(2000 + i)
        eproc = BernoulliMixtureE(spec, p0=p0, side="ge")
        for _ in range(n_max):
            x = 1.0 if rng.random() < p0 else 0.0
            eproc.update(x)
            if eproc.evalue().decision:
                rejects += 1
                break

    rate = rejects / n_sim
    assert rate <= alpha + 0.1
