# Development Tasks & Roadmap — Siphon

This document tracks all implementation milestones and atomic tasks for Siphon. Each feature task must have an accompanying `pytest` test before being checked off.

---

## [x] Milestone 0: Handoff File System & Project Governance
- [x] Create `AI_HANDOFF.md` containing project summary, fixed technology stack, sequential reading order, milestone status, and non-negotiable agent operating rules.
- [x] Create `PROJECT_STATE.md` with current milestone, completed milestones, active work, upcoming priorities, and system environment specifications.
- [x] Create `ARCHITECTURE.md` logging dated ADRs for naming, pywebview, dynamic port 0 binding, yt-dlp, AppImage packaging, pinned BtbN FFmpeg, Ubuntu 22.04 Docker builds, and static Type 2 runtime.
- [x] Create `TASKS.md` with complete milestones (M0 through M6) and at least 4 atomic tasks per milestone.
- [x] Create `KNOWN_ISSUES.md` with issue diagnostic template and initial empty-state register.
- [x] Create `DEV_SETUP.md` with comprehensive per-distro dependencies, venv setup, run/test commands, FFmpeg fetching, and containerized AppImage build workflows.
- [x] Create `CHANGELOG.md` with Keep a Changelog structure and Session 1 initial entry.
- [x] Archive kickoff specifications in `prompts/kickoff.md` and define standardized agent onboarding instructions in `prompts/handoff.md`.
- [x] Establish git repository baseline and commit handoff documentation.

---

## [x] Milestone 1: Backend Core & Dynamic Server
- [x] Initialize project packaging configuration (`pyproject.toml`, `requirements.txt`, `.gitignore`, `LICENSE`, `README.md`).
- [x] Create core Python package and frontend scaffolding (`src/siphon/`, `frontend/`, `tests/`, `scripts/`).
- [x] Implement Uvicorn server launcher binding dynamically to `127.0.0.1:0` and exposing a thread-safe port accessor.
- [x] Implement FastAPI application instance with `/health` endpoint returning structured JSON.
- [x] Mount frontend static file directory in FastAPI (`/` serving `frontend/index.html`).
- [x] Write pytest test suite in `tests/test_server.py` verifying dynamic port assignment, socket accessibility, and health check response.

---

## [x] Milestone 2: yt-dlp Extraction Engine
- [x] Implement yt-dlp Python API wrapper in `src/siphon/extractors/ytdlp_extractor.py` with quiet extract options.
- [x] Parse YouTube video metadata (video ID, title, uploader, duration, thumbnail URL).
- [x] Parse and categorize stream formats into progressive, video-only DASH (1080p/4K), and audio-only formats.
- [x] Create FastAPI endpoint `GET /api/info?url=...` validating URL and returning structured format options.
- [x] Add defensive error handling for invalid/empty URLs and yt-dlp `DownloadError` exceptions (HTTP 400).
- [x] Write pytest test suites in `tests/test_extractor.py` and `tests/test_api.py` utilizing mocked yt-dlp extractors.

---

## [x] Milestone 3: Download Pipeline & Static FFmpeg Muxing
- [x] Scaffold and configure static FFmpeg binary fetch pipeline (`scripts/fetch_ffmpeg.sh`).
- [x] Implement `download_media` in `src/siphon/downloader/core.py` resolving companion audio for DASH streams.
- [x] Implement `mux_streams` in `src/siphon/downloader/ffmpeg_muxer.py` invoking bundled FFmpeg with `-c:v copy -c:a aac` and temporary file cleanup.
- [x] Create FastAPI endpoint `POST /api/download` executing download and muxing pipeline.
- [x] Write pytest test suite in `tests/test_downloader.py` verifying DASH stream separation, exact FFmpeg command generation, failure raising, and `/api/download` execution.

---

## [x] Milestone 4: Native pywebview Desktop Shell & UI
- [x] Build responsive, modern dark-themed frontend in `frontend/index.html`, `frontend/style.css`, and `frontend/app.js` (URL input, video card preview, format selector, download manager).
- [x] Create vector icon `assets/icons/icon.svg` and implement `scripts/gen_icons.sh` generating `assets/icons/icon.png`.
- [x] Implement desktop shell launcher in `src/siphon/launcher.py` combining Uvicorn background server with `pywebview.create_window` on main thread.
- [x] Connect pywebview window lifecycle to server shutdown, ensuring closing the window terminates the Uvicorn process cleanly.
- [x] Update `src/siphon/__main__.py` to dispatch `launch_app()` for GUI mode and preserve `--headless` mode for debugging.
- [x] Write pytest test suite in `tests/test_launcher.py` verifying URL construction, `webview.start` invocation, and graceful shutdown.

---

## [x] Milestone 5: Desktop Packaging & AppImage Generation
- [x] Create vector icon in `assets/icons/icon.svg` and implement `scripts/gen_icons.sh`.
- [x] Create XDG desktop entry `assets/io.github.BobiButt.siphon.desktop` specifying Name, Exec, Icon, and Categories.
- [x] Create PyInstaller spec `Siphon.spec` in ONEDIR mode bundling frontend and icon assets with hidden imports.
- [x] Implement AppDir assembly in `scripts/build_appimage.sh` with AppRun entrypoint, desktop symlinks, and FFmpeg binary.
- [x] Implement containerized build script `scripts/build_in_docker.sh` using Ubuntu 22.04 and static Type 2 runtime.
- [x] Write pytest test suite in `tests/test_packaging.py` verifying build failure detection and desktop entry attributes.

---

## [x] Milestone 6: Continuous Integration & Automated Releases
- [x] Configure GitHub Actions workflow `.github/workflows/test.yml` running pytest across Python 3.11 and 3.12.
- [x] Configure GitHub Actions workflow `.github/workflows/build.yml` executing `scripts/build_in_docker.sh` to generate the AppImage artifact.
- [x] Configure release workflow `.github/workflows/release.yml` triggered on git tags (`v*`) to upload `Siphon-<version>-x86_64.AppImage` and SHA-256 checksums.
- [x] Write end-to-end smoke verification test ensuring AppImage binary executes `--version` and exits with code 0. (Implemented as a `--version` smoke-test step in `build.yml`/`release.yml`; structure guarded by `tests/test_ci.py`. Locally verified: `Siphon-0.1.0-x86_64.AppImage --version` → exit 0.)
