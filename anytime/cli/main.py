"""Command-line interface for anytime inference."""

import sys
from pathlib import Path

import click

from anytime.spec import StreamSpec, ABSpec
from anytime.cs.hoeffding import HoeffdingCS
from anytime.cs.empirical_bernstein import EmpiricalBernsteinCS
from anytime.cs.bernoulli_exact import BernoulliCS
from anytime.twosample.hoeffding import TwoSampleHoeffdingCS
from anytime.twosample.empirical_bernstein import TwoSampleEmpiricalBernsteinCS
from anytime.recommend import recommend_cs, recommend_ab
from anytime.config import (
    load_yaml_config,
    create_run_dir,
    write_manifest,
    JSONLLogger,
    validate_atlas_config,
)
from anytime.io import read_one_sample_csv, read_ab_test_csv
from anytime.atlas.runner import AtlasRunner, Scenario, StoppingRule
from anytime.atlas.report import generate_comparison_report


def _diagnostics_summary(iv) -> str:
    diag = getattr(iv, "diagnostics", None)
    if not diag:
        return ""
    return (
        f"tier={iv.tier.value}, "
        f"missing={diag.missing_count}, "
        f"out_of_range={diag.out_of_range_count}, "
        f"clipped={diag.clipped_count}, "
        f"drift={diag.drift_detected}"
    )


def _diagnostics_payload(iv) -> dict[str, object] | None:
    diag = getattr(iv, "diagnostics", None)
    if not diag:
        return None
    return diag.to_dict()


@click.group()
def cli():
    """Anytime: Peeking-safe streaming inference for A/B tests and online metrics."""
    pass


@cli.command()
@click.option("--config", "-c", required=True, help="Path to YAML config file")
@click.option("--output", "-o", help="Output directory for results")
def mean(config: str, output: str | None):
    """Run one-sample confidence sequence on CSV data."""
    cfg = load_yaml_config(config)

    # Parse spec
    spec = StreamSpec(
        alpha=cfg.get("alpha", 0.05),
        support=tuple(cfg.get("support", [0.0, 1.0])),
        kind=cfg.get("kind", "bounded"),
        two_sided=cfg.get("two_sided", True),
        name=cfg.get("name", ""),
    )

    # Get method
    method_name = cfg.get("method", "auto")
    if method_name == "auto":
        rec = recommend_cs(spec)
        cs_cls = rec.method
        click.echo(f"Using recommended method: {rec.reason}")
    elif method_name == "hoeffding":
        cs_cls = HoeffdingCS
    elif method_name == "empirical_bernstein":
        cs_cls = EmpiricalBernsteinCS
    elif method_name == "bernoulli":
        cs_cls = BernoulliCS
    else:
        click.echo(f"Unknown method: {method_name}", err=True)
        sys.exit(1)

    # Setup output
    if output:
        run_dir = create_run_dir(output, spec.name or "mean")
        logger = JSONLLogger(Path(run_dir) / "results.jsonl")
    else:
        run_dir = None
        logger = None

    # Read and process CSV
    input_file = cfg.get("input")
    column = cfg.get("column", "value")

    cs = cs_cls(spec)

    try:
        reader = read_one_sample_csv(input_file, value_column=column)

        for row, row_num in reader.rows():
            x = reader.read_numeric(row, column)
            if x is not None:
                cs.update(x)
                iv = cs.interval()

                if logger:
                    logger.log({
                        "t": iv.t,
                        "estimate": iv.estimate,
                        "lo": iv.lo,
                        "hi": iv.hi,
                        "width": iv.width,
                        "tier": iv.tier.value,
                        "diagnostics": _diagnostics_payload(iv),
                    })

                # Print progress
                if iv.t % 100 == 0:
                    summary = _diagnostics_summary(iv)
                    suffix = f" ({summary})" if summary else ""
                    click.echo(
                        f"t={iv.t}: estimate={iv.estimate:.4f}, [{iv.lo:.4f}, {iv.hi:.4f}]{suffix}"
                    )

        # Final result
        iv = cs.interval()
        click.echo(f"\nFinal result at t={iv.t}:")
        click.echo(f"  Estimate: {iv.estimate:.4f}")
        click.echo(f"  {1-spec.alpha:.0%} CI: [{iv.lo:.4f}, {iv.hi:.4f}]")
        click.echo(f"  Width: {iv.width:.4f}")
        click.echo(f"  Tier: {iv.tier.value}")
        summary = _diagnostics_summary(iv)
        if summary:
            click.echo(f"  Diagnostics: {summary}")

        # Print CSV read summary
        csv_summary = reader.get_summary()
        if csv_summary["missing_values"] > 0 or csv_summary["invalid_values"] > 0:
            click.echo(f"\nCSV reading summary:")
            click.echo(f"  Rows processed: {csv_summary['row_count']}")
            click.echo(f"  Missing values: {csv_summary['missing_values']}")
            click.echo(f"  Invalid values: {csv_summary['invalid_values']}")

        if run_dir:
            write_manifest(run_dir, cfg)
            click.echo(f"\nResults written to {run_dir}")

    except FileNotFoundError:
        click.echo(f"Input file not found: {input_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        if logger:
            logger.close()


@cli.command()
@click.option("--config", "-c", required=True, help="Path to YAML config file")
@click.option("--output", "-o", help="Output directory for results")
def abtest(config: str, output: str | None):
    """Run two-sample A/B test on CSV data."""
    cfg = load_yaml_config(config)

    # Parse spec
    spec = ABSpec(
        alpha=cfg.get("alpha", 0.05),
        support=tuple(cfg.get("support", [0.0, 1.0])),
        kind=cfg.get("kind", "bounded"),
        two_sided=cfg.get("two_sided", True),
        name=cfg.get("name", ""),
    )

    # Get method
    method_name = cfg.get("method", "auto")
    if method_name == "auto":
        rec = recommend_ab(spec)
        cs_cls = rec.method
        click.echo(f"Using recommended method: {rec.reason}")
    elif method_name == "hoeffding":
        cs_cls = TwoSampleHoeffdingCS
    elif method_name == "empirical_bernstein":
        cs_cls = TwoSampleEmpiricalBernsteinCS
    else:
        click.echo(f"Unknown method: {method_name}", err=True)
        sys.exit(1)

    # Setup output
    if output:
        run_dir = create_run_dir(output, spec.name or "abtest")
        logger = JSONLLogger(Path(run_dir) / "results.jsonl")
    else:
        run_dir = None
        logger = None

    # Read and process CSV
    input_file = cfg.get("input")
    arm_col = cfg.get("arm_column", "arm")
    val_col = cfg.get("value_column", "value")

    cs = cs_cls(spec)

    try:
        reader = read_ab_test_csv(input_file, arm_column=arm_col, value_column=val_col)

        for row, row_num in reader.rows():
            arm = row[arm_col]
            x = reader.read_numeric(row, val_col)
            if x is not None:
                cs.update((arm, x))
                iv = cs.interval()

                if logger:
                    logger.log({
                        "t": iv.t,
                        "estimate": iv.estimate,
                        "lo": iv.lo,
                        "hi": iv.hi,
                        "width": iv.width,
                        "tier": iv.tier.value,
                        "diagnostics": _diagnostics_payload(iv),
                    })

                # Print progress
                if iv.t % 100 == 0:
                    summary = _diagnostics_summary(iv)
                    suffix = f" ({summary})" if summary else ""
                    click.echo(
                        f"t={iv.t}: lift={iv.estimate:.4f}, [{iv.lo:.4f}, {iv.hi:.4f}]{suffix}"
                    )

        # Final result
        iv = cs.interval()
        click.echo(f"\nFinal result at t={iv.t}:")
        click.echo(f"  Lift: {iv.estimate:.4f}")
        click.echo(f"  {1-spec.alpha:.0%} CI: [{iv.lo:.4f}, {iv.hi:.4f}]")
        click.echo(f"  Width: {iv.width:.4f}")
        click.echo(f"  Tier: {iv.tier.value}")
        summary = _diagnostics_summary(iv)
        if summary:
            click.echo(f"  Diagnostics: {summary}")

        # Print CSV read summary
        csv_summary = reader.get_summary()
        if csv_summary["missing_values"] > 0 or csv_summary["invalid_values"] > 0:
            click.echo(f"\nCSV reading summary:")
            click.echo(f"  Rows processed: {csv_summary['row_count']}")
            click.echo(f"  Missing values: {csv_summary['missing_values']}")
            click.echo(f"  Invalid values: {csv_summary['invalid_values']}")

        if run_dir:
            write_manifest(run_dir, cfg)
            click.echo(f"\nResults written to {run_dir}")

    except FileNotFoundError:
        click.echo(f"Input file not found: {input_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        if logger:
            logger.close()


def _direction_check_fn(direction: str, threshold: float):
    """Create direction check function for stopping rules."""
    if direction == "ge":
        return lambda iv: iv.lo > threshold
    if direction == "le":
        return lambda iv: iv.hi < threshold
    return lambda iv: iv.lo > threshold or iv.hi < threshold


def _parse_stopping_rule(rule_cfg: dict[str, object] | None) -> StoppingRule | None:
    """Parse stopping rule configuration.

    Returns None for 'fixed' horizon (no early stopping).
    """
    if not rule_cfg:
        return None

    rule_type = rule_cfg.get("type", "fixed")

    if rule_type == "fixed":
        return None

    if rule_type == "exclude_threshold":
        threshold = float(rule_cfg.get("threshold", 0.0))
        direction = rule_cfg.get("direction", "both")
        name = f"exclude_{direction}_{threshold}"
        check_fn = _direction_check_fn(direction, threshold)
        return StoppingRule(name=name, fn=lambda iv, _t: check_fn(iv))

    if rule_type == "periodic":
        every = int(rule_cfg.get("every", 50))
        inner_cfg = rule_cfg.get("rule", {"type": "exclude_threshold"})
        inner = _parse_stopping_rule(inner_cfg)
        if inner is None:
            return None
        name = f"periodic_{every}_{inner.name}"
        return StoppingRule(
            name=name,
            fn=lambda iv, t: t % every == 0 and inner.fn(iv, t),
        )

    raise click.ClickException(f"Unknown stopping rule type: {rule_type}")


@cli.command()
@click.option("--config", "-c", help="Path to YAML config file")
@click.option("--output", "-o", help="Output directory for results")
def atlas(config: str | None, output: str | None):
    """Run atlas benchmarks and generate reports."""
    cfg = load_yaml_config(config) if config else {}
    if config:
        validate_atlas_config(cfg)
    n_sim = int(cfg.get("n_sim", 200))

    run_dir = create_run_dir(output, "atlas") if output else None

    # Default tiny benchmark if no config is provided.
    use_defaults = config is None
    if use_defaults:
        one_sample_cfg = {
            "spec": {"alpha": 0.05, "support": [0.0, 1.0], "kind": "bernoulli", "two_sided": True},
            "methods": ["hoeffding", "empirical_bernstein", "bernoulli"],
            "scenarios": [
                {"name": "bernoulli_null", "distribution": "bernoulli", "true_mean": 0.5, "n_max": 200, "is_null": True},
                {"name": "bernoulli_alt", "distribution": "bernoulli", "true_mean": 0.55, "n_max": 200, "is_null": False},
            ],
        }
        two_sample_cfg = {
            "spec": {"alpha": 0.05, "support": [0.0, 1.0], "kind": "bernoulli", "two_sided": True},
            "methods": ["hoeffding", "empirical_bernstein"],
            "scenarios": [
                {
                    "name": "ab_null",
                    "distribution": "bernoulli",
                    "true_mean": 0.1,
                    "true_lift": 0.0,
                    "n_max": 200,
                    "is_null": True,
                },
                {
                    "name": "ab_alt",
                    "distribution": "bernoulli",
                    "true_mean": 0.1,
                    "true_lift": 0.02,
                    "n_max": 200,
                    "is_null": False,
                },
            ],
        }
    else:
        one_sample_cfg = cfg.get("one_sample")
        two_sample_cfg = cfg.get("two_sample")

    runner = AtlasRunner(n_sim=n_sim)

    # One-sample benchmarks.
    if one_sample_cfg:
        spec_cfg = one_sample_cfg.get("spec", {})
        spec = StreamSpec(
            alpha=spec_cfg.get("alpha", 0.05),
            support=tuple(spec_cfg.get("support", [0.0, 1.0])),
            kind=spec_cfg.get("kind", "bounded"),
            two_sided=spec_cfg.get("two_sided", True),
            name=spec_cfg.get("name", ""),
        )
        method_map = {
            "hoeffding": HoeffdingCS,
            "empirical_bernstein": EmpiricalBernsteinCS,
            "bernoulli": BernoulliCS,
        }
        results: dict[str, dict[str, object]] = {}
        stop_rule = _parse_stopping_rule(one_sample_cfg.get("stopping_rule"))
        for method_name in one_sample_cfg.get("methods", []):
            cs_cls = method_map.get(method_name)
            if cs_cls is None:
                raise click.ClickException(f"Unknown one-sample method: {method_name}")
            results[method_name] = {}
            for sc in one_sample_cfg.get("scenarios", []):
                scenario = Scenario(
                    name=sc["name"],
                    true_mean=float(sc["true_mean"]),
                    distribution=sc.get("distribution", "bernoulli"),
                    support=tuple(sc.get("support", spec.support)),
                    n_max=int(sc.get("n_max", 200)),
                    seed=int(sc.get("seed", 42)),
                    is_null=bool(sc.get("is_null", False)),
                )
                sc_rule = _parse_stopping_rule(sc.get("stopping_rule")) or stop_rule
                metrics = runner.run_one_sample(scenario, spec, cs_cls, sc_rule)
                results[method_name][scenario.name] = metrics

        if results:
            report_path = Path(run_dir or ".") / "report_one_sample.md"
            generate_comparison_report(results, str(report_path))
            click.echo(f"One-sample report written to {report_path}")

    # Two-sample benchmarks.
    if two_sample_cfg:
        spec_cfg = two_sample_cfg.get("spec", {})
        spec = ABSpec(
            alpha=spec_cfg.get("alpha", 0.05),
            support=tuple(spec_cfg.get("support", [0.0, 1.0])),
            kind=spec_cfg.get("kind", "bounded"),
            two_sided=spec_cfg.get("two_sided", True),
            name=spec_cfg.get("name", ""),
        )
        method_map = {
            "hoeffding": TwoSampleHoeffdingCS,
            "empirical_bernstein": TwoSampleEmpiricalBernsteinCS,
        }
        results = {}
        stop_rule = _parse_stopping_rule(two_sample_cfg.get("stopping_rule"))
        for method_name in two_sample_cfg.get("methods", []):
            cs_cls = method_map.get(method_name)
            if cs_cls is None:
                raise click.ClickException(f"Unknown two-sample method: {method_name}")
            results[method_name] = {}
            for sc in two_sample_cfg.get("scenarios", []):
                true_lift = float(sc["true_lift"])
                is_null = sc.get("is_null")
                if is_null is None:
                    is_null = true_lift == 0.0
                scenario = Scenario(
                    name=sc["name"],
                    true_mean=float(sc["true_mean"]),
                    true_lift=true_lift,
                    distribution=sc.get("distribution", "bernoulli"),
                    support=tuple(sc.get("support", spec.support)),
                    n_max=int(sc.get("n_max", 200)),
                    seed=int(sc.get("seed", 42)),
                    is_null=bool(is_null),
                )
                sc_rule = _parse_stopping_rule(sc.get("stopping_rule")) or stop_rule
                metrics = runner.run_two_sample(scenario, spec, cs_cls, sc_rule)
                results[method_name][scenario.name] = metrics

        if results:
            report_path = Path(run_dir or ".") / "report_two_sample.md"
            generate_comparison_report(results, str(report_path))
            click.echo(f"Two-sample report written to {report_path}")

    if run_dir:
        write_manifest(run_dir, cfg)


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
