# Developer Setup & Build Guide — Siphon

This guide provides instructions for setting up a local development environment, installing host dependencies, running tests, executing the application, and building the standalone AppImage.

---

## 1. System Requirements & Compatibility

- **Architecture:** `x86_64` Linux
- **C Library:** GNU C Library (`glibc`) version 2.35 or newer (Ubuntu 22.04 LTS baseline).
- **Python Version:** Python 3.11+
- **Desktop Runtime Dependencies:** GTK 3 and WebKit2GTK are required for `pywebview` native desktop rendering.
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
