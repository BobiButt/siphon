# Project State — Siphon

## Current Milestone
**M7: Search, Streaming & UI Pivot (YouTube Clone)** — implementation complete and 41 tests passing; **awaiting local user testing before the final AppImage build.**

---

## ✅ Completed
- **Handoff File System Initialized:** Created all core governance and context persistence files at the repository root (`AI_HANDOFF.md`, `PROJECT_STATE.md`, `ARCHITECTURE.md`, `TASKS.md`, `KNOWN_ISSUES.md`, `DEV_SETUP.md`, `CHANGELOG.md`).
- **Prompt Archives Established:** Documented original project specifications and requirements in `prompts/kickoff.md` and created the standard reusable agent onboarding prompt in `prompts/handoff.md`.
- **Architectural Baseline Established:** Formulated ADRs covering naming identity, pywebview desktop runtime, dynamic port allocation on localhost, yt-dlp native extraction, static FFmpeg binary strategy, Docker-based Ubuntu 22.04 packaging, and static Type 2 AppImage runtime.
- **Development Roadmap Outlined:** Broken down milestones M0 through M6 with atomic, testable checkboxes.
- **Project Scaffold Created:**
  - Package tree initialized under `src/siphon/` (`__init__.py`, `app.py`, `server.py`, `launcher.py`).
  - Extractor and downloader modules stubbed (`src/siphon/extractors/ytdlp_extractor.py`, `src/siphon/downloader/ffmpeg_muxer.py`).
  - Frontend scaffolding established (`frontend/index.html` with `<title>Siphon</title>`, `frontend/style.css`, `frontend/app.js`).
  - Packaging configuration created (`pyproject.toml`, `requirements.txt`, `.gitignore`, `LICENSE`, `README.md`).
  - Scripts stubbed (`scripts/gen_icons.sh`, `scripts/build_appimage.sh`, `scripts/fetch_ffmpeg.sh`, `scripts/build_in_docker.sh`).
- **M1 Backend Core & Dynamic Server:**
  - Implemented `SiphonServer` and `start_server` in `src/siphon/server.py` programmatically wrapping Uvicorn on `127.0.0.1:0` and extracting ephemeral port via socket inspection.
  - Implemented `create_app()` in `src/siphon/app.py` with `/health` endpoint returning `{"status": "ok", "app": "siphon"}` and static file mounting for `frontend/` at `/`.
  - Implemented CLI runner in `src/siphon/__main__.py` with `--headless` flag, localhost constraint enforcement, and graceful SIGINT/SIGTERM termination.
  - Created integration test suite in `tests/test_server.py` verifying dynamic port allocation (non-8000), `/health` payload, clean shutdown, and root static file serving.
- **M2 yt-dlp Extraction Engine:**
  - Implemented `extract_video_info()` in `src/siphon/extractors/ytdlp_extractor.py` using native `yt_dlp.YoutubeDL` Python API with quiet options.
  - Parsed video metadata (`title`, `duration`, `thumbnail`, `uploader`, `id`) and categorized streams into progressive, video-only DASH (1080p, 1440p, 4K), and audio-only formats.
  - Implemented `GET /api/info?url=...` in `src/siphon/api.py` with clean 400 Bad Request error handling.
  - Wrote comprehensive offline mock unit tests in `tests/test_extractor.py` and `tests/test_api.py`.
- **M3 Download Pipeline & Static FFmpeg Muxing:**
  - Implemented `download_media()` in `src/siphon/downloader/core.py` detecting DASH video-only streams and downloading companion audio streams for muxing.
  - Implemented `mux_streams()` in `src/siphon/downloader/ffmpeg_muxer.py` executing bundled static FFmpeg (`assets/ffmpeg/ffmpeg`) with `-c:v copy -c:a aac`, error capture via `MuxingError`, and temporary source cleanup.
  - Implemented `POST /api/download` in `src/siphon/api.py` orchestrating stream downloads and muxing.
  - Wrote unit tests in `tests/test_downloader.py` validating DASH resolution, exact FFmpeg command generation, failure raising, and API route execution.
- **M4 Native pywebview Shell & Frontend:**
  - Created vector icon `assets/icons/icon.svg` and generated 256x256 PNG `assets/icons/icon.png` via `scripts/gen_icons.sh`.
  - Built dark-mode responsive UI in `frontend/index.html`, `style.css`, and `app.js` with metadata preview and 3 separate format streams.
  - Implemented `launch_app()` in `src/siphon/launcher.py` with dynamic port binding, WebKitGTK window launch on main thread, and graceful shutdown on close.
  - Updated `src/siphon/__main__.py` to dispatch to `launch_app()` in GUI mode and keep `--headless` mode.
  - Added unit test suite in `tests/test_launcher.py` with GUI mocking, verifying port forwarding, `webview.start`, and shutdown.
- **M5 Desktop Packaging & AppImage Generation:**
  - Configured `Siphon.spec` in ONEDIR mode bundling frontend and icon datas, with explicit hidden imports for Uvicorn, FastAPI, and Pydantic.
  - Implemented `scripts/build_appimage.sh` assembling the standard AppDir layout, configuring `siphon.desktop` and `AppRun`, bundling static FFmpeg, and embedding the static Type 2 runtime (`--runtime-file`).
  - Created XDG desktop entry `assets/io.github.BobiButt.siphon.desktop`.
  - Implemented containerized build wrapper in `scripts/build_in_docker.sh` targeting `ubuntu:22.04` for glibc 2.35 compatibility.
  - Documented Runtime Dependencies in `DEV_SETUP.md` and `README.md`.
  - Wrote packaging unit tests in `tests/test_packaging.py` verifying build failure handling, spec hidden imports, and desktop entry fields. All 24 tests passing.
- **Launcher Bug Fix (Session 2):** Removed the unsupported `icon=icon_arg` argument from `webview.create_window()` in `src/siphon/launcher.py`, which previously raised a `TypeError` on GUI launch. Also removed the dead `icon_path` plumbing and now-unused imports. All 24 tests remain green.
- **M5 AppImage Build Executed (Session 2):** Ran `scripts/build_appimage.sh` on the host (Fedora 44). Successfully produced `dist/Siphon-0.1.0-x86_64.AppImage` (30 MB, static Type 2 runtime — `static-pie linked`, no `libfuse2` dependency). Smoke test passed: `./Siphon-0.1.0-x86_64.AppImage --version` → `Siphon 0.1.0`, exit code 0. **Caveat:** host glibc is 2.43, so this locally-built artifact targets glibc ≥ 2.43 and is **not** the release-grade glibc-2.35 build. The official artifact must come from the containerized build (`scripts/build_in_docker.sh`), which will run in CI.
- **M6 CI Workflows Authored (Session 2):** Created `.github/workflows/test.yml` (pytest matrix on Python 3.11 + 3.12), `build.yml` (containerized `build_in_docker.sh` + `--version` smoke test + artifact upload), and `release.yml` (triggered on `v*` tags; builds, smoke-tests, generates SHA-256 checksums, and publishes to a GitHub Release). Added `tests/test_ci.py` validating workflow structure. All 28 tests pass.
- **M7 Search Backend (Session 3):** `search_youtube()` using `ytsearch<n>:` + `extract_flat=True`; `GET /api/search?q=...` endpoint returning `{id, title, uploader, duration, thumbnail, url}`. Limit clamped to [1, 50].
- **M7 Streaming (Session 3):** `stream_url` (best progressive direct URL) added to `/api/info`; new `extract_stream_url()` + `GET /api/stream?url=...`. FFmpeg availability check (`ffmpeg_available` / `check_ffmpeg_or_warn`) logs a clear startup warning from `create_app()`.
- **M7 YouTube-Clone UI (Session 3):** Search bar (Enter-to-search), responsive CSS-grid results, click-to-load info, HTML5 `<video>` player with the "Streaming requires muxed audio/video" fallback, and the `.format-list` "long div" bug fixed via `max-height: 300px` + `overflow-y: auto`.
- **M7 Icon + Version (Session 3):** `gen_icons.sh` rewritten to square-pad-scale the new raster `icon.png` (300×294 → distortion-free 16–512 set); `.desktop` refreshed; version bumped to 0.2.0. New suite `tests/test_m7_search_stream.py`. **All 41 tests passing.**
- **Bot-Check Cookie Support & Search Thumbnail Fix (Session 4):** All yt-dlp call sites now use `_build_ydl_opts()`, attaching `cookiefile` when `~/.config/siphon/cookies.txt` exists; the "Sign in to confirm you're not a bot" error is caught specifically and surfaced as clear guidance. `search_youtube` switched to `extract_flat=False` so thumbnails/durations populate correctly. Cookie workaround documented in `README.md` and `DEV_SETUP.md`. **All 46 tests passing.**

---

## 🚧 In Progress
- **Awaiting Local Test (M7):** The YouTube-clone pivot plus the bot-check/thumbnail fixes are implemented and committed. The user will test locally (`python -m siphon`) before we run the final AppImage build.

---

## ⏭️ Next Up
1. **User local test (M7):** Verify search, playback, format lists, and the new icon in the running app.
2. **Final AppImage rebuild:** After local sign-off, run `./scripts/build_in_docker.sh` (glibc 2.35) to produce the release-grade 0.2.0 artifact — requires the Docker daemon to be started.
3. **First CI Run (M6):** Push and confirm `test.yml` + `build.yml` pass on GitHub runners.
4. **Container Python Parity (M6):** Resolve ISSUE-002 (`ubuntu:22.04` Python 3.10 vs `requires-python >= 3.11`) before the first tagged release.

---

## 🔧 Environment Notes
- **Target Platform:** Linux x86_64 with glibc >= 2.35 (Ubuntu 22.04 LTS baseline).
- **Python Version:** Python 3.11+ required.
- **Host GUI Runtime Dependencies:** Requires GTK 3 and WebKit2GTK for pywebview execution (`gir1.2-webkit2-4.0` / `gir1.2-webkit2-4.1` on Debian/Ubuntu, `webkit2gtk3` on Fedora, `webkit2gtk` on Arch).
- **Packaging Pipeline:** PyInstaller builds run inside an `ubuntu:22.04` Docker container for glibc compatibility; `appimagetool` is configured with the static Type 2 runtime (`appimagetool-x86_64.AppImage` runtime) to eliminate any host `libfuse2` requirement.
- **Unsupported Environments:** Alpine Linux and other musl-libc based systems are explicitly unsupported.
