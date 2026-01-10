"""Tests for spec validation."""

import pytest
from anytime.spec import StreamSpec, ABSpec
from anytime.errors import ConfigError


def test_stream_spec_valid():
    """Valid spec should not raise."""
    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True,
    )
    assert spec.alpha == 0.05
    assert spec.support == (0.0, 1.0)
    assert spec.kind == "bounded"


def test_stream_spec_invalid_alpha():
    """Invalid alpha should raise."""
    with pytest.raises(ConfigError):
        StreamSpec(alpha=0.0, support=(0.0, 1.0), kind="bounded", two_sided=True)

    with pytest.raises(ConfigError):
        StreamSpec(alpha=1.0, support=(0.0, 1.0), kind="bounded", two_sided=True)


def test_stream_spec_invalid_support():
    """Invalid support should raise."""
    with pytest.raises(ConfigError):
        StreamSpec(alpha=0.05, support=(1.0, 0.0), kind="bounded", two_sided=True)


def test_stream_spec_bounded_requires_support():
    """Bounded kind requires finite support."""
    with pytest.raises(ConfigError):
        StreamSpec(alpha=0.05, support=(None, None), kind="bounded", two_sided=True)


def test_stream_spec_bernoulli_requires_unit_support():
    """Bernoulli kind requires support=(0.0, 1.0)."""
    with pytest.raises(ConfigError):
        StreamSpec(alpha=0.05, support=(0.0, 2.0), kind="bernoulli", two_sided=True)


def test_ab_spec_valid():
    """Valid ABSpec should not raise."""
    spec = ABSpec(
        alpha=0.05,
        support=(0.0, 1.0),
        kind="bounded",
        two_sided=True,
    )
    assert spec.alpha == 0.05
    assert spec.support == (0.0, 1.0)
    assert spec.kind == "bounded"


def test_ab_spec_invalid_alpha():
    """Invalid alpha should raise."""
    with pytest.raises(ConfigError):
        ABSpec(alpha=-0.01, support=(0.0, 1.0), kind="bounded", two_sided=True)


def test_ab_spec_bernoulli_requires_unit_support():
    """Bernoulli kind requires support=(0.0, 1.0)."""
    with pytest.raises(ConfigError):
        ABSpec(alpha=0.05, support=(0.0, 0.5), kind="bernoulli", two_sided=True)


def test_clip_mode_validation():
    """Invalid clip_mode should raise."""
    with pytest.raises(ConfigError):
        StreamSpec(
            alpha=0.05,
            support=(0.0, 1.0),
            kind="bounded",
            two_sided=True,
            clip_mode="invalid",
        )
