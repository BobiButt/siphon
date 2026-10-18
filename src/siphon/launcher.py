"""pywebview desktop shell launcher for Siphon."""

import os
from pathlib import Path
from typing import Optional
import webview
from siphon.server import SiphonServer


def launch_app(
    host: str = "127.0.0.1",
    port: int = 0,
    title: str = "Siphon",
    icon_path: Optional[str] = None,
    width: int = 1060,
    height: int = 760,
) -> None:
    """Launch the Siphon desktop application shell.

    1. Starts the Uvicorn server in a background daemon thread bound dynamically to port 0 on 127.0.0.1.
    2. Waits for dynamic port assignment from the OS kernel.
    3. Creates a pywebview window pointing to http://127.0.0.1:<port> with native WebKitGTK.
    4. Calls webview.start() on the main thread (blocking until window is closed).
    5. Cleanly triggers server shutdown when the window is closed.
    """
    if icon_path is None:
        default_icon = Path(__file__).resolve().parents[2] / "assets" / "icons" / "icon.png"
        icon_path = str(default_icon) if default_icon.exists() else "assets/icons/icon.png"

    # Start background Uvicorn server with dynamic port 0
    server = SiphonServer(host=host, port=port)
    assigned_port = server.start()
    app_url = f"http://{host}:{assigned_port}"

    try:
        # Create desktop window
        icon_arg = icon_path if (icon_path and (os.path.exists(icon_path) or icon_path.startswith("assets/"))) else None
        webview.create_window(
            title=title,
            url=app_url,
            width=width,
            height=height,
            min_size=(720, 520),
            icon=icon_arg,
        )

        # Start native desktop window event loop on main thread
        webview.start()
    finally:
        # Gracefully stop Uvicorn server when GUI window closes
        server.stop()
