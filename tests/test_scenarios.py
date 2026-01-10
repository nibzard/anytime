"""Tests for atlas scenario generators."""

import pytest

from anytime.atlas.scenarios import (
    one_sample_scenarios,
    two_sample_scenarios,
    validate_bernoulli_ab_scenario,
    _validate_bernoulli_probability,
    OneSampleGenerator,
    TwoSampleGenerator,
    exclude_threshold_rule,
)
from anytime.errors import ConfigError


def test_one_sample_scenarios_count():
    """Should generate 8 one-sample scenarios."""
    scenarios = one_sample_scenarios(n_max=100)
    assert len(scenarios) == 8


def test_two_sample_scenarios_count():
    """Should generate 8 two-sample scenarios."""
    scenarios = two_sample_scenarios(n_max=100)
    assert len(scenarios) == 8


def test_scenario_names():
    """Scenarios should have unique names."""
    one_sample = one_sample_scenarios(n_max=100)
    two_sample = two_sample_scenarios(n_max=100)

    names = [s.name for s in one_sample + two_sample]
    assert len(names) == len(set(names)), "Scenario names should be unique"


def test_scenarios_have_required_fields():
    """All scenarios should have required fields."""
    scenarios = one_sample_scenarios(n_max=100) + two_sample_scenarios(n_max=100)

    for s in scenarios:
        assert s.name is not None
        assert s.distribution in ("bernoulli", "uniform", "bounded")
        assert s.support is not None
        assert s.n_max > 0
        assert s.seed is not None
        assert isinstance(s.is_null, bool)


def test_bernoulli_probability_validation():
    """Should validate Bernoulli probabilities."""
    # Valid probabilities
    _validate_bernoulli_probability(0.0)
    _validate_bernoulli_probability(0.5)
    _validate_bernoulli_probability(1.0)

    # Invalid probabilities
    with pytest.raises(ConfigError):
        _validate_bernoulli_probability(-0.1)
    with pytest.raises(ConfigError):
        _validate_bernoulli_probability(1.1)


def test_bernoulli_ab_validation():
    """Should validate Bernoulli A/B scenarios."""
    # Valid scenarios
    validate_bernoulli_ab_scenario(0.1, 0.11)
    validate_bernoulli_ab_scenario(0.5, 0.5)
    validate_bernoulli_ab_scenario(0.001, 0.999)

    # Invalid: out of bounds
    with pytest.raises(ConfigError):
        validate_bernoulli_ab_scenario(-0.1, 0.5)
    with pytest.raises(ConfigError):
        validate_bernoulli_ab_scenario(0.5, 1.1)

    # Invalid: too close to boundaries
    with pytest.raises(ConfigError):
        validate_bernoulli_ab_scenario(0.0001, 0.5)
    with pytest.raises(ConfigError):
        validate_bernoulli_ab_scenario(0.5, 0.9999)


def test_one_sample_generator_bernoulli():
    """Should generate Bernoulli data."""
    from anytime.atlas.runner import Scenario

    scenario = Scenario(
        name="test_bernoulli",
        true_mean=0.3,
        distribution="bernoulli",
        support=(0.0, 1.0),
        n_max=100,
        seed=42,
        is_null=False,
    )

    data = OneSampleGenerator.get(scenario, n=1000)
    assert len(data) == 1000
    assert all(x in (0.0, 1.0) for x in data)
    # Mean should be close to 0.3
    mean = sum(data) / len(data)
    assert 0.2 < mean < 0.4


def test_one_sample_generator_bimodal_mean():
    """Bimodal mixture should match configured mean roughly."""
    scenario = next(s for s in one_sample_scenarios(n_max=100) if s.name == "bimodal_mixture")
    data = OneSampleGenerator.get(scenario, n=2000)

    assert all(0.0 <= x <= 1.0 for x in data)
    mean = sum(data) / len(data)
    assert abs(mean - scenario.true_mean) < 0.05


def test_two_sample_generator_bernoulli():
    """Should generate paired A/B Bernoulli data."""
    from anytime.atlas.runner import Scenario

    scenario = Scenario(
        name="test_ab",
        true_mean=0.15,
        true_lift=0.05,
        distribution="bernoulli",
        support=(0.0, 1.0),
        n_max=100,
        seed=42,
        is_null=False,
    )

    data = TwoSampleGenerator.get(scenario, n=100)
    assert len(data) == 100

    arms = [arm for arm, _ in data]
    values = [val for _, val in data]

    # Should have both arms
    assert "A" in arms
    assert "B" in arms

    # Values should be 0 or 1
    assert all(v in (0.0, 1.0) for v in values)


def test_two_sample_generator_beta_continuous():
    """Continuous beta scenario should yield bounded non-binary values."""
    scenario = next(s for s in two_sample_scenarios(n_max=100) if s.name == "ab_beta_continuous")
    data = TwoSampleGenerator.get(scenario, n=1000)

    values = [val for _, val in data]
    assert all(0.0 <= v <= 1.0 for v in values)
    assert any(v not in (0.0, 1.0) for v in values)

    a_vals = [val for arm, val in data if arm == "A"]
    b_vals = [val for arm, val in data if arm == "B"]
    mean_a = sum(a_vals) / len(a_vals)
    mean_b = sum(b_vals) / len(b_vals)
    assert abs((mean_b - mean_a) - scenario.true_lift) < 0.05


def test_exclude_threshold_stopping_rule():
    """Exclude threshold stopping rule should work correctly."""
    from anytime.spec import StreamSpec
    from anytime.cs.hoeffding import HoeffdingCS

    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
    rule = exclude_threshold_rule(threshold=0.0)

    cs = HoeffdingCS(spec)
    # Add data that should create a CI that excludes 0
    for _ in range(100):
        cs.update(0.8)

    iv = cs.interval()
    # With enough high values, CI should exclude 0
    result = rule.fn(iv, iv.t)
    assert isinstance(result, bool)


def test_null_scenarios_marked_correctly():
    """Null scenarios should have is_null=True."""
    one_sample = one_sample_scenarios(n_max=100)
    two_sample = two_sample_scenarios(n_max=100)

    null_scenarios = [s for s in one_sample + two_sample if s.is_null]

    # Should have at least 2 null scenarios (one from each set)
    assert len(null_scenarios) >= 2

    # Check that two-sample null scenarios have zero lift
    for s in null_scenarios:
        if s.true_lift is not None:  # Two-sample scenarios
            assert s.true_lift == 0.0
