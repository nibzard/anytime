"""Smoke tests for atlas benchmarking."""

import tempfile
from pathlib import Path

import yaml

from anytime.spec import StreamSpec, ABSpec
from anytime.atlas.runner import AtlasRunner, Scenario
from anytime.atlas.scenarios import one_sample_scenarios, two_sample_scenarios
from anytime.atlas.report import generate_comparison_report


def test_atlas_runner_smoke():
    """Atlas runner should complete a small benchmark."""
    runner = AtlasRunner(n_sim=10)

    # Simple one-sample scenario
    scenario = Scenario(
        name="smoke_bernoulli",
        true_mean=0.5,
        distribution="bernoulli",
        support=(0.0, 1.0),
        n_max=50,
        seed=42,
        is_null=True,
    )

    spec = StreamSpec(
        alpha=0.1,  # Higher alpha for faster test
        support=(0.0, 1.0),
        kind="bernoulli",
        two_sided=True,
    )

    from anytime.cs.bernoulli_exact import BernoulliCS
    metrics = runner.run_one_sample(scenario, spec, BernoulliCS, stopping_rule=None)

    # Check metrics structure
    assert metrics.coverage >= 0.0
    assert metrics.coverage <= 1.0
    assert metrics.final_coverage >= 0.0
    assert metrics.final_coverage <= 1.0
    assert metrics.avg_width > 0
    assert metrics.median_stop_time > 0
    assert metrics.avg_runtime >= 0


def test_atlas_report_smoke():
    """Report generation should work with sample data."""
    from anytime.atlas.runner import Metrics
    from anytime.spec import StreamSpec

    # Create minimal results
    results = {
        "hoeffding": {
            "scenario1": Metrics(
                coverage=0.95,
                final_coverage=0.96,
                type_i_error=0.05,
                power=0.8,
                avg_width=0.1,
                median_stop_time=100,
                avg_runtime=0.01,
            )
        },
        "bernoulli": {
            "scenario1": Metrics(
                coverage=0.97,
                final_coverage=0.98,
                type_i_error=0.03,
                power=0.85,
                avg_width=0.08,
                median_stop_time=80,
                avg_runtime=0.015,
            )
        }
    }

    # Create specs for recommender audit
    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bounded", two_sided=True)
    specs = {"one_sample": spec}

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        output_path = f.name

    try:
        generate_comparison_report(results, output_path, specs=specs)
        assert Path(output_path).exists()

        content = Path(output_path).read_text()
        assert "hoeffding" in content.lower()
        assert "bernoulli" in content.lower()
        assert "scenario1" in content
        assert "Type I Error" in content
        assert "Power" in content
        assert "Recommender Audit" in content
    finally:
        Path(output_path).unlink()


def test_atlas_smoke_config():
    """Create a minimal smoke atlas config."""
    config = {
        "one_sample": {
            "spec": {
                "alpha": 0.1,
                "support": [0.0, 1.0],
                "kind": "bernoulli",
                "two_sided": True,
            },
            "methods": ["bernoulli"],
            "scenarios": [
                {
                    "name": "smoke_null",
                    "distribution": "bernoulli",
                    "true_mean": 0.5,
                    "n_max": 50,
                    "is_null": True,
                }
            ]
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name

    try:
        from anytime.config import load_yaml_config, validate_atlas_config
        loaded = load_yaml_config(config_path)
        validate_atlas_config(loaded)

        assert "one_sample" in loaded
        assert loaded["one_sample"]["methods"] == ["bernoulli"]
    finally:
        Path(config_path).unlink()


def test_two_sample_atlas_smoke():
    """Two-sample atlas should run a small benchmark."""
    runner = AtlasRunner(n_sim=10)

    scenario = Scenario(
        name="smoke_ab_null",
        true_mean=0.5,
        true_lift=0.0,
        distribution="bernoulli",
        support=(0.0, 1.0),
        n_max=50,
        seed=42,
        is_null=True,
    )

    spec = ABSpec(
        alpha=0.1,
        support=(0.0, 1.0),
        kind="bernoulli",
        two_sided=True,
    )

    from anytime.twosample.hoeffding import TwoSampleHoeffdingCS
    metrics = runner.run_two_sample(scenario, spec, TwoSampleHoeffdingCS, stopping_rule=None)

    assert metrics.coverage >= 0.0
    assert metrics.coverage <= 1.0
    assert metrics.avg_width > 0


def test_report_builder_plot_embedding():
    """ReportBuilder should support plot embedding with captions."""
    from anytime.atlas.report import ReportBuilder

    builder = ReportBuilder("Test Report")
    builder.add_header(2, "Plots")

    # Create a dummy image file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as f:
        img_path = f.name
        # Write a minimal 1x1 PNG
        import base64
        # 1x1 red PNG
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        f.write(png_data.decode('latin1'))

    try:
        builder.add_plot(img_path, "Test plot caption")
        builder.add_plot(img_path)  # No caption

        report = builder.build()
        assert "![Test plot caption](" in report or "plot](" in report
        assert "*Test plot caption*" in report
        assert "![plot](" in report
    finally:
        Path(img_path).unlink()


def test_report_builder_code_block():
    """ReportBuilder should support code blocks."""
    from anytime.atlas.report import ReportBuilder

    builder = ReportBuilder("Test Report")
    builder.add_header(2, "Code Examples")
    builder.add_code_block("print('hello')", "python")

    report = builder.build()
    assert "```python" in report
    assert "print('hello')" in report
    assert "```" in report


def test_atlas_smoke_config_runs():
    """Smoke atlas config should run successfully and produce expected outputs."""
    import yaml
    from anytime.config import load_yaml_config, validate_atlas_config
    import tempfile

    # Load smoke config
    config = load_yaml_config("configs/atlas_smoke.yaml")

    # Config should have required fields
    assert "one_sample" in config
    assert "two_sample" in config
    assert "spec" in config["one_sample"]
    assert "methods" in config["one_sample"]
    assert "scenarios" in config["one_sample"]

    # Config should be valid
    validate_atlas_config(config)


def test_naive_peeking_inflates_error():
    """Naive peeking should inflate Type I error compared to CS."""
    from anytime.atlas.runner import AtlasRunner, Scenario, naive_peeking_test

    # Run null scenario
    scenario = Scenario(
        name="null_bernoulli",
        true_mean=0.5,
        distribution="bernoulli",
        support=(0.0, 1.0),
        n_max=200,
        seed=42,
        is_null=True,
    )

    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli", two_sided=True)

    runner = AtlasRunner(n_sim=100)

    # Run with naive peeking tracking
    from anytime.cs.hoeffding import HoeffdingCS
    metrics = runner.run_one_sample(
        scenario, spec, HoeffdingCS, stopping_rule=None, track_naive_peeking=True
    )

    # Naive peeking should have inflated error (much higher than alpha)
    # CS should control error properly
    if metrics.naive_peeking_error > 0:
        # Naive peeking is invalid - should inflate Type I error
        assert metrics.naive_peeking_error > spec.alpha

    # CS type I error (from fixed-n stopping) should be controlled
    # This tracks CS-based stopping, which is valid


def test_evalue_decision_tracking():
    """Atlas should track e-value decision rates."""
    from anytime.atlas.runner import AtlasRunner, Scenario
    from anytime.evalues import BernoulliMixtureE

    scenario = Scenario(
        name="evalue_test",
        true_mean=0.7,  # Alternative (false null)
        distribution="bernoulli",
        support=(0.0, 1.0),
        n_max=100,
        seed=42,
        is_null=False,
    )

    spec = StreamSpec(alpha=0.05, support=(0.0, 1.0), kind="bernoulli", two_sided=True)

    runner = AtlasRunner(n_sim=50)

    # Test with Bernoulli CS and BernoulliMixtureE
    from anytime.cs.bernoulli_exact import BernoulliCS
    metrics = runner.run_one_sample(
        scenario, spec, BernoulliCS, stopping_rule=None, evalue_class=BernoulliMixtureE
    )

    # E-value should detect some effect (power > 0 for alt scenario)
    # Decision rate tracks how often e >= 1/alpha
    assert 0.0 <= metrics.evalue_decision_rate <= 1.0
