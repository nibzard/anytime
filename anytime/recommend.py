"""Method recommendation system."""

from dataclasses import dataclass
from anytime.spec import StreamSpec, ABSpec
from anytime.errors import ConfigError
from anytime.cs.hoeffding import HoeffdingCS
from anytime.cs.empirical_bernstein import EmpiricalBernsteinCS
from anytime.cs.bernoulli_exact import BernoulliCS
from anytime.twosample.hoeffding import TwoSampleHoeffdingCS
from anytime.twosample.empirical_bernstein import TwoSampleEmpiricalBernsteinCS


@dataclass
class Recommendation:
    """Recommended method for a spec.

    Attributes:
        method: Method class to use
        reason: Human-readable explanation
    """

    method: type
    reason: str


def recommend_cs(spec: StreamSpec) -> Recommendation:
    """Recommend a confidence sequence method for one-sample inference.

    Args:
        spec: StreamSpec to analyze

    Returns:
        Recommendation with method class and reason
    """
    if spec.kind == "subgaussian":
        raise ConfigError("subgaussian methods are not implemented yet")

    if spec.kind == "bernoulli":
        return Recommendation(
            method=BernoulliCS,
            reason="Bernoulli exact CS for binary data (tightest valid intervals)",
        )

    if spec.kind == "bounded":
        # For bounded data, use Empirical Bernstein by default
        return Recommendation(
            method=EmpiricalBernsteinCS,
            reason="Empirical Bernstein CS: variance-adaptive for bounded data",
        )

    return Recommendation(
        method=HoeffdingCS,
        reason="Hoeffding CS: conservative and anytime-valid for bounded data",
    )


def recommend_ab(spec: ABSpec) -> Recommendation:
    """Recommend a confidence sequence method for A/B testing.

    Args:
        spec: ABSpec to analyze

    Returns:
        Recommendation with method class and reason
    """
    if spec.kind == "subgaussian":
        raise ConfigError("subgaussian methods are not implemented yet")

    if spec.kind == "bernoulli":
        return Recommendation(
            method=TwoSampleEmpiricalBernsteinCS,
            reason="Empirical Bernstein CS: variance-adaptive for binary A/B tests",
        )

    if spec.kind == "bounded":
        return Recommendation(
            method=TwoSampleEmpiricalBernsteinCS,
            reason="Empirical Bernstein CS: variance-adaptive for bounded data",
        )

    return Recommendation(
        method=TwoSampleHoeffdingCS,
        reason="Hoeffding CS: conservative and anytime-valid for bounded data",
    )
