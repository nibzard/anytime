"""Configuration and reproducibility utilities."""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from anytime.spec import StreamSpec, ABSpec
from anytime.errors import ConfigError


def load_yaml_config(path: str) -> dict[str, Any]:
    """Load YAML config file with validation.

    Args:
        path: Path to YAML file

    Returns:
        Parsed config dictionary

    Raises:
        ConfigError: If file is invalid or missing required fields
    """
    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {path}")
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML: {e}")

    if config is None:
        config = {}

    return config


def validate_atlas_config(config: dict[str, Any]) -> None:
    """Validate atlas config structure."""
    if not isinstance(config, dict):
        raise ConfigError("Atlas config must be a dictionary")

    if "one_sample" not in config and "two_sample" not in config:
        raise ConfigError("Atlas config must include at least one of: one_sample, two_sample")

    for section_name in ("one_sample", "two_sample"):
        section = config.get(section_name)
        if section is None:
            continue
        if not isinstance(section, dict):
            raise ConfigError(f"{section_name} must be a dictionary")
        if "spec" not in section or "methods" not in section or "scenarios" not in section:
            raise ConfigError(f"{section_name} must include spec, methods, and scenarios")

        if not isinstance(section["spec"], dict):
            raise ConfigError(f"{section_name}.spec must be a dictionary")
        if not isinstance(section["methods"], list) or not section["methods"]:
            raise ConfigError(f"{section_name}.methods must be a non-empty list")
        if not isinstance(section["scenarios"], list) or not section["scenarios"]:
            raise ConfigError(f"{section_name}.scenarios must be a non-empty list")

        for idx, sc in enumerate(section["scenarios"]):
            if not isinstance(sc, dict):
                raise ConfigError(f"{section_name}.scenarios[{idx}] must be a dictionary")
            if "name" not in sc or "distribution" not in sc or "n_max" not in sc:
                raise ConfigError(
                    f"{section_name}.scenarios[{idx}] must include name, distribution, n_max"
                )
            if section_name == "one_sample" and "true_mean" not in sc:
                raise ConfigError(f"{section_name}.scenarios[{idx}] missing true_mean")
            if section_name == "two_sample" and (
                "true_mean" not in sc or "true_lift" not in sc
            ):
                raise ConfigError(f"{section_name}.scenarios[{idx}] missing true_mean/true_lift")


def create_run_dir(base_dir: str = "runs", name: str = "") -> str:
    """Create a timestamped run directory.

    Args:
        base_dir: Base directory for runs
        name: Optional name suffix for the run

    Returns:
        Path to created run directory
    """
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = name.replace(" ", "_").replace("/", "_") if name else "run"
    run_name = f"{timestamp}_{slug}"

    run_dir = base / run_name
    run_dir.mkdir(exist_ok=True)

    return str(run_dir)


def write_manifest(
    run_dir: str,
    config: dict[str, Any],
    seed: int | None = None,
) -> dict[str, Any]:
    """Write manifest.json with run metadata.

    Args:
        run_dir: Run directory path
        config: Configuration dictionary
        seed: Random seed (optional)

    Returns:
        Manifest dictionary
    """
    manifest = {
        "config": config,
        "seed": seed,
        "timestamp": time.time(),
        "datetime": datetime.now().isoformat(),
        "versions": {
            "python": f"{_get_py_version()}",
        },
    }

    # Try to get git info
    try:
        manifest["git"] = {
            "commit": _get_git_hash(),
            "branch": _get_git_branch(),
        }
    except Exception:
        manifest["git"] = None

    manifest_path = Path(run_dir) / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def _get_py_version() -> str:
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _get_git_hash() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return None


def _get_git_branch() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return None


class JSONLLogger:
    """Logger for metrics and diagnostics in JSONL format."""

    def __init__(self, path: str):
        self.path = path
        self.file = open(path, "w")

    def log(self, data: dict[str, Any]) -> None:
        """Log a data entry."""
        self.file.write(json.dumps(data) + "\n")
        self.file.flush()

    def close(self) -> None:
        """Close the log file."""
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
