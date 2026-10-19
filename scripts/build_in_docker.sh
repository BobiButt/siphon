#!/usr/bin/env bash
# scripts/build_in_docker.sh — Build Siphon AppImage inside ubuntu:22.04 container
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DOCKER_CMD="docker"
if ! command -v docker &>/dev/null && command -v podman &>/dev/null; then
    DOCKER_CMD="podman"
fi

if ! command -v "${DOCKER_CMD}" &>/dev/null; then
    echo "Error: Neither docker nor podman was found on the host system." >&2
    exit 1
fi

echo "==> Building Siphon AppImage inside ubuntu:22.04 container using ${DOCKER_CMD}..."

${DOCKER_CMD} run --rm \
    --device /dev/fuse \
    --cap-add SYS_ADMIN \
    --security-opt apparmor:unconfined \
    -e HOST_UID="$(id -u)" \
    -e HOST_GID="$(id -g)" \
    -v "${REPO_ROOT}:/workspace" \
    -w /workspace \
    ubuntu:22.04 \
    bash -c '
        set -euo pipefail
        export DEBIAN_FRONTEND=noninteractive
        echo "==> Installing container build dependencies..."
        apt-get update -y
        apt-get install -y --no-install-recommends \
            python3 \
            python3-pip \
            python3-venv \
            libpython3.10 \
            git \
            curl \
            file \
            xz-utils \
            imagemagick \
            libglib2.0-0 \
            ca-certificates \
            binutils \
            libgl1 \
            libegl1 \
            libxkbcommon-x11-0 \
            libdbus-1-3 \
            libxcb-xinerama0

        echo "==> Downloading required binaries..."
        mkdir -p assets/bin assets/ffmpeg
        ./scripts/fetch_ffmpeg.sh
        curl -L -o assets/bin/bgutil-pot https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs/releases/latest/download/bgutil-pot-linux-x86_64
        chmod +x assets/bin/bgutil-pot

        echo "==> Setting up virtual environment..."
        python3 -m venv /tmp/build_venv
        source /tmp/build_venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt pyinstaller

        echo "==> Executing AppImage build pipeline..."
        ./scripts/build_appimage.sh

        echo "==> Fixing file permissions for GitHub Actions runner..."
        chown -R "${HOST_UID}:${HOST_GID}" dist/ || true
        chown -R "${HOST_UID}:${HOST_GID}" build/ || true
        chown -R "${HOST_UID}:${HOST_GID}" assets/bin/ || true
        chown -R "${HOST_UID}:${HOST_GID}" assets/ffmpeg/ || true
    '

echo "==> Containerized AppImage build completed successfully."