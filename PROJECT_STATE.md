# Project State — Siphon

## Current Milestone
**M0: Handoff File System** (Satisfied, transitioning to **M1: Backend Core & Scaffolding**)

---

## ✅ Completed
- **Handoff File System Initialized:** Created all core governance and context persistence files at the repository root (`AI_HANDOFF.md`, `PROJECT_STATE.md`, `ARCHITECTURE.md`, `TASKS.md`, `KNOWN_ISSUES.md`, `DEV_SETUP.md`, `CHANGELOG.md`).
- **Prompt Archives Established:** Documented original project specifications and requirements in `prompts/kickoff.md` and created the standard reusable agent onboarding prompt in `prompts/handoff.md`.
- **Architectural Baseline Established:** Formulated ADRs covering naming identity, pywebview desktop runtime, dynamic port allocation on localhost, yt-dlp native extraction, static FFmpeg binary strategy, Docker-based Ubuntu 22.04 packaging, and static Type 2 AppImage runtime.
- **Development Roadmap Outlined:** Broken down milestones M0 through M6 with atomic, testable checkboxes.

---

## 🚧 In Progress
- **Project Scaffold:** Preparing the standard directory structure:
  - `src/siphon/` (core application package, Uvicorn server launcher, pywebview window wrapper).
  - `src/siphon/extractors/` (yt-dlp Python API abstraction).
  - `src/siphon/downloader/` (download management, stream merging via FFmpeg).
  - `frontend/` (static HTML, CSS, JS served by FastAPI).
  - `scripts/` (utility scripts for static FFmpeg retrieval, icon generation, Docker builds, and AppImage compilation).
  - `assets/icons/` and `assets/ffmpeg/` (visual identity and binary assets).
  - `tests/` (unit and integration tests with pytest).
  - Package metadata and configuration (`pyproject.toml`, `requirements.txt`, `.gitignore`, `LICENSE`, `README.md`).

---

## ⏭️ Next Up
1. **Repository Scaffolding:** Create directory trees, `.gitignore` (ignoring `assets/ffmpeg/ffmpeg`, virtual environments, Python caches, and build artifacts), MIT `LICENSE`, `pyproject.toml`, and `requirements.txt`.
2. **FFmpeg Setup Script:** Write `scripts/fetch_ffmpeg.sh` to download the pinned static BtbN FFmpeg Linux x86_64 binary and verify executable permissions.
3. **M1 Backend Core:** Implement the Uvicorn server startup with dynamic OS port allocation (`port=0` on `127.0.0.1`), health check endpoints (`/api/health`, `/api/version`), and initial pytest test cases.
4. **Desktop Icon Assets:** Place the base SVG icon at `assets/icons/icon.svg` and provide `scripts/gen_icons.sh`.

---

## 🔧 Environment Notes
- **Target Platform:** Linux x86_64 with glibc >= 2.35 (Ubuntu 22.04 LTS baseline).
- **Python Version:** Python 3.11+ required.
- **Host GUI Runtime Dependencies:** Requires GTK 3 and WebKit2GTK for pywebview execution (e.g., `gir1.2-webkit2-4.0` / `gir1.2-webkit2-4.1` on Debian/Ubuntu, `webkit2gtk3` / `webkit2gtk4.1` on Fedora, `webkit2gtk` on Arch).
- **Packaging Pipeline:** PyInstaller builds run inside an `ubuntu:22.04` Docker container for glibc compatibility; `appimagetool` is configured with the static Type 2 runtime (`appimagetool-x86_64.AppImage` runtime) to eliminate any host `libfuse2` requirement.
- **Unsupported Environments:** Alpine Linux and other musl-libc based systems are explicitly unsupported.
