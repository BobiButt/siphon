# Siphon

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Linux x86_64](https://img.shields.io/badge/Platform-Linux%20x86__64-orange.svg)]()

**Siphon** is a native Linux desktop **YouTube clone** inspired by NewPipe — search, browse, stream, and download YouTube videos from a clean, fast desktop app. It extracts stream metadata with `yt-dlp`, plays progressive streams directly in an embedded HTML5 video player, and downloads any format including DASH high-resolution video (1080p, 1440p, 4K) with automatic muxing.

Distributed as a standalone `x86_64` AppImage with seamless desktop integration.

---

## Features

- **Search & Browse:** Type a query and press Enter. Results render in a responsive grid with thumbnails, titles, dates, and durations.
- **In-App Streaming:** Watch videos directly in the built-in player. Supports an automatic quality dropdown (360p/480p/720p MP4) to ensure smooth playback across all Linux systems.
- **Format Inspection:** Click any result (or paste a URL) to inspect all available formats — progressive, DASH video-only, and audio-only — in neatly scrollable lists.
- **DASH & High-Resolution Downloads:** Download adaptive video streams up to 4K (2160p) with automatic muxing using the bundled static FFmpeg.
- **Built-in Bot Protection:** Automatically bypasses YouTube's "Sign in to confirm you're not a bot" error using a bundled Proof-of-Origin (POT) token provider and automatic browser cookie extraction.
- **Native Desktop Shell:** Built on `pywebview` and `PyQt5` for a lightweight, native window with custom application icons and blurred loading overlays.
- **Standalone AppImage:** Built inside Ubuntu 22.04 LTS containers with a static Type 2 runtime, eliminating host `libfuse2` requirements.

---

## API Overview

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/search?q=<query>&limit=<n>` | GET | Search YouTube (full metadata) → list of videos. |
| `/api/info?url=<url>` | GET | Full metadata + categorized formats. |
| `/api/stream?url=<url>` | GET | Resolve a directly-playable progressive (muxed) stream URL. |
| `/api/proxy?url=<url>` | GET | Proxy video bytes with correct headers to bypass CORS/Qt restrictions. |
| `/api/download` | POST | Download a chosen format; mux DASH streams via bundled FFmpeg. |
| `/health` | GET | Backend health check. |

---

## How Authentication Works

Siphon handles YouTube's bot checks automatically. When you launch the app:

1. It starts a background **Rust-based POT (Proof-of-Origin) provider**.
2. It attempts to extract cookies directly from your installed browser (Firefox, Chrome, Chromium).
3. These tokens and cookies are passed to `yt-dlp` to guarantee high-resolution extraction.

> **Note:** Make sure you are logged into YouTube in your browser for the most reliable experience. If you use a sandboxed browser (such as a Flatpak install), you may need to manually export a `cookies.txt` file to `~/.config/siphon/cookies.txt`.

---

## Runtime Dependencies

While the Siphon AppImage bundles Python, FFmpeg, and the POT provider, the host system must have `PyQt5` and its underlying libraries to render the window.

- **Fedora / RHEL / CentOS:**
  ```bash
  sudo dnf install qt5-qtwebengine qt5-qtbase
  ```

- **Ubuntu / Debian / Linux Mint:**
  ```bash
  sudo apt install libqt5webengine5 libqt5webenginewidgets5
  ```

- **Arch Linux / Manjaro:**
  ```bash
  sudo pacman -S qt5-webengine qt5-base
  ```

> **Note:** Siphon targets `x86_64` Linux distributions with glibc >= 2.35 (Ubuntu 22.04 LTS baseline). Alpine Linux and other musl-libc based systems are not supported.

---

## AppImage Execution

Download the latest release `Siphon-<version>-x86_64.AppImage` from [Releases](https://github.com/BobiButt/siphon/releases):

```bash
chmod +x Siphon-*-x86_64.AppImage
./Siphon-*-x86_64.AppImage
```

---

## Developer Setup & Contributing

For instructions on building from source, running the test suite, fetching the bundled FFmpeg, or compiling the AppImage in Docker, see [DEV_SETUP.md](DEV_SETUP.md).

Architecture decisions and project continuity guidelines are documented in:

- [AI_HANDOFF.md](AI_HANDOFF.md)
- [PROJECT_STATE.md](PROJECT_STATE.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [TASKS.md](TASKS.md)
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.