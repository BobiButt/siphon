# -*- mode: python ; coding: utf-8 -*-

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
    "uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto",
    "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan", "uvicorn.lifespan.on",
    "fastapi", "starlette", "pydantic", "pydantic_core",
    "webview", "webview.platforms.qt",
    "PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets", 
    "PyQt5.QtWebEngineWidgets", "PyQt5.QtWebEngineCore",
    "httpx", "httpcore", "anyio", "h11", "sniffio", "certifi",
    
    # CRITICAL FIX: Bundle yt-dlp, its YouTube extractor, the POT plugin, and EJS
    "yt_dlp",
    "yt_dlp.extractor",
    "yt_dlp.extractor.youtube",
    "yt_dlp.plugins",
    "yt_dlp_plugins",
    "yt_dlp_plugins.extractor",
    "yt_dlp_plugins.extractor.getpot_bgutil_http",
    "bgutil_ytdlp_pot_provider",
    "yt_dlp_ejs",
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
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="siphon",
    debug=False, strip=False, upx=True,
    console=False, 
    disable_windowed_traceback=False, argv_emulation=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True, upx_exclude=[], name="siphon",
)