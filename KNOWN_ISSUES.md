# Known Issues & Bug Register — Siphon

This document tracks known bugs, environmental quirks, edge cases, and unresolved blockers. When a bug or unexpected behavior is discovered during development, document it immediately using the standardized issue template below.

---

## Standard Issue Template

When filing a new issue in this register, use the following structure:

```markdown
### ISSUE-XXX: [Short Descriptive Title]
- **Date Discovered:** YYYY-MM-DD
- **Affected Milestone / Component:** [e.g., M4 / pywebview or M5 / packaging]
- **Symptom:** Clear explanation of observed failure, unexpected behavior, or error traceback.
- **Repro:** Minimal step-by-step instructions to reproduce the failure.
- **Investigation So Far:** Details on root cause analysis, logs examined, socket states, or stack traces.
- **Attempted Fixes:** Chronological list of workarounds or fixes attempted and their outcomes.
- **Next Step:** Concrete proposed next action or fix to be executed.
```

---

## Active Issues Register

### ISSUE-001: GUI launcher crashed with `TypeError` on `webview.create_window()`
- **Date Discovered:** 2026-10-18
- **Affected Milestone / Component:** M4 / pywebview shell
- **Symptom:** Launching GUI mode (`python -m siphon`) raised `TypeError: create_window() got an unexpected keyword argument 'icon'` when constructing the desktop window.
- **Repro:** Run `python -m siphon` (GUI mode) with the pre-fix `src/siphon/launcher.py`.
- **Investigation So Far:** `pywebview`'s `create_window()` API does not accept an `icon` argument. The prior session passed `icon=icon_arg` in error.
- **Attempted Fixes:** Removed the `icon=icon_arg` argument entirely, along with the dead `icon_path` parameter, its default-resolution block, and the now-unused `os`/`Path`/`Optional` imports. Committed as `b426d19`. Verified all 24 tests pass.
- **Next Step:** Resolved. Window/desktop icon integration is handled by the AppImage and XDG `.desktop` entry (M5/M6); no further launcher-level action needed.

### No Other Active Issues
- **Status:** All other systems operational. The handoff documentation system and architectural foundations were established without further issues.

### ISSUE-002: Containerized build uses Python 3.10 but project requires Python 3.11+
- **Date Discovered:** 2026-10-18
- **Affected Milestone / Component:** M5 / packaging (`scripts/build_in_docker.sh`) and M6 / CI (`build.yml`, `release.yml`)
- **Symptom:** The reference build runs inside an `ubuntu:22.04` container, whose system `python3` is **3.10**. However, `pyproject.toml` declares `requires-python = ">=3.11"` and the architecture baseline mandates Python 3.11+. The containerized AppImage would bundle a 3.10 interpreter, contradicting the stated requirement.
- **Repro:** Inspect `scripts/build_in_docker.sh` (installs `python3` from the Ubuntu 22.04 apt repo → Python 3.10) versus `pyproject.toml` (`requires-python = ">=3.11"`).
- **Investigation So Far:** The host build used Python 3.14 (works). The container path installs only distro `python3`, which on 22.04 is 3.10. `pip install -r requirements.txt` does not enforce `requires-python`, so the build currently succeeds despite the mismatch.
- **Attempted Fixes:** None yet — deferred to avoid unilaterally changing an ADR-mandated build environment.
- **Next Step:** Decide on a fix that preserves the glibc 2.35 baseline while providing Python 3.11+: e.g., install Python 3.11 from the deadsnakes PPA inside the container, or switch to a `python:3.11`-based image with glibc 2.35/2.36. Record the choice as a new ADR before changing the script.
