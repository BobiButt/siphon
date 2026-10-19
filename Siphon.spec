# -*- mode: python ; coding: utf-8 -*-
# Siphon.spec — PyInstaller build specification for Siphon (ONEDIR mode)

from pathlib import Path

block_cipher = None
spec_root = Path.cwd()

datas = [
    (str(spec_root / "frontend"), "frontend"),
    (str(spec_root / "assets" / "icons"), "assets/icons"),
]

if (spec_root / "assets" / "bin").exists():
    datas.append((str(spec_root / "assets" / "bin"), "assets/bin"))
if (spec_root / "assets" / "ffmpeg").exists():
    datas.append((str(spec_root / "assets" / "ffmpeg"), "assets/ffmpeg"))

hidden_imports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "starlette",
    "pydantic",
    "pydantic_core",
    "yt_dlp",
    "webview",
    "webview.platforms.qt",
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "PyQt5.QtWebEngineWidgets",
    "PyQt5.QtWebEngineCore",
    "qtpy",
]

a = Analysis(
    ["src/siphon/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="siphon",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="siphon",
)