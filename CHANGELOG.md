# Changelog — Siphon

All notable changes to the Siphon project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Session 1 — 2026-10-18
#### Added
- Initialized Phase 0 AI handoff documentation system for context persistence across agent sessions:
  - `AI_HANDOFF.md`: Primary entry point, fixed stack definition, sequential reading order, and agent operating rules.
  - `PROJECT_STATE.md`: Real-time snapshot of completed milestones, in-progress tasks, and environment constraints.
  - `ARCHITECTURE.md`: Dated Architectural Decision Records (ADRs) covering naming conventions, pywebview shell, dynamic port 0 binding, yt-dlp native extraction, PyInstaller + AppImage packaging, pinned BtbN FFmpeg binary fetch, containerized Ubuntu 22.04 builds, and static Type 2 AppImage runtime.
  - `TASKS.md`: Roadmap covering Milestones M0 through M6 with atomic checkboxes for all engineering phases.
  - `KNOWN_ISSUES.md`: Issue logging template and empty register.
  - `DEV_SETUP.md`: Complete developer onboarding guide with distro package commands, virtual environment management, FFmpeg fetching, and containerized AppImage compilation.
  - `CHANGELOG.md`: Standardized changelog tracking project changes and session progress.
  - `prompts/kickoff.md`: Verbatim archive of initial project kickoff brief and requirements.
  - `prompts/handoff.md`: Standardized prompt template for incoming AI agents resuming development.
- Verified Phase 0 requirements and gated progression to Phase 1 pending user approval.
- Session 1 — scaffolded project structure:
  - Created package layout under `src/siphon/` (`__init__.py`, `app.py`, `server.py`, `launcher.py`).
  - Added module stubs for extractors (`ytdlp_extractor.py`) and downloader (`ffmpeg_muxer.py`).
  - Created zero-build frontend stubs (`frontend/index.html` with `<title>Siphon</title>`, `style.css`, `app.js`).
  - Created project metadata and configuration (`pyproject.toml`, `requirements.txt`, `.gitignore`, `LICENSE`, `README.md`).
  - Created packaging and setup scripts (`scripts/gen_icons.sh`, `scripts/build_appimage.sh`, `scripts/fetch_ffmpeg.sh`, `scripts/build_in_docker.sh`).
  - Initialized test harness with `tests/test_placeholder.py` verifying package metadata and passing with pytest.
