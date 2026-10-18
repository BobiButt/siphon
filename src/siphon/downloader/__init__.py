"""Downloader and media muxing modules for Siphon."""

from siphon.downloader.core import DownloadResult, download_media
from siphon.downloader.ffmpeg_muxer import (
    DEFAULT_FFMPEG_PATH,
    MuxingError,
    check_ffmpeg_or_warn,
    ffmpeg_available,
    mux_streams,
)

__all__ = [
    "download_media",
    "DownloadResult",
    "mux_streams",
    "MuxingError",
    "ffmpeg_available",
    "check_ffmpeg_or_warn",
    "DEFAULT_FFMPEG_PATH",
]
