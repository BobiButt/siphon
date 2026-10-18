"""Unit tests for Siphon pywebview desktop shell launcher with GUI mocking."""

import sys
from unittest.mock import MagicMock, call, patch
import pytest
from siphon.launcher import launch_app


def test_launch_app_lifecycle_and_port_forwarding() -> None:
    """Test 1, 2, 3, 4: Verify launch_app dynamically constructs the URL, starts webview, and triggers server shutdown on exit."""
    with patch("webview.create_window") as mock_create_window, \
         patch("webview.start") as mock_webview_start, \
         patch("siphon.launcher.SiphonServer") as mock_server_cls:

        mock_server = MagicMock()
        mock_server.start.return_value = 52189
        mock_server_cls.return_value = mock_server

        # Order of execution tracker
        execution_order = []
        mock_webview_start.side_effect = lambda: execution_order.append("webview_started")
        mock_server.stop.side_effect = lambda: execution_order.append("server_stopped")

        # Execute launcher
        launch_app(host="127.0.0.1", port=0)

        # Test 1 & 2: Assert dynamic URL construction
        mock_server_cls.assert_called_once_with(host="127.0.0.1", port=0)
        mock_server.start.assert_called_once()

        mock_create_window.assert_called_once()
        _, kwargs = mock_create_window.call_args
        assert kwargs["title"] == "Siphon"
        assert kwargs["url"] == "http://127.0.0.1:52189"

        # Test 3: Assert webview.start was called
        mock_webview_start.assert_called_once()

        # Test 4: Assert server.stop was triggered after webview.start returned
        mock_server.stop.assert_called_once()
        assert execution_order == ["webview_started", "server_stopped"]


def test_launch_app_graceful_shutdown_on_error() -> None:
    """Verify server shutdown is guaranteed even if webview raises an exception."""
    with patch("webview.create_window"), \
         patch("webview.start", side_effect=RuntimeError("GUI error")), \
         patch("siphon.launcher.SiphonServer") as mock_server_cls:

        mock_server = MagicMock()
        mock_server.start.return_value = 49123
        mock_server_cls.return_value = mock_server

        with pytest.raises(RuntimeError, match="GUI error"):
            launch_app(host="127.0.0.1", port=0)

        mock_server.stop.assert_called_once()


def test_main_cli_gui_dispatch() -> None:
    """Verify python -m siphon without --headless dispatches to launch_app."""
    with patch("siphon.__main__.launch_app") as mock_launch, \
         patch.object(sys, "argv", ["siphon"]):

        from siphon.__main__ import main
        main()

        mock_launch.assert_called_once_with(host="127.0.0.1", port=0)
