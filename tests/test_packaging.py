"""Unit tests for desktop packaging, AppImage build scripts, and .desktop metadata."""

import configparser
import os
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_appimage_fails_when_pyinstaller_fails() -> None:
    """Test 1: Verify build_appimage.sh exits with non-zero return code when PyInstaller fails."""
    script_path = REPO_ROOT / "scripts" / "build_appimage.sh"
    assert script_path.is_file(), "build_appimage.sh must exist"

    env = os.environ.copy()
    # Force PyInstaller command to fail immediately
    env["PYINSTALLER_CMD"] = "false"

    proc = subprocess.run(
        ["bash", str(script_path)],
        env=env,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0, "build_appimage.sh must exit with non-zero status on PyInstaller failure"


def test_desktop_entry_fields() -> None:
    """Test 2: Verify .desktop file specifies correct Name, Exec, Icon, and Type fields."""
    desktop_file = REPO_ROOT / "assets" / "io.github.BobiButt.siphon.desktop"
    assert desktop_file.is_file(), f"Desktop file missing at {desktop_file}"

    config = configparser.ConfigParser(interpolation=None)
    config.read_string(desktop_file.read_text())

    assert "Desktop Entry" in config
    entry = config["Desktop Entry"]

    assert entry.get("Name") == "Siphon"
    assert entry.get("Exec") == "siphon"
    assert entry.get("Icon") == "siphon"
    assert entry.get("Type") == "Application"
    assert "AudioVideo" in entry.get("Categories", "")


def test_pyinstaller_spec_hidden_imports() -> None:
    """Verify Siphon.spec declares all required Uvicorn, FastAPI, and Pydantic hidden imports."""
    spec_path = REPO_ROOT / "Siphon.spec"
    assert spec_path.is_file(), "Siphon.spec must exist"

    content = spec_path.read_text()

    required_hidden_imports = [
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.websockets",
        "uvicorn.lifespan",
        "fastapi",
        "pydantic",
    ]

    for imp in required_hidden_imports:
        assert imp in content, f"Hidden import '{imp}' missing in Siphon.spec"

    # Verify ONEDIR mode (exclude_binaries=True in EXE and COLLECT block present)
    assert "exclude_binaries=True" in content
    assert "COLLECT(" in content
