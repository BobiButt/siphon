"""CLI entry point for Siphon."""

import argparse
import signal
import sys
import time
from typing import Any
from siphon import __app_name__, __version__
from siphon.launcher import launch_app
from siphon.server import SiphonServer


def main() -> None:
    """Parse CLI arguments and run Siphon in the requested mode."""
    parser = argparse.ArgumentParser(
        prog="siphon",
        description=f"{__app_name__} v{__version__} — YouTube Media Downloader for Linux",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run backend server in headless mode without opening GUI window.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind (strictly 127.0.0.1 by default).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port to bind (0 for dynamic OS allocation).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__app_name__} {__version__}",
    )

    args = parser.parse_args()

    # Security check: never allow binding to 0.0.0.0
    if args.host != "127.0.0.1" and args.host != "localhost":
        sys.stderr.write("Error: For security, Siphon only binds to localhost / 127.0.0.1.\n")
        sys.exit(1)

    if not args.headless:
        # Launch native desktop pywebview shell on main thread
        launch_app(host=args.host, port=args.port)
        return

    # Headless backend mode for testing and debugging
    server = SiphonServer(host=args.host, port=args.port)
    assigned_port = server.start()
    print(f"[{__app_name__}] Server started on http://127.0.0.1:{assigned_port}")
    print(f"[{__app_name__}] Health endpoint available at http://127.0.0.1:{assigned_port}/health")
    print(f"[{__app_name__}] Press Ctrl+C to stop.")

    running = True

    def _signal_handler(sig: int, frame: Any) -> None:
        nonlocal running
        print("\nStopping Siphon server...")
        running = False
        server.stop()
        print("Siphon server stopped cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        while running and server.is_running:
            time.sleep(0.2)
    except KeyboardInterrupt:
        _signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
