"""Placeholder test suite verifying test runner execution and package metadata."""

import sys
from pathlib import Path

# Ensure src is on sys.path for testing
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import siphon


def test_package_metadata() -> None:
    """Verify core Siphon package identifiers and semantic version."""
    assert siphon.__version__ == "0.1.0"
    assert siphon.__app_name__ == "Siphon"
    assert siphon.__app_id__ == "io.github.BobiButt.siphon"


def test_trivial_passing() -> None:
    """Trivial assertion verifying pytest configuration."""
    assert True
