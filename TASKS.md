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

## [ ] Milestone 2: yt-dlp Extraction Engine
- [ ] Implement yt-dlp Python API wrapper in `src/siphon/extractors/youtube.py` with custom logger and quiet extract options.
- [ ] Parse YouTube video metadata (video ID, title, channel name, duration, view count, high-res thumbnail URL).
- [ ] Parse and categorize stream formats into progressive (combined video+audio) and adaptive DASH formats (video-only up to 4K, audio-only formats).
- [ ] Create FastAPI endpoint `POST /api/info` taking a YouTube URL, validating format, and returning structured stream options.
- [ ] Add defensive error handling for invalid URLs, private/restricted videos, geo-blocks, and network timeouts.
- [ ] Write pytest test suite in `tests/test_extractor.py` utilizing mocked yt-dlp extractors and recorded sample payloads.

---

## [ ] Milestone 3: Download Pipeline & Static FFmpeg Muxing
- [ ] Create `scripts/fetch_ffmpeg.sh` to download pinned BtbN static Linux x86_64 FFmpeg binary into `assets/ffmpeg/ffmpeg` with `chmod 0755`.
- [ ] Implement download manager in `src/siphon/downloader/manager.py` handling active downloads, cancelation tokens, and destination directory resolution.
- [ ] Implement yt-dlp progress hook emitting real-time percentage, download speed, ETA, and state transitions (downloading, muxing, completed, error).
- [ ] Configure yt-dlp post-processor to execute bundled static FFmpeg (`assets/ffmpeg/ffmpeg`) for automatic DASH video/audio stream muxing.
- [ ] Create FastAPI endpoints `POST /api/download` (start download) and `GET /api/download/{id}/status` or WebSocket streaming for live progress.
- [ ] Write pytest test suite in `tests/test_downloader.py` verifying download job state machine, FFmpeg path resolution, and error propagation.

---

## [ ] Milestone 4: Native pywebview Desktop Shell & UI
- [ ] Build responsive, modern frontend in `frontend/index.html`, `frontend/style.css`, and `frontend/app.js` (URL input, video card preview, format selector, download manager).
- [ ] Implement desktop shell launcher in `src/siphon/app.py` combining Uvicorn background server thread with `pywebview.create_window`.
- [ ] Connect pywebview window lifecycle to server shutdown, ensuring closing the window terminates the Uvicorn process cleanly.
- [ ] Wire frontend UI events to backend REST endpoints with live progress bars, status indicators, and notification toasts.
- [ ] Add CLI arguments (`--headless`, `--port`, `--debug`) to `src/siphon/__main__.py` to facilitate automated testing and debugging.
- [ ] Write test cases in `tests/test_app_lifecycle.py` verifying clean startup and shutdown in headless mode.

---

## [ ] Milestone 5: Desktop Packaging & AppImage Generation
- [ ] Create vector icon in `assets/icons/icon.svg` and write `scripts/gen_icons.sh` converting it to standard PNG sizes (16px to 512px).
- [ ] Create XDG desktop entry `assets/io.github.BobiButt.siphon.desktop` specifying Name, Exec, Icon, Categories, and reverse-DNS desktop ID.
- [ ] Create PyInstaller build specification `siphon.spec` bundling Python runtime, static assets, bundled FFmpeg, and frontend assets.
- [ ] Implement AppDir structure generator assembly script `scripts/build_appimage.sh` with AppRun entrypoint.
- [ ] Implement `scripts/build_in_docker.sh` executing the build inside `ubuntu:22.04` using the static Type 2 AppImage runtime (`--runtime-file`).
- [ ] Verify generated `Siphon-<version>-x86_64.AppImage` executes correctly, displays the proper icon, and runs without host `libfuse2`.

---

## [ ] Milestone 6: Continuous Integration & Automated Releases
- [ ] Configure GitHub Actions workflow `.github/workflows/test.yml` running pytest across Python 3.11 and 3.12.
- [ ] Configure GitHub Actions workflow `.github/workflows/build.yml` executing `scripts/build_in_docker.sh` to generate the AppImage artifact.
- [ ] Configure release workflow `.github/workflows/release.yml` triggered on git tags (`v*`) to upload `Siphon-<version>-x86_64.AppImage` and SHA-256 checksums.
- [ ] Write end-to-end smoke verification test ensuring AppImage binary executes `--version` and exits with code 0.
