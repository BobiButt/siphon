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
- Session 1 — implemented dynamic Uvicorn server and health check:
  - Implemented `SiphonServer` and `start_server()` in `src/siphon/server.py` with programmatic Uvicorn runner, dynamic port-0 binding on `127.0.0.1`, and ephemeral port extraction via socket inspection.
  - Implemented `create_app()` in `src/siphon/app.py` providing `/health` endpoint and mounting `frontend/` static assets at `/`.
  - Added CLI entry point in `src/siphon/__main__.py` supporting `--headless` execution, localhost verification, and graceful SIGINT/SIGTERM shutdown.
  - Added integration test suite in `tests/test_server.py` verifying non-8000 dynamic port assignment, HTTP `/health` JSON response, and clean socket teardown.
- Session 1 — implemented yt-dlp extraction, format parsing, and API endpoint:
  - Implemented `extract_video_info` in `src/siphon/extractors/ytdlp_extractor.py` utilizing native `yt_dlp.YoutubeDL` Python API with quiet options.
  - Parsed metadata and categorized formats into progressive, video-only DASH (1080p, 1440p, 4K), and audio-only streams.
  - Implemented `GET /api/info?url=...` endpoint in `src/siphon/api.py` with 400 Bad Request error mapping.
  - Added offline unit test suites in `tests/test_extractor.py` and `tests/test_api.py` utilizing mocked yt-dlp fixtures.
- Session 1 — implemented download pipeline, FFmpeg muxing, and download endpoint:
  - Implemented `download_media` in `src/siphon/downloader/core.py` detecting DASH video-only streams and retrieving complementary audio tracks for muxing.
  - Implemented `mux_streams` in `src/siphon/downloader/ffmpeg_muxer.py` using bundled static FFmpeg with `-c:v copy -c:a aac` and temporary stream file cleanup.
  - Implemented `POST /api/download` in `src/siphon/api.py` orchestrating stream downloads and muxing.
  - Added unit test suite in `tests/test_downloader.py` covering DASH resolution, exact FFmpeg command generation, error handling, and API integration.
- Session 1 — implemented native pywebview shell and frontend UI:
  - Created vector icon `assets/icons/icon.svg` and implemented `scripts/gen_icons.sh` generating `assets/icons/icon.png` (256x256).
  - Built clean, responsive dark-themed frontend in `frontend/index.html`, `frontend/style.css`, and `frontend/app.js` with metadata preview and 3-tier format selection.
  - Implemented `launch_app` in `src/siphon/launcher.py` integrating dynamic port-0 Uvicorn background server with main-thread pywebview WebKitGTK window.
  - Connected pywebview window lifecycle to trigger clean server shutdown upon window closure.
  - Updated `src/siphon/__main__.py` to dispatch to `launch_app` in default GUI mode while retaining `--headless` debugging mode.
  - Added unit test suite in `tests/test_launcher.py` validating window lifecycle, URL construction, and graceful server teardown.
- Session 1 — implemented PyInstaller packaging and AppImage build script:
  - Configured `Siphon.spec` in ONEDIR mode bundling frontend and icon datas, with explicit hidden imports for Uvicorn, FastAPI, and Pydantic.
  - Implemented `scripts/build_appimage.sh` assembling standard AppDir hierarchy, desktop entry, AppRun, bundled static FFmpeg, and embedding static Type 2 runtime (`--runtime-file`).
  - Created XDG desktop entry `assets/io.github.BobiButt.siphon.desktop`.
  - Implemented `scripts/build_in_docker.sh` for reproducible Ubuntu 22.04 containerized compilation.
  - Documented host Runtime Dependencies in `README.md` and `DEV_SETUP.md`.
  - Added unit tests in `tests/test_packaging.py` verifying build failure handling, spec hidden imports, and desktop entry fields.

### Session 2 — 2026-10-18
#### Fixed
- Removed the unsupported `icon=icon_arg` keyword argument from the `webview.create_window()` call in `src/siphon/launcher.py`, which previously raised a `TypeError` on GUI launch. `pywebview`'s `create_window()` API does not accept an `icon` parameter; desktop icon integration is delegated to the AppImage and the XDG `.desktop` entry (per ADR-001 / M5). Also removed the now-dead `icon_path` parameter, its default-resolution block, and the unused `os`/`Path`/`Optional` imports. All 24 tests pass.
