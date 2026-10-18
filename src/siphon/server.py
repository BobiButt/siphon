"""Uvicorn server manager binding dynamically to port 0 on 127.0.0.1."""

import threading
import time
from typing import Any, Callable, Optional, Tuple
import uvicorn
from uvicorn import Config, Server
from siphon.app import create_app


class SiphonServer:
    """Manages programmatic execution of Uvicorn on localhost with dynamic port allocation."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0, app: Optional[Any] = None) -> None:
        self.host = host
        self.port = port
        self.app = app if app is not None else create_app()
        self.config = Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
            loop="asyncio",
        )
        self.server = Server(config=self.config)
        self.bound_port: Optional[int] = None
        self._thread: Optional[threading.Thread] = None

    def start(self, timeout: float = 5.0) -> int:
        """Start the server in a background thread and wait for dynamic port assignment."""
        self._thread = threading.Thread(target=self.server.run, daemon=True)
        self._thread.start()

        start_time = time.time()
        while time.time() - start_time < timeout:
            if getattr(self.server, "started", False) and getattr(self.server, "servers", None):
                try:
                    sockets = self.server.servers[0].sockets
                    if sockets:
                        self.bound_port = sockets[0].getsockname()[1]
                        return self.bound_port
                except (IndexError, AttributeError):
                    pass
            time.sleep(0.01)

        raise TimeoutError(f"Uvicorn server failed to bind and start within {timeout} seconds.")

    def stop(self, timeout: float = 5.0) -> None:
        """Signal Uvicorn to exit and wait for the runner thread to terminate."""
        self.server.should_exit = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    @property
    def is_running(self) -> bool:
        """Check if server thread is active and running."""
        return self._thread is not None and self._thread.is_alive()


def start_server(
    host: str = "127.0.0.1", port: int = 0, app: Optional[Any] = None
) -> Tuple[int, Callable[[], None]]:
    """Start the Siphon server on the specified host and port (defaults to 127.0.0.1:0).

    Returns a tuple containing:
        - bound_port (int): The dynamically assigned OS port.
        - stop_fn (Callable[[], None]): Function to trigger clean server shutdown.
    """
    server_instance = SiphonServer(host=host, port=port, app=app)
    bound_port = server_instance.start()
    return bound_port, server_instance.stop
