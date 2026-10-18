# AI Handoff & Continuity Guide — Siphon

## Project Summary
**Siphon** is an open-source, NewPipe-inspired Linux desktop application built to provide a clean, fast, and reliable way to inspect and download YouTube videos and audio. Users paste a video URL, browse available stream formats (including high-resolution DASH 1080p, 1440p, 4K video-only streams and separate audio streams), select their desired quality, and download muxed media files directly to their local drive. Siphon is packaged and distributed as a standalone, zero-dependency x86_64 AppImage with native desktop integration, desktop entry, and icons.

## Fixed Technology Stack
The architectural foundation of Siphon is established and fixed. Do not re-litigate or alter these core choices:
- **Backend:** FastAPI + Uvicorn running on Python 3.11+.
- **Extraction Engine:** `yt-dlp` using its native Python API (`yt_dlp.YoutubeDL`), avoiding external CLI subprocess wrappers wherever possible.
- **Media Muxing:** Pinned static FFmpeg binary located at `assets/ffmpeg/ffmpeg`, fetched via `scripts/fetch_ffmpeg.sh`.
- **Desktop Shell:** `pywebview` rendering a native WebKitGTK desktop window on Linux.
- **Frontend:** Zero-build vanilla HTML5, CSS3, and modern JavaScript served directly by the FastAPI static mount.
- **Packaging:** PyInstaller compiles the Python application into a standalone binary bundle, packaged into an AppDir, and converted into an AppImage via `appimagetool` using the static Type 2 runtime (`libfuse2`-independent).
- **Network & Port Strategy:** Uvicorn strictly binds to `127.0.0.1` on port `0` (dynamic OS ephemeral assignment), reads back the allocated port, and launches `pywebview` directed at `http://127.0.0.1:<port>`. Never bind `0.0.0.0`. Never hardcode `8000` or any other port.
- **Visual Identity & Icons:** Source SVG vector icon at `assets/icons/icon.svg` rendered to standard PNG resolutions (`16x16`, `32x32`, `48x48`, `64x64`, `128x128`, `256x256`, `512x512`) via `scripts/gen_icons.sh`.

## Start Here: Required Reading Order
Every incoming agent or contributor must read repository documentation in the following exact sequence before taking any action:
1. `AI_HANDOFF.md` (this file) — Core context, stack boundaries, and operating protocol.
2. `PROJECT_STATE.md` — Real-time operational snapshot of what is completed, active, and pending.
3. `ARCHITECTURE.md` — Complete decision log explaining why technical choices were made.
4. `TASKS.md` — Active development roadmap with atomic checkboxes across all milestones.
5. `KNOWN_ISSUES.md` — Bug catalog, known blockers, investigation findings, and reproductions.
6. `DEV_SETUP.md` — Environment setup, dependency installation, running, testing, and packaging instructions.
7. `CHANGELOG.md` — Historical ledger of sessions, changes, and version bumps.

## Current Milestone Status
- **Current Milestone:** M0 — Handoff File System Complete; Transitioning to M1 — Backend Core & Scaffold.
- **Immediate Objective:** Establish clean project scaffolding (`src/siphon/`, `frontend/`, `scripts/`, `assets/`, `tests/`), configure package definitions (`pyproject.toml`, `requirements.txt`), implement Uvicorn dynamic port allocation, and verify the backend health check with `pytest`.

## Core Agent Operating Rules
1. **Maintain State Continuity:** At the start of every session, read the 7 handoff documents in order. At the end of every session, update `PROJECT_STATE.md`, append to `CHANGELOG.md`, document any blockers in `KNOWN_ISSUES.md`, and record new decisions in `ARCHITECTURE.md`.
2. **Atomic Commits:** Commit after every completed atomic task with clear conventional commit messages (e.g., `feat:`, `fix:`, `test:`, `docs:`, `chore:`).
3. **Test-Driven Discipline:** Every feature or endpoint must have at least one passing `pytest` test before marking the task complete in `TASKS.md`.
4. **Strict Localhost & Dynamic Ports:** Never hardcode a network port. Always bind Uvicorn to `127.0.0.1:0` and retrieve the dynamically assigned port from the server socket before instantiating the UI. Never bind `0.0.0.0`.
5. **Append-Only Architecture Log:** Never edit or delete past architectural decisions in `ARCHITECTURE.md`. Record new technical decisions or superseding choices as new dated entries with context, alternatives considered, and consequences.
