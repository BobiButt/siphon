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
