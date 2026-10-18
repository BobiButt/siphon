# Project State — Siphon

## Current Milestone
**M1: Backend Core & Dynamic Server** (Scaffold complete, entering core implementation)

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
  - Test harness initialized (`tests/__init__.py`, `tests/test_placeholder.py`) with 100% passing pytest run.

---

## 🚧 In Progress
- **M1 Backend Core:** Implementing Uvicorn port-0 server launcher, FastAPI application factory, and dynamic socket port inspection.

---

## ⏭️ Next Up (M1 Tasks)
1. **Dynamic Port Uvicorn Server:** Implement thread-safe Uvicorn background runner in `src/siphon/server.py` binding to `127.0.0.1:0` and reading back the kernel-assigned ephemeral port.
2. **FastAPI Application Setup:** Implement `create_app()` in `src/siphon/app.py` with `/api/health` and `/api/version` endpoints returning application status and metadata.
3. **Static Frontend Mount:** Mount `frontend/` directory in FastAPI to serve `index.html`, `style.css`, and `app.js` at root `/`.
4. **Backend Test Suite:** Create `tests/test_server.py` using `pytest` and `httpx` to verify dynamic port binding, socket accessibility, and health responses.

---

## 🔧 Environment Notes
- **Target Platform:** Linux x86_64 with glibc >= 2.35 (Ubuntu 22.04 LTS baseline).
- **Python Version:** Python 3.11+ required.
- **Host GUI Runtime Dependencies:** Requires GTK 3 and WebKit2GTK for pywebview execution (`gir1.2-webkit2-4.0` / `gir1.2-webkit2-4.1` on Debian/Ubuntu, `webkit2gtk3` on Fedora, `webkit2gtk` on Arch).
- **Packaging Pipeline:** PyInstaller builds run inside an `ubuntu:22.04` Docker container for glibc compatibility; `appimagetool` is configured with the static Type 2 runtime (`appimagetool-x86_64.AppImage` runtime) to eliminate any host `libfuse2` requirement.
- **Unsupported Environments:** Alpine Linux and other musl-libc based systems are explicitly unsupported.
