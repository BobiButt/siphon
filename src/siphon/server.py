"""Uvicorn server manager binding to ephemeral port 0 on 127.0.0.1."""

from typing import Any, Optional


class ServerManager:
    """Manages the lifecycle of the Uvicorn server bound to localhost port 0.

    Stub implementation for project scaffolding.
    Full dynamic port resolution and background thread runner implemented in Milestone 1.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 0) -> None:
        self.host = host
        self.port = port
        self.bound_port: Optional[int] = None
        self._server: Optional[Any] = None

    def start(self) -> int:
        """Start server and return the dynamically assigned OS port."""
        return self.bound_port or self.port

    def stop(self) -> None:
        """Gracefully terminate the running server."""
        pass
