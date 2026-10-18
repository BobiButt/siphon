"""Unit tests for Siphon download pipeline and static FFmpeg muxer with mocking."""

from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest
from siphon.app import create_app
from siphon.downloader import DownloadResult, MuxingError, download_media, mux_streams


SAMPLE_FORMATS_METADATA = {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "duration": 212,
    "formats": [
        {
            "format_id": "18",
            "ext": "mp4",
            "vcodec": "avc1.42001E",
            "acodec": "mp4a.40.2",
            "height": 360,
        },
        {
            "format_id": "137",
            "ext": "mp4",
            "vcodec": "avc1.640028",
            "acodec": "none",
            "height": 1080,
        },
        {
            "format_id": "140",
            "ext": "m4a",
            "vcodec": "none",
            "acodec": "mp4a.40.2",
            "abr": 128,
        },
    ],
}


def test_download_media_dash_resolves_and_downloads_both_streams(tmp_path: Path) -> None:
    """Test 1: Mock yt_dlp.YoutubeDL and verify download_media returns correct video and audio paths for DASH."""
    staging_dir = tmp_path / "staging"
    output_dir = tmp_path / "output"

    with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = SAMPLE_FORMATS_METADATA
        mock_ydl.download.return_value = 0
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        res = download_media(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            format_id="137",
            output_dir=output_dir,
            temp_dir=staging_dir,
        )

        expected_video = staging_dir / "dQw4w9WgXcQ_137.mp4"
        expected_audio = staging_dir / "dQw4w9WgXcQ_140_audio.m4a"

        assert res.video_path == expected_video
        assert res.audio_path == expected_audio
        assert res["video_path"] == expected_video
        assert res["audio_path"] == expected_audio
        assert res.is_dash is True

        # Verify ydl downloaded both streams
        assert mock_ydl.download.call_count == 2


def test_mux_streams_generates_exact_command(tmp_path: Path) -> None:
    """Test 2: Mock subprocess.run and assert mux_streams builds the exact FFmpeg command string."""
    with patch("subprocess.run") as mock_subproc:
        mock_subproc.return_value = MagicMock(returncode=0, stdout="", stderr="")

        video_file = "video.mp4"
        audio_file = "audio.m4a"
        output_file = "output.mp4"

        result_path = mux_streams(
            video_path=video_file,
            audio_path=audio_file,
            output_path=output_file,
            ffmpeg_bin="assets/ffmpeg/ffmpeg",
            cleanup_sources=False,
        )

        expected_cmd = [
            "assets/ffmpeg/ffmpeg",
            "-i",
            "video.mp4",
            "-i",
            "audio.m4a",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "output.mp4",
        ]

        # Verify exact command list
        mock_subproc.assert_called_once_with(
            expected_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        assert result_path == Path(output_file)


def test_mux_streams_raises_muxing_error_on_failure() -> None:
    """Test 3: Mock subprocess.run with non-zero exit code and assert MuxingError is raised."""
    with patch("subprocess.run") as mock_subproc:
        mock_subproc.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="[aac @ 0x55] Error while opening encoder",
        )

        with pytest.raises(MuxingError) as exc_info:
            mux_streams(
                video_path="video.mp4",
                audio_path="audio.m4a",
                output_path="output.mp4",
                ffmpeg_bin="assets/ffmpeg/ffmpeg",
                cleanup_sources=False,
            )

        assert "FFmpeg muxing failed (exit 1)" in str(exc_info.value)
        assert "Error while opening encoder" in str(exc_info.value)


def test_api_download_endpoint_success(tmp_path: Path) -> None:
    """Test 4: Verify POST /api/download returns 200 OK and executes download and muxing pipeline."""
    app = create_app()
    client = TestClient(app)

    fake_video = tmp_path / "temp_video.mp4"
    fake_audio = tmp_path / "temp_audio.m4a"
    fake_output = tmp_path / "muxed_output.mp4"

    mock_dl_result = DownloadResult(
        video_path=fake_video,
        audio_path=fake_audio,
        is_dash=True,
        title="Sample Video",
        video_id="sample123",
        ext="mp4",
    )

    with patch("siphon.api.download_media", return_value=mock_dl_result) as mock_dl, \
         patch("siphon.api.mux_streams", return_value=fake_output) as mock_mux:

        payload = {
            "url": "https://www.youtube.com/watch?v=sample123",
            "format_id": "137",
            "output_dir": str(tmp_path),
        }

        response = client.post("/api/download", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["output_path"] == str(fake_output)

        mock_dl.assert_called_once_with(
            url="https://www.youtube.com/watch?v=sample123",
            format_id="137",
            output_dir=tmp_path,
        )
        mock_mux.assert_called_once()
