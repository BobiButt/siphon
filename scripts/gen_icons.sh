#!/usr/bin/env bash
# scripts/gen_icons.sh — Generate the standard PNG icon size set for Siphon.
#
# Source of truth is assets/icons/icon.png (a manually authored raster icon).
# Because the source may be non-square, each output is centre-fitted into a
# transparent square canvas so nothing is stretched or distorted.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_DIR="${REPO_ROOT}/assets/icons"
ICON_PNG="${OUTPUT_DIR}/icon.png"

# Standard hicolor icon sizes produced for the .desktop entry / AppImage.
SIZES=(16 32 48 64 128 256 512)

if [[ ! -f "${ICON_PNG}" ]]; then
    echo "Error: Source icon not found at ${ICON_PNG}" >&2
    exit 1
fi

# Pick an available ImageMagick converter.
MAGICK_CMD=()
if command -v magick &>/dev/null; then
    MAGICK_CMD=(magick)
elif command -v convert &>/dev/null; then
    MAGICK_CMD=(convert)
else
    echo "Error: No ImageMagick converter found (need 'magick' or 'convert')." >&2
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

echo "==> Scaling ${ICON_PNG} into ${#SIZES[@]} sizes (square, distortion-free)..."

# Render icon.png at a given square size, centre-fitted on a transparent canvas.
render_size() {
    local size="$1"
    local out="$2"
    "${MAGICK_CMD[@]}" "${ICON_PNG}" \
        -resize "${size}x${size}" \
        -background none \
        -gravity center \
        -extent "${size}x${size}" \
        "${out}"
}

for size in "${SIZES[@]}"; do
    # The canonical icon.png stays at 256x256; other sizes get suffixed names.
    if [[ "${size}" == "256" ]]; then
        # Write to a temp file first, then swap, so we never truncate the source.
        tmp="${OUTPUT_DIR}/.icon_256.tmp.png"
        render_size "${size}" "${tmp}"
        mv -f "${tmp}" "${ICON_PNG}"
    else
        render_size "${size}" "${OUTPUT_DIR}/icon_${size}.png"
    fi
    echo "    - icon_${size}.png"
done

echo "==> Done. Canonical icon: ${ICON_PNG} (256x256, square-padded)."
