#!/usr/bin/env bash
# scripts/fetch_ffmpeg.sh — Download pinned BtbN static Linux x86_64 FFmpeg binary
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${REPO_ROOT}/assets/ffmpeg"
TARGET_BIN="${TARGET_DIR}/ffmpeg"

# Pinned BtbN FFmpeg Release (Linux x86_64 GPL Static)
FFMPEG_TAG="latest"
FFMPEG_ARCHIVE="ffmpeg-n7.1-latest-linux64-gpl-7.1.tar.xz"
FFMPEG_URL="https://github.com/BtbN/FFmpeg-Builds/releases/download/${FFMPEG_TAG}/${FFMPEG_ARCHIVE}"

if [[ -f "${TARGET_BIN}" && -x "${TARGET_BIN}" ]]; then
    echo "==> Static FFmpeg binary already exists at ${TARGET_BIN}"
    "${TARGET_BIN}" -version | head -n 1
    exit 0
fi

mkdir -p "${TARGET_DIR}"
TMP_DIR="$(mktemp -d -t siphon_ffmpeg_XXXXXX)"
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "==> Downloading pinned static FFmpeg from ${FFMPEG_URL}..."
curl -fsSL --retry 3 "${FFMPEG_URL}" -o "${TMP_DIR}/${FFMPEG_ARCHIVE}"

echo "==> Extracting ffmpeg binary..."
tar -xJf "${TMP_DIR}/${FFMPEG_ARCHIVE}" -C "${TMP_DIR}"

EXTRACTED_BIN="$(find "${TMP_DIR}" -type f -name "ffmpeg" -perm -u+x | head -n 1)"
if [[ -z "${EXTRACTED_BIN}" ]]; then
    echo "Error: ffmpeg binary not found inside extracted archive" >&2
    exit 1
fi

mv "${EXTRACTED_BIN}" "${TARGET_BIN}"
chmod 0755 "${TARGET_BIN}"

echo "==> Successfully installed static FFmpeg to ${TARGET_BIN}"
"${TARGET_BIN}" -version | head -n 1
