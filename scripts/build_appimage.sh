#!/usr/bin/env bash
# scripts/build_appimage.sh — Assemble AppDir and build Siphon AppImage
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Resolve Python environment
PYTHON_BIN="python3"
if [[ -f "${REPO_ROOT}/.venv/bin/python3" ]]; then
    PYTHON_BIN="${REPO_ROOT}/.venv/bin/python3"
fi

VERSION="$("${PYTHON_BIN}" -c "import sys; sys.path.insert(0, '${REPO_ROOT}/src'); import siphon; print(siphon.__version__)")"
echo "==> Building Siphon v${VERSION} AppImage..."

# a. Run PyInstaller using spec file
echo "==> Running PyInstaller..."
if [[ -n "${PYINSTALLER_CMD:-}" ]]; then
    PYINSTALLER_BIN="${PYINSTALLER_CMD}"
elif [[ -f "${REPO_ROOT}/.venv/bin/pyinstaller" ]]; then
    PYINSTALLER_BIN="${REPO_ROOT}/.venv/bin/pyinstaller"
elif command -v pyinstaller &>/dev/null; then
    PYINSTALLER_BIN="pyinstaller"
else
    "${PYTHON_BIN}" -m pip install pyinstaller
    PYINSTALLER_BIN="${PYTHON_BIN} -m PyInstaller"
fi

${PYINSTALLER_BIN} --noconfirm --clean "${REPO_ROOT}/Siphon.spec"
# Delete the crashing GLX plugin for Fedora/Wayland compatibility
echo "==> Patching PyInstaller output for GLX compatibility..."
find dist/siphon -name "libqxcb-glx-integration.so" -delete || true

PYINSTALLER_OUT="${REPO_ROOT}/dist/siphon"
if [[ ! -d "${PYINSTALLER_OUT}" ]]; then
    echo "Error: PyInstaller onedir output directory not found at ${PYINSTALLER_OUT}" >&2
    exit 1
fi

# b. Create standard AppDir structure
APPDIR="${REPO_ROOT}/AppDir"
echo "==> Creating AppDir at ${APPDIR}..."
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${APPDIR}/assets/ffmpeg"

# c. Copy PyInstaller onedir output into AppDir/usr/bin/
echo "==> Copying PyInstaller bundle into AppDir/usr/bin/..."
cp -r "${PYINSTALLER_OUT}"/* "${APPDIR}/usr/bin/"

# d. Ensure and copy static FFmpeg binary
if [[ ! -f "${REPO_ROOT}/assets/ffmpeg/ffmpeg" ]]; then
    echo "==> Fetching static FFmpeg binary..."
    "${REPO_ROOT}/scripts/fetch_ffmpeg.sh" || true
fi

if [[ -f "${REPO_ROOT}/assets/ffmpeg/ffmpeg" ]]; then
    cp "${REPO_ROOT}/assets/ffmpeg/ffmpeg" "${APPDIR}/usr/bin/ffmpeg"
    cp "${REPO_ROOT}/assets/ffmpeg/ffmpeg" "${APPDIR}/assets/ffmpeg/ffmpeg"
    chmod 0755 "${APPDIR}/usr/bin/ffmpeg" "${APPDIR}/assets/ffmpeg/ffmpeg"
fi

# e. Copy icon to AppDir icon path
if [[ ! -f "${REPO_ROOT}/assets/icons/icon.png" ]]; then
    "${REPO_ROOT}/scripts/gen_icons.sh"
fi
cp "${REPO_ROOT}/assets/icons/icon.png" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/siphon.png"

# f. Create .desktop file
DESKTOP_FILE="${APPDIR}/usr/share/applications/siphon.desktop"
echo "==> Generating .desktop file at ${DESKTOP_FILE}..."
cat > "${DESKTOP_FILE}" << 'EOF'
[Desktop Entry]
Name=Siphon
Exec=siphon
Icon=siphon
Type=Application
Categories=AudioVideo;Video;
EOF
chmod 0644 "${DESKTOP_FILE}"

# g. Create required top-level symlinks and AppRun
echo "==> Configuring top-level symlinks and AppRun..."
ln -sf "usr/share/applications/siphon.desktop" "${APPDIR}/siphon.desktop"
ln -sf "usr/share/icons/hicolor/256x256/apps/siphon.png" "${APPDIR}/siphon.png"
ln -sf "siphon.png" "${APPDIR}/.DirIcon"

cat > "${APPDIR}/AppRun" << 'EOF'
#!/usr/bin/env bash
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="${SELF_DIR}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${SELF_DIR}/usr/lib:${SELF_DIR}/usr/bin:${LD_LIBRARY_PATH:-}"
exec "${SELF_DIR}/usr/bin/siphon" "$@"
EOF
chmod 0755 "${APPDIR}/AppRun"

# h. Fetch static Type 2 runtime and build AppImage with appimagetool
DIST_DIR="${REPO_ROOT}/dist"
mkdir -p "${DIST_DIR}"
OUTPUT_APPIMAGE="${DIST_DIR}/Siphon-${VERSION}-x86_64.AppImage"
CACHE_DIR="${REPO_ROOT}/.cache"
mkdir -p "${CACHE_DIR}"

STATIC_RUNTIME="${CACHE_DIR}/type2-runtime-x86_64"
if [[ ! -f "${STATIC_RUNTIME}" ]]; then
    echo "==> Downloading static Type 2 AppImage runtime..."
    curl -fsSL --retry 3 \
        "https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64" \
        -o "${STATIC_RUNTIME}"
    chmod 0755 "${STATIC_RUNTIME}"
fi

APPIMAGETOOL_BIN="appimagetool"
if ! command -v "${APPIMAGETOOL_BIN}" &>/dev/null; then
    APPIMAGETOOL_PATH="${CACHE_DIR}/appimagetool-x86_64.AppImage"
    if [[ ! -f "${APPIMAGETOOL_PATH}" ]]; then
        echo "==> Downloading appimagetool..."
        curl -fsSL --retry 3 \
            "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
            -o "${APPIMAGETOOL_PATH}"
        chmod 0755 "${APPIMAGETOOL_PATH}"
    fi
    APPIMAGETOOL_BIN="${APPIMAGETOOL_PATH}"
fi

echo "==> Running appimagetool with static Type 2 runtime..."
# Use appimagetool with extracted runtime if host doesn't have fuse
export ARCH=x86_64
"${APPIMAGETOOL_BIN}" --runtime-file "${STATIC_RUNTIME}" "${APPDIR}" "${OUTPUT_APPIMAGE}"

echo "==> AppImage build completed: ${OUTPUT_APPIMAGE}"
ls -lh "${OUTPUT_APPIMAGE}"
