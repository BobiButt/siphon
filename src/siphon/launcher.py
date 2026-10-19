"""pywebview desktop shell launcher for Siphon."""

import os
import subprocess
import time
import sys
from pathlib import Path

# --- FIX: Force software rendering to prevent GLX crashes in AppImage ---
# These MUST be set before importing webview or PyQt5
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox"
os.environ["QT_OPENGL"] = "software"
os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"
os.environ["PYWEBVIEW_GUI"] = "qt"
os.environ["QT_API"] = "pyqt5"
# ------------------------------------------------------------------------

import webview
from siphon.server import SiphonServer
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

def launch_app(host: str = "127.0.0.1", port: int = 0, title: str = "Siphon", width: int = 1060, height: int = 760) -> None:
    icon_str = _setup_wayland_icon()

    base_path = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[2]))
    pot_bin = base_path / "assets" / "bin" / "bgutil-pot"
    
    pot_process = None
    if pot_bin.exists():
        pot_process = subprocess.Popen([str(pot_bin), "server", "--port", "4416"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

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