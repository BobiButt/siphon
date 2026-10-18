# Architecture Decision Log — Siphon

This document records the foundational architectural decisions for Siphon. Each entry outlines the technical decision, rationale, alternatives considered, and architectural consequences. This log is append-only.

---

### ADR-001: Project Identity and Naming Conventions
- **Date:** 2026-10-18
- **Decision:** Establish consistent naming and identifiers across all project surfaces:
  - Display Name: `Siphon`
  - Python Package / Module: `siphon`
  - Reverse-DNS Application ID: `io.github.BobiButt.siphon`
  - GitHub Repository: `https://github.com/BobiButt/siphon`
  - AppImage Binary Pattern: `Siphon-<version>-x86_64.AppImage`
  - Desktop Entry File: `io.github.BobiButt.siphon.desktop`
  - Python Class Identifier Base: `Siphon`
- **Why:** Clear, collision-free naming prevents packaging conflicts, aligns with modern Linux desktop conventions (XDG desktop entry specification), and ensures unambiguous package distribution across PyPI, Git tags, and AppImage releases.
- **Alternatives Considered:**
  - Generic names (e.g., `youtube-downloader`, `ytdl-gui`): Rejected due to lack of distinct brand identity and naming collisions in desktop application menus.
  - Non-reverse-DNS application IDs (e.g., `siphon-app`): Rejected because Flatpak, AppStream, and modern desktop environments require reverse-DNS format (`io.github.<user>.<app>`) for DBus and desktop integration.
- **Consequences:** All configurations, documentation, desktop entries, and import statements must adhere strictly to these identifiers without variation.

---

### ADR-002: Desktop Shell Selection — pywebview with WebKitGTK
- **Date:** 2026-10-18
- **Decision:** Use `pywebview` utilizing the host's native WebKitGTK engine as the desktop GUI shell.
- **Why:** `pywebview` creates lightweight native desktop windows wrapping WebKitGTK without bundling an entire Chromium browser runtime. This minimizes memory overhead, reduces final binary size by hundreds of megabytes compared to Electron, and permits building a clean modern HTML/CSS/JS frontend without node/npm build dependencies.
- **Alternatives Considered:**
  - *Electron:* Rejected due to severe memory footprint (easily 150MB+ idle), 100MB+ binary bloat, and dependency on a Node.js runtime alongside Python.
  - *Flet (Flutter for Python):* Rejected because it introduces large Dart/Flutter engine dependencies, custom rendering quirks on Linux, and complex C-extension packaging hurdles in PyInstaller.
  - *PyQt / PySide (Qt6):* Rejected due to large shared library footprint, licensing considerations (GPL/LGPL constraints), and higher styling complexity compared to web standards (HTML/CSS).
- **Consequences:** The target system must have GTK 3 and WebKit2GTK installed at runtime (`gir1.2-webkit2-4.0` / `gir1.2-webkit2-4.1` on Debian/Ubuntu, `webkit2gtk3` / `webkit2gtk4.1` on Fedora, `webkit2gtk` on Arch).

---

### ADR-003: Dynamic Port Allocation with Uvicorn (Port 0 on Localhost)
- **Date:** 2026-10-18
- **Decision:** Bind Uvicorn strictly to `127.0.0.1` on port `0` (ephemeral port allocation), query the operating system for the assigned socket port, and launch `pywebview` pointing to `http://127.0.0.1:<port>`. Never bind `0.0.0.0`. Never hardcode `8000` or any fixed port number.
- **Why:** Hardcoded ports (e.g., 8000 or 5000) lead to immediate application crashes if another local development server or service is already using the port. Binding to port `0` guarantees collision-free port assignment by the OS kernel. Binding strictly to `127.0.0.1` ensures that local services are completely inaccessible to other devices on the local area network.
- **Alternatives Considered:**
  - *Hardcoded port 8000:* Rejected due to frequent port conflicts on developer and user machines.
  - *Port scanning loop (testing 8000, 8001, etc.):* Rejected as racy, inefficient, and susceptible to race conditions between testing and socket binding. Port 0 handles this atomically at the kernel level.
  - *Direct pywebview Python-to-JS bridge API without HTTP:* Considered, but rejected because FastAPI provides structured request validation, clean streaming capabilities for real-time download progress, clear decoupling of frontend and backend logic, and straightforward automated testing via `httpx`/`TestClient`.
- **Consequences:** The application must start the server socket first, extract the assigned port from the server's listening socket (`server.servers[0].sockets[0].getsockname()[1]`), and pass the resulting URL to the pywebview window lifecycle.

---

### ADR-004: Extraction Engine — yt-dlp Python API
- **Date:** 2026-10-18
- **Decision:** Utilize `yt-dlp` directly via its Python module API (`yt_dlp.YoutubeDL`) rather than spawning external CLI subprocesses.
- **Why:** `yt-dlp` is the active, industry-standard fork of youtube-dl with rapid updates against YouTube extractor breakage, support for DASH manifests, cipher solving, and thorough metadata extraction. Using the direct Python API provides fine-grained control over progress hooks, format dictionaries, error exceptions, and avoids fragile shell quoting and subprocess overhead.
- **Alternatives Considered:**
  - *Custom HTTP scraper / parser:* Rejected because YouTube frequently rotates player scripts, cipher algorithms, and signature mechanisms. Maintaining a bespoke scraper would require unsustainable maintenance.
  - *`pytube`:* Rejected due to frequent unmaintained periods, lack of robust DASH stream parsing, and recurrent breakage on newer YouTube player variations.
  - *Calling `yt-dlp` via `subprocess.Popen`:* Rejected because parsing stdout/stderr text for progress and format information is error-prone compared to Python callbacks and dictionaries.
- **Consequences:** `yt-dlp` is bundled directly in the application's Python environment and PyInstaller package. Updates to `yt-dlp` can be managed as regular Python dependency updates.

---

### ADR-005: Packaging Pipeline — PyInstaller, AppDir, and appimagetool
- **Date:** 2026-10-18
- **Decision:** Package the desktop application into a standalone Linux AppImage by first freezing Python code and dependencies into a single directory using PyInstaller, assembling an AppDir with desktop metadata and icon assets, and producing an AppImage using `appimagetool`.
- **Why:** AppImages are single-file executable bundles that run across virtually all modern Linux distributions without requiring root privileges or package managers. Unlike Snap or Flatpak, AppImages require zero sandbox daemon overhead and offer seamless portable distribution on GitHub Releases.
- **Alternatives Considered:**
  - *Flatpak:* Excellent for sandboxing, but requires users to install runtime runtimes and complicates distribution via simple standalone binary releases.
  - *Deb/RPM packages:* Requires maintaining multiple packaging formats and dealing with distro-specific dependency name differences.
  - *Standalone PyInstaller single-file binary (`--onefile`):* PyInstaller `--onefile` unpacks to `/tmp` on every execution, increasing startup latency and lacking standardized desktop file, icon, and MIME integration. AppImage provides standard desktop integration and fast mounting.
- **Consequences:** Builds must be carefully orchestrated to respect glibc version baselines and system library bundling boundaries.

---

### ADR-006: Pinned Static BtbN FFmpeg Fetched via Script
- **Date:** 2026-10-18
- **Decision:** Download a pinned BtbN static Linux x86_64 build of FFmpeg from GitHub releases (`https://github.com/BtbN/FFmpeg-Builds/releases`) via `scripts/fetch_ffmpeg.sh`, unpack it to `assets/ffmpeg/ffmpeg`, set executable permissions (`chmod 0755`), and ignore the binary in Git (`.gitignore`).
- **Why:** FFmpeg is required for muxing high-resolution DASH video streams (1080p, 1440p, 4K) with audio streams. Pinning a specific static GPL build ensures 100% deterministic, reproducible builds and identical muxing behavior across developer workstations and CI runners. Fetching on demand keeps the Git repository small and clean.
- **Alternatives Considered:**
  - *Committing the FFmpeg binary to Git:* Rejected because checking 80MB+ binaries into Git history causes permanent repository bloat.
  - *Downloading the unpinned "latest" release at build time:* Rejected because non-deterministic builds break reproducibility and can cause sudden regressions when upstream releases change.
  - *Relying on the host system's `ffmpeg`:* Rejected because many minimal host systems do not have FFmpeg installed, or have outdated/crippled versions missing required codecs.
- **Consequences:** Internet access is required during initial developer setup (`./scripts/fetch_ffmpeg.sh`) and CI builds. Upgrading FFmpeg requires an explicit version tag bump in `scripts/fetch_ffmpeg.sh`.

---

### ADR-007: Containerized AppImage Build Environment (Ubuntu 22.04 LTS)
- **Date:** 2026-10-18
- **Decision:** Build the release AppImage inside an `ubuntu:22.04` Docker container via `scripts/build_in_docker.sh`.
- **Why:** On Linux, binaries compiled against a given GNU C Library (`glibc`) cannot run on systems with an older `glibc`. Building on Ubuntu 22.04 LTS sets the minimum glibc requirement to version 2.35, which is supported by all modern Linux distributions (Debian 12+, Ubuntu 22.04+, Fedora 36+, Arch Linux). Building inside a container guarantees identical build outputs regardless of the developer's host distribution.
- **Alternatives Considered:**
  - *Building directly on the host machine:* Rejected because developers on rolling release distributions (e.g., Arch, Fedora Rawhide with glibc 2.39+) would generate AppImages that fail to run on LTS distributions like Ubuntu or Debian.
  - *Building on Ubuntu 20.04 (glibc 2.31):* Rejected because Python 3.11+ and modern WebKitGTK packaging tooling on Ubuntu 20.04 require backports and obsolete toolchains with diminishing practical benefits given Ubuntu 20.04's lifecycle.
- **Consequences:** Docker (or Podman) is required on build machines and GitHub Actions CI runners to generate release AppImages.

---

### ADR-008: Static Type 2 AppImage Runtime (libfuse2 Independence)
- **Date:** 2026-10-18
- **Decision:** Configure `appimagetool` to embed the static Type 2 AppImage runtime (`https://github.com/AppImage/type2-runtime`) instead of the traditional default runtime.
- **Why:** Traditional AppImage runtimes depend on `libfuse2` to mount the squashfs filesystem. Modern Linux distributions—notably Fedora 40+, Fedora Atomic Desktops (Silverblue, Kinoite 44+), and Ubuntu 24.04+—no longer install `libfuse2` by default, shipping only `fuse3`. The static Type 2 runtime does not require host `libfuse2`, allowing Siphon to run out of the box without requiring manual user installation of legacy system libraries.
- **Alternatives Considered:**
  - *Default AppImage runtime:* Rejected because users on modern Fedora and Ubuntu systems encounter `dlopen(): error loading libfuse.so.2` and cannot run the application without installing deprecated packages.
  - *Prompting users to install `libfuse2`:* Rejected as poor user experience for an open-source desktop application aimed at ease of use.
- **Consequences:** The build script must fetch the prebuilt static Type 2 runtime binary and pass it to `appimagetool` via the `--runtime-file` flag. The resulting AppImage size is marginally larger (~1-2MB), which is negligible.

---

### ADR-009: CI/CD via GitHub Actions with Containerized Builds and Tag-Triggered Releases
- **Date:** 2026-10-18
- **Decision:** Use GitHub Actions for continuous integration and release automation, with three workflows:
  - `test.yml`: run `pytest` across a Python 3.11 and 3.12 matrix on pushes and pull requests to `main`.
  - `build.yml`: execute the existing `scripts/build_in_docker.sh` (reusing the ADR-007 containerized pipeline) on pushes/PRs and manual dispatch, smoke-test the produced AppImage via `--version`, and upload it as a workflow artifact.
  - `release.yml`: on `v*` tag pushes, run the containerized build, smoke-test, generate a `SHA256SUMS.txt` via `sha256sum`, and publish the AppImage plus checksum to a GitHub Release using `softprops/action-gh-release@v2` with `permissions: contents: write`.
- **Why:** GitHub Actions is native to the hosting platform (no external CI credentials), provides Linux runners with Docker preinstalled (satisfying the ADR-007 container requirement), and supports matrix testing and tag-triggered release publishing out of the box. Reusing `build_in_docker.sh` in CI guarantees the exact same glibc-2.35 build environment used locally, keeping artifacts reproducible and identical between developer machines and release binaries. The `--version` smoke test (handled by `argparse` before any server/GUI initialization) validates the binary headlessly.
- **Alternatives Considered:**
  - *GitLab CI / CircleCI / Travis:* Rejected because they require external service credentials and do not match the GitHub hosting target.
  - *Building directly on the hosted runner (no container):* Rejected because runner glibc versions change over time and would violate the ADR-007 glibc-2.35 reproducibility guarantee.
  - *Writing a custom release script with the GitHub REST API:* Rejected in favor of the well-maintained `softprops/action-gh-release` action, which handles asset upload and release notes generation.
- **Consequences:** Workflow definitions live in `.github/workflows/` and are validated by `tests/test_ci.py` (structure, Python matrix, containerized build invocation, tag trigger, and release-asset wiring). Docker is required on CI runners. Release artifacts are only produced from `v*` tags, decoupling "merge" from "release." A known open issue (ISSUE-002) remains: the `ubuntu:22.04` build container's system Python is 3.10 versus the project's `requires-python >= 3.11` requirement, which must be reconciled before the first tagged release.
