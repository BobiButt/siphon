"""Unit tests validating the GitHub Actions CI/CD workflow definitions (M6)."""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def _load(name: str) -> dict:
    path = WORKFLOWS_DIR / name
    assert path.is_file(), f"Workflow missing at {path}"
    with path.open() as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict), f"{name} must parse to a mapping"
    return data


def test_all_workflows_exist_and_parse() -> None:
    """Every expected workflow file exists and parses to a valid YAML mapping with a 'jobs' key."""
    for name in ("test.yml", "build.yml", "release.yml"):
        data = _load(name)
        assert "jobs" in data and data["jobs"], f"{name} must define at least one job"


def test_test_workflow_matrix_python_versions() -> None:
    """test.yml runs a single 'test' job across a Python 3.11 and 3.12 matrix and invokes pytest."""
    data = _load("test.yml")
    job = data["jobs"]["test"]
    matrix = job["strategy"]["matrix"]["python-version"]
    assert matrix == ["3.11", "3.12"], f"Expected Python 3.11/3.12 matrix, got {matrix}"

    steps = job["steps"]
    run_steps = "\n".join(step.get("run", "") for step in steps)
    assert "pytest" in run_steps, "test.yml must run pytest"
    assert "pip install -e ." in run_steps, "test.yml must install the siphon package (editable)"


def test_build_workflow_containerized_build_and_artifact() -> None:
    """build.yml executes the containerized build script, smoke-tests, and uploads the AppImage artifact."""
    data = _load("build.yml")
    job = data["jobs"]["build"]
    steps = job["steps"]

    run_steps = "\n".join(step.get("run", "") for step in steps)
    assert "./scripts/build_in_docker.sh" in run_steps, "build.yml must run build_in_docker.sh"
    assert "--version" in run_steps, "build.yml must smoke-test the AppImage via --version"

    uses_steps = [step.get("uses", "") for step in steps]
    assert any(u.startswith("actions/upload-artifact") for u in uses_steps), (
        "build.yml must upload the built AppImage as a workflow artifact"
    )


def test_release_workflow_tag_trigger_and_assets() -> None:
    """release.yml triggers on v* tags, has contents:write, and uploads the AppImage plus SHA-256 checksums."""
    data = _load("release.yml")

    # Trigger on v* tag push
    push_tags = data[True]["push"]["tags"] if True in data else data["on"]["push"]["tags"]
    assert push_tags == ["v*"], f"release.yml must trigger on v* tags, got {push_tags}"

    # Permission to create releases
    assert data.get("permissions", {}).get("contents") == "write", (
        "release.yml must grant contents:write to publish the GitHub Release"
    )

    job = data["jobs"]["release"]
    run_steps = "\n".join(step.get("run", "") for step in job["steps"])
    assert "./scripts/build_in_docker.sh" in run_steps, "release.yml must build inside the container"
    assert "sha256sum" in run_steps, "release.yml must generate SHA-256 checksums"

    uses_steps = [step.get("uses", "") for step in job["steps"]]
    assert any(u.startswith("softprops/action-gh-release") for u in uses_steps), (
        "release.yml must publish via a GitHub Release action"
    )

    # The uploaded assets are declared in the release action's `with.files` input.
    release_step = next(s for s in job["steps"] if s.get("uses", "").startswith("softprops/action-gh-release"))
    files = release_step.get("with", {}).get("files", "")
    assert "SHA256SUMS.txt" in files, "release.yml must upload the checksum file"
    assert "*.AppImage" in files, "release.yml must upload the AppImage asset"
