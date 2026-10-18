"""Unit tests for yt-dlp metadata and format extractor with mock data."""

from unittest.mock import MagicMock, patch
import pytest
from yt_dlp.utils import DownloadError
from siphon.extractors import ExtractionError, extract_video_info


SAMPLE_YT_DATA = {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "duration": 212,
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "uploader": "Rick Astley",
    "formats": [
        {
            "format_id": "18",
            "ext": "mp4",
            "vcodec": "avc1.42001E",
            "acodec": "mp4a.40.2",
            "height": 360,
            "format_note": "360p",
            "filesize": 15000000,
        },
        {
            "format_id": "137",
            "ext": "mp4",
            "vcodec": "avc1.640028",
            "acodec": "none",
            "height": 1080,
            "format_note": "1080p",
            "filesize": 45000000,
        },
        {
            "format_id": "313",
            "ext": "webm",
            "vcodec": "vp9",
            "acodec": "none",
            "height": 2160,
            "format_note": "2160p",
            "filesize": 120000000,
        },
        {
            "format_id": "140",
            "ext": "m4a",
            "vcodec": "none",
            "acodec": "mp4a.40.2",
            "abr": 128,
            "format_note": "medium",
            "filesize": 3500000,
        },
        {
            "format_id": "251",
            "ext": "webm",
            "vcodec": "none",
            "acodec": "opus",
            "abr": 160,
            "format_note": "medium",
            "filesize": 4200000,
        },
    ],
}


def test_extract_video_info_structure() -> None:
    """Test 1: Verify extract_video_info categorizes progressive, video-only, and audio streams."""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = SAMPLE_YT_DATA
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        res = extract_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # Verify metadata
        assert res["id"] == "dQw4w9WgXcQ"
        assert res["title"] == "Rick Astley - Never Gonna Give You Up"
        assert res["duration"] == 212
        assert res["thumbnail"] == "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
        assert res["uploader"] == "Rick Astley"

        # Verify progressive formats
        assert len(res["progressive_options"]) == 1
        prog = res["progressive_options"][0]
        assert prog["format_id"] == "18"
        assert prog["ext"] == "mp4"
        assert prog["quality"] == "360p"
        assert prog["filesize"] == 15000000

        # Verify video-only (DASH) formats
        assert len(res["video_options"]) == 2
        vid_1080 = res["video_options"][0]
        assert vid_1080["format_id"] == "137"
        assert vid_1080["quality"] == "1080p"
        assert vid_1080["ext"] == "mp4"

        vid_4k = res["video_options"][1]
        assert vid_4k["format_id"] == "313"
        assert vid_4k["quality"] == "2160p"
        assert vid_4k["ext"] == "webm"

        # Verify audio-only formats
        assert len(res["audio_options"]) == 2
        aud_m4a = res["audio_options"][0]
        assert aud_m4a["format_id"] == "140"
        assert aud_m4a["bitrate"] == "128 kbps"
        assert aud_m4a["ext"] == "m4a"

        aud_opus = res["audio_options"][1]
        assert aud_opus["format_id"] == "251"
        assert aud_opus["bitrate"] == "160 kbps"
        assert aud_opus["ext"] == "webm"


def test_extract_video_info_empty_url() -> None:
    """Verify empty or invalid URL strings raise ExtractionError."""
    with pytest.raises(ExtractionError):
        extract_video_info("")

    with pytest.raises(ExtractionError):
        extract_video_info("   ")


def test_extract_video_info_download_error() -> None:
    """Verify yt-dlp DownloadError is caught and wrapped into ExtractionError."""
    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = DownloadError("Video unavailable")
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        with pytest.raises(ExtractionError) as exc_info:
            extract_video_info("https://www.youtube.com/watch?v=invalid_id")

        assert "Failed to extract video information" in str(exc_info.value)
