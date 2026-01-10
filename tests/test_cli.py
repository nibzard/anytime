"""CLI smoke tests."""

from click.testing import CliRunner

from anytime.cli.main import cli


def test_cli_mean_smoke():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "mean",
            "--config",
            "tests/fixtures/mean_config.yaml",
        ],
    )
    assert result.exit_code == 0
    assert "Final result" in result.output


def test_cli_abtest_smoke():
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "abtest",
            "--config",
            "tests/fixtures/ab_config.yaml",
        ],
    )
    assert result.exit_code == 0
    assert "Final result" in result.output


def test_cli_atlas_smoke(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "atlas",
            "--config",
            "configs/atlas_smoke.yaml",
            "--output",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    reports = list(tmp_path.rglob("report_one_sample.md"))
    assert reports, "missing report_one_sample.md"
    reports = list(tmp_path.rglob("report_two_sample.md"))
    assert reports, "missing report_two_sample.md"
