# Project State — Siphon

## Current Milestone
**M6: Continuous Integration & Automated Releases** (Milestones 0 through 5 satisfied; entering CI/CD phase)

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
- **Launcher Bug Fix (Session 2):** Removed the unsupported `icon=icon_arg` argument from `webview.create_window()` in `src/siphon/launcher.py`, which previously raised a `TypeError` on GUI launch. Also removed the dead `icon_path` plumbing and now-unused imports. All 24 tests remain green. (Note: the AppImage artifact itself has not yet been built — `dist/` does not exist.)

---

## 🚧 In Progress
- **M6 CI & Automated Releases:** Configuring GitHub Actions workflows for automated testing, containerized AppImage builds, and tagged release distribution.

---

## ⏭️ Next Up (M6 Tasks)
1. **Automated Testing Workflow:** Create `.github/workflows/test.yml` running pytest across Python 3.11 and 3.12.
2. **Containerized Build Workflow:** Create `.github/workflows/build.yml` executing `scripts/build_in_docker.sh` and publishing AppImage artifact.
3. **Tagged Release Workflow:** Create `.github/workflows/release.yml` publishing `Siphon-<version>-x86_64.AppImage` and SHA-256 checksums to GitHub Releases on tag push.
4. **Final Smoke Verification:** Execute verification suite to ensure all milestones and handoff criteria are satisfied.

---

## 🔧 Environment Notes
- **Target Platform:** Linux x86_64 with glibc >= 2.35 (Ubuntu 22.04 LTS baseline).
- **Python Version:** Python 3.11+ required.
- **Host GUI Runtime Dependencies:** Requires GTK 3 and WebKit2GTK for pywebview execution (`gir1.2-webkit2-4.0` / `gir1.2-webkit2-4.1` on Debian/Ubuntu, `webkit2gtk3` on Fedora, `webkit2gtk` on Arch).
- **Packaging Pipeline:** PyInstaller builds run inside an `ubuntu:22.04` Docker container for glibc compatibility; `appimagetool` is configured with the static Type 2 runtime (`appimagetool-x86_64.AppImage` runtime) to eliminate any host `libfuse2` requirement.
- **Unsupported Environments:** Alpine Linux and other musl-libc based systems are explicitly unsupported.
