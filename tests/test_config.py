"""Tests for configuration and reproducibility utilities."""

import json
import tempfile
from pathlib import Path

from anytime.config import write_manifest, create_run_dir


def test_create_run_dir():
    """Run directory should be created with timestamp."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = create_run_dir(base_dir=tmpdir, name="test_run")
        assert Path(run_dir).exists()
        assert "test_run" in run_dir
        assert Path(run_dir).is_dir()


def test_write_manifest():
    """Manifest should be written with all required fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {"alpha": 0.05, "n_max": 1000}
        seed = 42

        manifest = write_manifest(tmpdir, config, seed)

        # Check return value
        assert manifest["config"] == config
        assert manifest["seed"] == seed
        assert "timestamp" in manifest
        assert "datetime" in manifest
        assert "versions" in manifest
        assert "python" in manifest["versions"]
        assert "numpy" in manifest["versions"]
        assert "scipy" in manifest["versions"]
        assert "git" in manifest

        # Check file was written
        manifest_path = Path(tmpdir) / "manifest.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            loaded = json.load(f)

        assert loaded["config"] == config
        assert loaded["seed"] == seed
        assert loaded["versions"]["python"] != "unknown"


def test_write_manifest_without_seed():
    """Manifest should handle None seed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {"alpha": 0.05}
        manifest = write_manifest(tmpdir, config)

        assert manifest["seed"] is None

        manifest_path = Path(tmpdir) / "manifest.json"
        with open(manifest_path) as f:
            loaded = json.load(f)

        assert loaded["seed"] is None
