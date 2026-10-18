"""Tests for Milestone 7: YouTube search, direct streaming, and FFmpeg availability."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from yt_dlp.utils import DownloadError

from siphon.app import create_app
from siphon.downloader import check_ffmpeg_or_warn, ffmpeg_available
from siphon.extractors import (
    ExtractionError,
    extract_stream_url,
    extract_video_info,
    search_youtube,
)


MOCK_SEARCH_RAW = {
    "entries": [
        {
            "id": "abc123",
            "title": "Result One",
            "uploader": "Channel A",
            "duration": 120,
            "thumbnail": "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
        },
        {
            "id": "def456",
            "title": "Result Two",
            "channel": "Channel B",
            "duration": None,
            "thumbnail": None,
        },
    ]
}

MOCK_SEARCH_RESULTS = [
    {
        "id": "abc123",
        "title": "Result One",
        "uploader": "Channel A",
        "duration": 120,
        "thumbnail": "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=abc123",
    },
    {
        "id": "def456",
        "title": "Result Two",
        "uploader": "Channel B",
        "duration": None,
        "thumbnail": None,
        "url": "https://www.youtube.com/watch?v=def456",
    },
]


def test_search_youtube_uses_full_extraction() -> None:
    """search_youtube uses ytsearch<N>: with extract_flat=False and maps entries.

    extract_flat=False forces yt-dlp to resolve full metadata so thumbnails and
    durations are reliably populated for the results grid.
    """
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = MOCK_SEARCH_RAW
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        results = search_youtube("test query", limit=5)

        # Verify the ytsearch pseudo-URL and FULL (non-flat) extraction were used.
        positional_args, kwargs = mock_ydl_cls.call_args
        opts = positional_args[0]
        assert opts["extract_flat"] == "in_playlist"
        mock_ydl.extract_info.assert_called_once_with("ytsearch5:test query", download=False)

        # Verify mapping to the documented result shape.
        assert len(results) == 2
        first = results[0]
        assert first["id"] == "abc123"
        assert first["title"] == "Result One"
        assert first["uploader"] == "Channel A"
        assert first["duration"] == 120
        assert first["url"] == "https://www.youtube.com/watch?v=abc123"

        # 'channel' is used as a fallback uploader when 'uploader' is absent.
        assert results[1]["uploader"] == "Channel B"


def test_search_youtube_empty_query_raises() -> None:
    """Empty or whitespace-only queries raise ExtractionError."""
    with patch("yt_dlp.YoutubeDL"):
        try:
            search_youtube("   ")
            raise AssertionError("Expected ExtractionError for empty query")
        except ExtractionError:
            pass


def test_search_youtube_download_error_wrapped() -> None:
    """yt-dlp DownloadError during search is wrapped into ExtractionError."""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = DownloadError("rate limited")
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        try:
            search_youtube("something")
            raise AssertionError("Expected ExtractionError")
        except ExtractionError as exc:
            assert "Search failed" in str(exc)


def test_cookiefile_attached_when_cookies_exist(tmp_path: Path) -> None:
    """_build_ydl_opts passes cookiefile to yt-dlp when cookies.txt exists."""
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape HTTP Cookie File\n")

    with patch("siphon.extractors.ytdlp_extractor.get_cookies_path", return_value=cookies):
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = MOCK_SEARCH_RAW
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            search_youtube("hello")

            opts = mock_ydl_cls.call_args[0][0]
            assert opts["cookiesfrombrowser"] == ("firefox",)


def test_cookiefile_omitted_when_cookies_absent(tmp_path: Path) -> None:
    """_build_ydl_opts omits cookiefile when cookies.txt does not exist."""
    missing = tmp_path / "no_such_cookies.txt"

    with patch("siphon.extractors.ytdlp_extractor.get_cookies_path", return_value=missing):
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = MagicMock()
            mock_ydl.extract_info.return_value = MOCK_SEARCH_RAW
            mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

            search_youtube("hello")

            opts = mock_ydl_cls.call_args[0][0]
            assert "cookiefile" not in opts


def test_bot_check_error_raises_cookie_guidance() -> None:
    """A 'not a bot' DownloadError maps to the exact cookie guidance message."""
    from siphon.extractors.ytdlp_extractor import BOT_CHECK_GUIDANCE

    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = DownloadError(
            "Sign in to confirm you're not a bot. This helps protect our community."
        )
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        try:
            search_youtube("anything")
            raise AssertionError("Expected ExtractionError")
        except ExtractionError as exc:
            assert str(exc) == BOT_CHECK_GUIDANCE
            assert "cookies.txt" in str(exc)


def test_bot_check_error_in_video_info_raises_cookie_guidance() -> None:
    """extract_video_info also surfaces cookie guidance on the bot check."""
    from siphon.extractors.ytdlp_extractor import BOT_CHECK_GUIDANCE

    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = DownloadError(
            "youtube said: Sign in to confirm you're not a bot"
        )
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        try:
            extract_video_info("https://www.youtube.com/watch?v=abc")
            raise AssertionError("Expected ExtractionError")
        except ExtractionError as exc:
            assert str(exc) == BOT_CHECK_GUIDANCE


def test_non_bot_error_keeps_context_message() -> None:
    """Non-bot DownloadErrors retain their contextual prefix (not the cookie message)."""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = DownloadError("Video unavailable")
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        try:
            extract_video_info("https://www.youtube.com/watch?v=abc")
            raise AssertionError("Expected ExtractionError")
        except ExtractionError as exc:
            assert "Failed to extract video information" in str(exc)
            assert "cookies.txt" not in str(exc)


def test_info_includes_stream_url_for_progressive() -> None:
    """extract_video_info returns the best progressive direct URL as stream_url."""
    data = {
        "id": "vid",
        "title": "T",
        "formats": [
            {"format_id": "18", "vcodec": "avc1", "acodec": "mp4a", "height": 360, "url": "https://cdn/low.mp4"},
            {"format_id": "22", "vcodec": "avc1", "acodec": "mp4a", "height": 720, "url": "https://cdn/high.mp4"},
            {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080, "url": "https://cdn/dash.mp4"},
        ],
    }
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = data
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        res = extract_video_info("https://www.youtube.com/watch?v=vid")

        # Highest progressive (720p) URL should be chosen; DASH (1080p) ignored.
        assert res["stream_url"] == "https://cdn/high.mp4"


def test_info_stream_url_none_when_no_progressive() -> None:
    """stream_url is None when only DASH/audio streams exist (no muxed stream)."""
    data = {
        "id": "vid",
        "title": "T",
        "formats": [
            {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080, "url": "https://cdn/dash.mp4"},
            {"format_id": "140", "vcodec": "none", "acodec": "mp4a", "url": "https://cdn/audio.m4a"},
        ],
    }
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = data
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        res = extract_video_info("https://www.youtube.com/watch?v=vid")
        assert res["stream_url"] is None


def test_extract_stream_url_returns_direct_url() -> None:
    """extract_stream_url returns the resolved progressive direct URL."""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "url": "https://cdn/stream.mp4",
            "title": "Playable",
        }
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        res = extract_stream_url("https://www.youtube.com/watch?v=abc")
        assert res["stream_url"] == "https://cdn/stream.mp4"
        assert res["title"] == "Playable"


def test_api_search_endpoint_success() -> None:
    """GET /api/search?q=... returns the mapped result list."""
    app = create_app()
    client = TestClient(app)

    with patch("siphon.api.search_youtube", return_value=MOCK_SEARCH_RESULTS) as mock_search:
        resp = client.get("/api/search?q=hello")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["id"] == "abc123"
        assert data[0]["url"] == "https://www.youtube.com/watch?v=abc123"
        mock_search.assert_called_once()


def test_api_search_endpoint_empty_query_returns_400() -> None:
    """GET /api/search with a whitespace query returns 400."""
    app = create_app()
    client = TestClient(app)

    resp = client.get("/api/search?q=%20%20")
    assert resp.status_code == 400
    assert "detail" in resp.json()


def test_api_stream_endpoint_success() -> None:
    """GET /api/stream?url=... returns the direct stream_url."""
    app = create_app()
    client = TestClient(app)

    payload = {"stream_url": "https://cdn/play.mp4", "title": "Play"}
    with patch("siphon.api.extract_stream_url", return_value=payload) as mock_stream:
        resp = client.get("/api/stream?url=https://youtube.com/watch?v=1")

        assert resp.status_code == 200
        assert resp.json()["stream_url"] == "https://cdn/play.mp4"
        mock_stream.assert_called_once()


def test_api_stream_endpoint_empty_url_returns_400() -> None:
    """GET /api/stream with an empty url returns 400."""
    app = create_app()
    client = TestClient(app)

    resp = client.get("/api/stream?url=%20")
    assert resp.status_code == 400


def test_ffmpeg_available_false_for_missing_path(tmp_path: Path) -> None:
    """ffmpeg_available returns False when the binary is absent."""
    missing = tmp_path / "ffmpeg"
    assert ffmpeg_available(missing) is False


def test_ffmpeg_available_true_for_executable(tmp_path: Path) -> None:
    """ffmpeg_available returns True for an existing executable file."""
    binary = tmp_path / "ffmpeg"
    binary.write_bytes(b"#!/bin/sh\n")
    binary.chmod(0o755)
    assert ffmpeg_available(binary) is True


def test_check_ffmpeg_or_warn_logs_warning(tmp_path: Path, caplog) -> None:
    """check_ffmpeg_or_warn emits a clear warning when FFmpeg is missing."""
    missing = tmp_path / "ffmpeg"
    with caplog.at_level("WARNING"):
        result = check_ffmpeg_or_warn(missing)

    assert result is False
    assert any("FFmpeg not found" in record.message for record in caplog.records)