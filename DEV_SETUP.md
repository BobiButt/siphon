# Developer Setup & Build Guide — Siphon

This guide provides instructions for setting up a local development environment, installing host dependencies, running tests, executing the application, and building the standalone AppImage.

---

## 1. System Requirements & Runtime Dependencies

- **Architecture:** `x86_64` Linux
- **C Library:** GNU C Library (`glibc`) version 2.35 or newer (Ubuntu 22.04 LTS baseline).
- **Python Version:** Python 3.11+
- **Runtime Dependencies:** While the Siphon AppImage bundles Python and static FFmpeg, the host system must have GTK 3 and WebKit2GTK installed for `pywebview` native desktop rendering (standard for any WebKitGTK desktop shell).
- **Unsupported Systems:** Alpine Linux and other musl-libc based distributions are explicitly unsupported.

### Install Host System Dependencies

#### Ubuntu / Debian (Debian 12+, Ubuntu 22.04+)
```bash
sudo apt update
sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0 \
    python3 python3-pip python3-venv git curl xz-utils
```

#### Fedora (Fedora 38+, Silverblue/Kinoite)
```bash
sudo dnf install -y python3-gobject gtk3 webkit2gtk3 \
    python3 python3-pip git curl xz
```

#### Arch Linux / Manjaro
```bash
sudo pacman -S --needed python-gobject gtk3 webkit2gtk \
    python python-pip git curl xz
```

---

## 2. Python Virtual Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/BobiButt/siphon.git
   cd siphon
   ```

2. **Create and activate the virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt -r requirements-dev.txt
   pip install -e .
   ```

---

## 3. Bundled FFmpeg Setup

Siphon relies on a pinned static build of FFmpeg from BtbN for stream muxing. The binary is excluded from git (`assets/ffmpeg/ffmpeg` is in `.gitignore`) and must be downloaded once after cloning:

```bash
chmod +x scripts/fetch_ffmpeg.sh
./scripts/fetch_ffmpeg.sh
```

This script:
1. Downloads the pinned BtbN Linux x86_64 GPL static archive from GitHub Releases.
2. Unpacks the archive and places the standalone binary at `assets/ffmpeg/ffmpeg`.
3. Sets executable permissions (`chmod 0755 assets/ffmpeg/ffmpeg`).
4. Verifies the binary runs successfully.

---

## 4. Running Siphon Locally

To run the application in desktop window mode:
```bash
python -m siphon
```

To run in headless backend mode (useful for testing or API development without opening the WebKitGTK window):
```bash
python -m siphon --headless
```

*Note on dynamic ports:* When launched, Siphon dynamically binds Uvicorn to `127.0.0.1:0`. The OS automatically assigns an available port, which Siphon displays in the terminal and attaches to `pywebview`. It never binds to `0.0.0.0` and never hardcodes port `8000`.

---

## 5. Running the Test Suite

Run the full automated test suite with pytest:
```bash
pytest
```

Run tests with verbose output and coverage report:
```bash
pytest -v --cov=src/siphon tests/
```

---

## 5.1 Fixing the "Sign in to confirm you're not a bot" error

YouTube may block automated extraction with an error such as **"Sign in to confirm you're not a bot."** Siphon supports sending your own YouTube session cookies to yt-dlp to bypass this check.

Setup:

1. Install a cookie-export browser extension, e.g. **"Get cookies.txt LOCALLY"** (Chrome/Firefox).
2. Log in to YouTube in that browser.
3. Export the cookies for `youtube.com` in Netscape `cookies.txt` format.
4. Place the exported file at:
   ```bash
   mkdir -p ~/.config/siphon
   mv ~/Downloads/cookies.txt ~/.config/siphon/cookies.txt
   ```
5. Restart the app.

**How it works in code:** `src/siphon/extractors/ytdlp_extractor.py` exposes `get_cookies_path()` (resolves to `~/.config/siphon/cookies.txt`) and `_build_ydl_opts()`, which adds yt-dlp's `cookiefile` option only when the file exists. If the file is absent, yt-dlp runs without cookies. When yt-dlp reports the bot-check error, Siphon raises a clear `ExtractionError` pointing the user to this file.

> ⚠️ The cookies file is sensitive (it carries your login session). Keep it out of version control and never share it.

---

## 6. Building the AppImage

### Reference Build (Recommended: Inside Docker)
To guarantee glibc 2.35 compatibility and reproducible output across any host distribution, the official build is executed inside an `ubuntu:22.04` Docker container:

```bash
chmod +x scripts/build_in_docker.sh
./scripts/build_in_docker.sh
```

### Host Build (Alternative: On Ubuntu 22.04 Host)
If building directly on an Ubuntu 22.04 machine with Docker unavailable:
```bash
chmod +x scripts/build_appimage.sh
./scripts/build_appimage.sh
```

### Static Type 2 Runtime Note
The build pipeline automatically fetches and embeds the static Type 2 AppImage runtime (`https://github.com/AppImage/type2-runtime`). This ensures that the generated AppImage **does not require `libfuse2`** on the user's host machine, making it fully compatible with Fedora Atomic Desktops (Silverblue/Kinoite 44+) and Ubuntu 24.04+.

### Build Artifact Output
All generated AppImage bundles land in the `dist/` directory:
```
dist/Siphon-<version>-x86_64.AppImage
```
Verify the artifact:
```bash
chmod +x dist/Siphon-*.AppImage
./dist/Siphon-*.AppImage --version
```
