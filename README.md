# Siphon

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux x86_64](https://img.shields.io/badge/Platform-Linux%20x86__64-orange.svg)]()

**Siphon** (`io.github.BobiButt.siphon`) is a native Linux desktop application inspired by NewPipe, designed for inspecting YouTube media streams and downloading video or audio at full quality, including DASH high-resolution video streams (1080p, 1440p, 4K) and separate audio streams.

Distributed as a standalone, zero-dependency `x86_64` AppImage with seamless desktop integration.

---

## Features Planned

- **Stream Extraction & Format Inspection:** Paste any YouTube video URL to inspect available formats, codecs, resolutions, and audio tracks.
- **DASH & High-Resolution Downloads:** Download adaptive video streams up to 4K (2160p) with automatic stream muxing using bundled static FFmpeg.
- **Audio-Only Extraction:** Download audio streams directly (e.g., Opus, AAC/M4A) with metadata preservation.
- **Native Lightweight Desktop Shell:** Minimal resource consumption using `pywebview` with native WebKitGTK rendering—no heavy Chromium/Electron overhead.
- **Secure Dynamic Networking:** Built on FastAPI and Uvicorn dynamically bound to ephemeral localhost sockets (`127.0.0.1:0`), preventing port collisions and network exposure.
- **Standalone AppImage:** Built inside Ubuntu 22.04 LTS containers with static Type 2 runtime, eliminating host `libfuse2` requirements and running cleanly across modern Linux desktops.

---

## Runtime Dependencies

While the Siphon AppImage bundles Python, all application code, and a static build of FFmpeg, the user's host system must have **GTK 3 and WebKit2GTK** installed to render the native desktop GUI (this is standard for any `pywebview` application):

- **Fedora / RHEL / CentOS (including Silverblue / Kinoite):**
  ```bash
  sudo dnf install python3-gobject gtk3 webkit2gtk3
  ```

- **Ubuntu / Debian / Linux Mint:**
  ```bash
  sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0
  ```

- **Arch Linux / Manjaro:**
  ```bash
  sudo pacman -S python-gobject gtk3 webkit2gtk
  ```

*Note: Siphon targets `x86_64` Linux distributions with glibc >= 2.35 (Ubuntu 22.04 LTS baseline). Alpine Linux and other musl-libc based systems are not supported.*

---

## AppImage Execution

Download the latest release pattern `Siphon-<version>-x86_64.AppImage` from [Releases](https://github.com/BobiButt/siphon/releases):

```bash
chmod +x Siphon-*-x86_64.AppImage
./Siphon-*-x86_64.AppImage
```

---

## Developer Setup & Contributing

For instructions on building from source, running the test suite, fetching bundled FFmpeg, or compiling the AppImage in Docker, please refer to [DEV_SETUP.md](DEV_SETUP.md).

Architecture decisions and project continuity guidelines are documented in:
- [AI_HANDOFF.md](AI_HANDOFF.md)
- [PROJECT_STATE.md](PROJECT_STATE.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [TASKS.md](TASKS.md)
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
