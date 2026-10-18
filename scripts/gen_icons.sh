#!/usr/bin/env bash
# scripts/gen_icons.sh — Generate PNG icons from assets/icons/icon.svg
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ICON_SRC="${REPO_ROOT}/assets/icons/icon.svg"
OUTPUT_DIR="${REPO_ROOT}/assets/icons"

if [[ ! -f "${ICON_SRC}" ]]; then
    echo "Error: Source icon not found at ${ICON_SRC}" >&2
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

echo "==> Generating icons from ${ICON_SRC}..."

# Generate primary 256x256 icon.png
if command -v magick &>/dev/null; then
    magick -background none "${ICON_SRC}" -resize 256x256 "${OUTPUT_DIR}/icon.png"
elif command -v convert &>/dev/null; then
    convert -background none "${ICON_SRC}" -resize 256x256 "${OUTPUT_DIR}/icon.png"
elif command -v inkscape &>/dev/null; then
    inkscape "${ICON_SRC}" -w 256 -h 256 -o "${OUTPUT_DIR}/icon.png"
elif command -v rsvg-convert &>/dev/null; then
    rsvg-convert -w 256 -h 256 "${ICON_SRC}" -o "${OUTPUT_DIR}/icon.png"
else
    echo "Error: No suitable icon converter found (magick, convert, inkscape, rsvg-convert)." >&2
    exit 1
fi

echo "==> Successfully generated ${OUTPUT_DIR}/icon.png (256x256)"
