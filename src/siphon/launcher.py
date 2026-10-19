"""pywebview desktop shell launcher for Siphon."""

import os
import subprocess
import time
import sys
from pathlib import Path
import shutil
import webview
from siphon.server import SiphonServer

# --- FORCE SOFTWARE RENDERING & DISABLE GPU ---
os.environ["PYWEBVIEW_GUI"] = "qt"
os.environ["QT_API"] = "pyqt5"
os.environ["QT_XCB_GL_INTEGRATION"] = "none"
os.environ["QT_OPENGL"] = "software"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox --autoplay-policy=no-user-gesture-required --disable-features=FFmpegAllowLists,UseChromeOSDirectVideoDecoder"
# ----------------------------------------------

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

APP_ID = "io.github.BobiButt.siphon"

def _setup_wayland_icon():
    icon_path = Path(__file__).resolve().parents[2] / "assets" / "icons" / "icon.png"
    if not icon_path.exists(): return None
    
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / f"{APP_ID}.desktop"
    content = f"""[Desktop Entry]\nName=Siphon\nExec=siphon\nIcon={icon_path.absolute()}\nType=Application\nCategories=AudioVideo;Video;\n"""
    desktop_file.write_text(content)
    return str(icon_path)

def _setup_ytdlp_plugins(base_path: Path):
    """Copy yt-dlp plugins to user config so they work in PyInstaller."""
    plugin_src = base_path / "yt_dlp_plugins"
    if plugin_src.exists():
        plugin_dest = Path.home() / ".config" / "yt-dlp" / "plugins" / "yt_dlp_plugins"
        plugin_dest.parent.mkdir(parents=True, exist_ok=True)
        if plugin_dest.exists():
            shutil.rmtree(plugin_dest)
        shutil.copytree(plugin_src, plugin_dest)

def launch_app(host: str = "127.0.0.1", port: int = 0, title: str = "Siphon", width: int = 1060, height: int = 760) -> None:
    icon_str = _setup_wayland_icon()

    base_path = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[2]))
    
    # Setup yt-dlp plugins
    _setup_ytdlp_plugins(base_path)

    pot_source = base_path / "assets" / "bin" / "bgutil-pot"
    pot_process = None
    if pot_source.exists():
        cache_dir = Path.home() / ".cache" / "siphon" / "bin"
        cache_dir.mkdir(parents=True, exist_ok=True)
        pot_target = cache_dir / "bgutil-pot"
        
        shutil.copy2(pot_source, pot_target)
        os.chmod(pot_target, 0o755)
        
        # Log POT output so we can debug it in ~/.cache/siphon/pot.log
        log_file = open(Path.home() / ".cache" / "siphon" / "pot.log", "w")
        pot_process = subprocess.Popen(
            [str(pot_target), "server", "--port", "4416"], 
            stdout=log_file, 
            stderr=log_file
        )
        time.sleep(1.5) # Give it a bit more time to boot

    server = SiphonServer(host=host, port=port)
    assigned_port = server.start()
    app_url = f"http://{host}:{assigned_port}"

    def set_icon(window):
        app = QApplication.instance()
        if app:
            app.setDesktopFileName(APP_ID)
            if icon_str:
                icon = QIcon(icon_str)
                app.setWindowIcon(icon)
                for widget in app.topLevelWidgets():
                    widget.setWindowIcon(icon)

    try:
        window = webview.create_window(title=title, url=app_url, width=width, height=height, min_size=(720, 520))
        webview.start(func=set_icon, args=window)
    finally:
        server.stop()
        if pot_process:
            pot_process.terminate()