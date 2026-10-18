"""pywebview desktop shell launcher for Siphon."""

import webview
from siphon.server import SiphonServer


def launch_app(
    host: str = "127.0.0.1",
    port: int = 0,
    title: str = "Siphon",
    width: int = 1060,
    height: int = 760,
) -> None:
    """Launch the Siphon desktop application shell.

    1. Starts the Uvicorn server in a background daemon thread bound dynamically to port 0 on 127.0.0.1.
    2. Waits for dynamic port assignment from the OS kernel.
    3. Creates a pywebview window pointing to http://127.0.0.1:<port> with native WebKitGTK.
    4. Calls webview.start() on the main thread (blocking until window is closed).
    5. Cleanly triggers server shutdown when the window is closed.

    Note: no window icon is passed to pywebview because its ``create_window`` API does not
    accept an ``icon`` argument. Desktop icon integration is handled by the AppImage and
    the XDG ``.desktop`` entry instead.
    """
    # Start background Uvicorn server with dynamic port 0
    server = SiphonServer(host=host, port=port)
    assigned_port = server.start()
    app_url = f"http://{host}:{assigned_port}"

    try:
        # Create desktop window (intentionally no icon kwarg: unsupported by pywebview)
        webview.create_window(
            title=title,
            url=app_url,
            width=width,
            height=height,
            min_size=(720, 520),
        )

        # Start native desktop window event loop on main thread
        webview.start()
    finally:
        # Gracefully stop Uvicorn server when GUI window closes
        server.stop()
