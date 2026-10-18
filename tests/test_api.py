"""API endpoint tests for Siphon with mocked extraction engine."""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from yt_dlp.utils import DownloadError
from siphon.app import create_app
from siphon.extractors import ExtractionError


MOCK_EXTRACTED_DATA = {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "duration": 212,
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "uploader": "Rick Astley",
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "progressive_options": [
        {"quality": "360p", "format_id": "18", "ext": "mp4", "filesize": 15000000}
    ],
    "video_options": [
        {"quality": "1080p", "format_id": "137", "ext": "mp4", "filesize": 45000000}
    ],
    "audio_options": [
        {"bitrate": "128 kbps", "format_id": "140", "ext": "m4a", "filesize": 3500000}
    ],
}


def test_api_info_success() -> None:
    """Test 3: Assert /api/info?url=... returns 200 OK and matching JSON structure."""
    app = create_app()
    client = TestClient(app)

    with patch("siphon.api.extract_video_info", return_value=MOCK_EXTRACTED_DATA) as mock_extract:
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        response = client.get(f"/api/info?url={url}")

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Rick Astley - Never Gonna Give You Up"
        assert data["duration"] == 212
        assert len(data["progressive_options"]) == 1
        assert len(data["video_options"]) == 1
        assert len(data["audio_options"]) == 1
        assert data["video_options"][0]["quality"] == "1080p"

        mock_extract.assert_called_once_with(url)


def test_api_info_extraction_error_returns_400() -> None:
    """Test 2: Assert extraction failures (e.g. DownloadError) return HTTP 400 Bad Request."""
    app = create_app()
    client = TestClient(app)

    with patch("siphon.api.extract_video_info", side_effect=ExtractionError("Video unavailable or private")):
        url = "https://www.youtube.com/watch?v=private_video"
        response = client.get(f"/api/info?url={url}")

        assert response.status_code == 400
        body = response.json()
        assert "detail" in body
        assert "Video unavailable or private" in body["detail"]


def test_api_info_empty_url_returns_400() -> None:
    """Verify empty url query parameter returns 400 Bad Request."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/info?url=   ")
    assert response.status_code == 400
    assert "detail" in response.json()


def test_api_info_missing_url_returns_422() -> None:
    """Verify missing required url parameter returns FastAPI 422 Unprocessable Entity."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/info")
    assert response.status_code == 422
