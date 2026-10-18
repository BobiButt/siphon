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
#### Added
- Executed the M5 AppImage build pipeline for the first time via `scripts/build_appimage.sh` on the host (Fedora 44), producing `dist/Siphon-0.1.0-x86_64.AppImage` (30 MB, static Type 2 runtime). Smoke test passed: `--version` → `Siphon 0.1.0`, exit code 0. Documented the host-glibc (2.43) caveat versus the release-grade glibc-2.35 containerized target.
- Added three GitHub Actions workflows for M6:
  - `.github/workflows/test.yml`: pytest matrix across Python 3.11 and 3.12 on push/PR.
  - `.github/workflows/build.yml`: containerized `build_in_docker.sh`, `--version` smoke test, and AppImage artifact upload.
  - `.github/workflows/release.yml`: triggered on `v*` tags; builds, smoke-tests, generates `SHA256SUMS.txt`, and publishes the AppImage + checksums to a GitHub Release.
- Added `tests/test_ci.py` validating the structure of all three workflow definitions (Python matrix, containerized build invocation, artifact/release asset wiring, tag trigger, and `contents:write` permission). Suite now totals 28 passing tests.
- Added `.cache/` to `.gitignore` (build-tooling download cache for `appimagetool` and the static Type 2 runtime).

### Session 3 — 2026-10-18 (Milestone 7: Search, Streaming & UI Polish)
#### Added
- **YouTube search backend:** `search_youtube(query, limit)` in the extractor using yt-dlp `ytsearch<limit>:` with `extract_flat=True` for fast, batched metadata-only search; returns `{id, title, uploader, duration, thumbnail, url}`. New endpoint `GET /api/search?q=...&limit=...`.
- **Direct streaming:** `extract_video_info` now returns `stream_url` (the highest-quality progressive/muxed direct URL, or `null` when none exists); new `extract_stream_url()` + endpoint `GET /api/stream?url=...` resolving a playable URL via the `best[acodec!=none][vcodec!=none]/best` selector.
- **FFmpeg startup check:** `ffmpeg_available()` and `check_ffmpeg_or_warn()` in `ffmpeg_muxer.py`; `create_app()` logs a clear warning when `assets/ffmpeg/ffmpeg` is missing (covers GUI and `--headless`).
- **YouTube-clone UI:** top search bar with Enter-to-search, responsive CSS-grid results (thumbnail/title/uploader/duration badge), click-to-load info, and an HTML5 `<video>` player that plays progressive streams or shows "Streaming requires muxed audio/video."
- **Format-list scroll fix:** `.format-list` capped at `max-height: 300px` with `overflow-y: auto` and a styled scrollbar, resolving the unbounded "loooooooooong div."
- **Icon pipeline:** `scripts/gen_icons.sh` rewritten to square-pad-scale the new raster `icon.png` (300×294 → distortion-free 16/32/48/64/128/256/512 set); `.desktop` entry updated for the YouTube-clone positioning (Comment/Keywords/Categories).
- Version bumped to **0.2.0**; `tests/test_m7_search_stream.py` added (search/stream/FFmpeg unit + endpoint coverage). Suite now totals 41 passing tests.
