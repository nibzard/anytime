"""Tests for method recommender."""

import pytest

from anytime.spec import StreamSpec, ABSpec
from anytime.recommend import recommend_cs, recommend_ab
from anytime.cs.bernoulli_exact import BernoulliCS
from anytime.cs.empirical_bernstein import EmpiricalBernsteinCS
from anytime.errors import ConfigError


def test_recommend_bernoulli():
    """Bernoulli kind should recommend BernoulliCS."""
    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli", two_sided=True)
    rec = recommend_cs(spec)
    assert rec.method == BernoulliCS
    assert "Bernoulli" in rec.reason


def test_recommend_bounded():
    """Bounded kind should recommend EmpiricalBernsteinCS."""
    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
    rec = recommend_cs(spec)
    assert rec.method == EmpiricalBernsteinCS
    assert "Empirical Bernstein" in rec.reason


def test_recommend_subgaussian():
    """Subgaussian kind should raise until methods exist."""
    spec = StreamSpec(
        alpha=0.05,
        support=(float("-inf"), float("inf")),
        kind="subgaussian",
        two_sided=True,
    )
    with pytest.raises(ConfigError):
        recommend_cs(spec)


def test_recommend_ab_bernoulli():
    """AB Bernoulli should recommend two-sample EB."""
    spec = ABSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli", two_sided=True)
    rec = recommend_ab(spec)
    assert "TwoSample" in rec.method.__name__
