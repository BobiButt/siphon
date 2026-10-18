"""Integration tests for Siphon dynamic Uvicorn server and health check."""

from typing import Generator, Tuple
import httpx
import pytest
from siphon.server import SiphonServer, start_server


@pytest.fixture
def running_server() -> Generator[Tuple[SiphonServer, int], None, None]:
    """Fixture that starts a SiphonServer on port 0 and yields (server, port)."""
    server = SiphonServer(host="127.0.0.1", port=0)
    port = server.start()
    try:
        yield server, port
    finally:
        if server.is_running:
            server.stop()


def test_dynamic_port_assignment(running_server: Tuple[SiphonServer, int]) -> None:
    """Test 1: Verify assigned port is dynamic, > 0, and not the hardcoded default 8000."""
    server, port = running_server
    assert port > 0, "Port must be a positive integer"
    assert port != 8000, "Port must NOT be hardcoded to 8000"
    assert server.bound_port == port
    assert server.is_running


def test_health_endpoint(running_server: Tuple[SiphonServer, int]) -> None:
    """Test 2: Verify HTTP GET /health returns 200 OK with {'status': 'ok', 'app': 'siphon'}."""
    server, port = running_server
    url = f"http://127.0.0.1:{port}/health"
    response = httpx.get(url, timeout=5.0)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "siphon"}


def test_clean_server_shutdown() -> None:
    """Test 3: Verify the server terminates cleanly and closes socket when stopped."""
    server = SiphonServer(host="127.0.0.1", port=0)
    port = server.start()
    assert server.is_running

    # Confirm it is serving requests
    url = f"http://127.0.0.1:{port}/health"
    response = httpx.get(url, timeout=5.0)
    assert response.status_code == 200

    # Stop server
    server.stop(timeout=5.0)
    assert not server.is_running

    # Confirm socket is no longer accepting requests
    with pytest.raises(httpx.ConnectError):
        httpx.get(url, timeout=1.0)


def test_start_server_convenience_function() -> None:
    """Verify start_server helper returns assigned port and functional stop callable."""
    port, stop_fn = start_server(host="127.0.0.1", port=0)
    assert port > 0
    assert port != 8000

    url = f"http://127.0.0.1:{port}/health"
    response = httpx.get(url, timeout=5.0)
    assert response.status_code == 200

    stop_fn()


def test_static_frontend_served(running_server: Tuple[SiphonServer, int]) -> None:
    """Verify root / serves the frontend index.html."""
    server, port = running_server
    url = f"http://127.0.0.1:{port}/"
    response = httpx.get(url, timeout=5.0)
    assert response.status_code == 200
    assert "<title>Siphon</title>" in response.text
