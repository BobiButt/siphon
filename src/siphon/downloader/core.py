"""Core media download pipeline utilizing yt-dlp."""

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yt_dlp
from yt_dlp.utils import DownloadError
from siphon.extractors.ytdlp_extractor import ExtractionError

# Re-export ffmpeg utilities so they can be imported from siphon.downloader
from siphon.downloader.ffmpeg_muxer import (
    ffmpeg_available,
    check_ffmpeg_or_warn,
    mux_streams,
    MuxingError,
)


class DownloadResult(dict):
    """Result dictionary containing paths to downloaded media streams."""

    def __init__(
        self,
        video_path: Optional[Path] = None,
        audio_path: Optional[Path] = None,
        is_dash: bool = False,
        title: str = "",
        video_id: str = "",
        ext: str = "mp4",
    ) -> None:
        super().__init__(
            video_path=video_path,
            audio_path=audio_path,
            is_dash=is_dash,
            title=title,
            video_id=video_id,
            ext=ext,
        )

    @property
    def video_path(self) -> Optional[Path]:
        return self["video_path"]

    @property
    def audio_path(self) -> Optional[Path]:
        return self["audio_path"]

    @property
    def is_dash(self) -> bool:
        return self["is_dash"]

    def __iter__(self):
        yield self["video_path"]
        yield self["audio_path"]


def _get_dl_base_opts() -> Dict[str, Any]:
    """Base yt-dlp options required to bypass YouTube bot checks."""
    return {
        "quiet": True,
        "no_warnings": True,
        "cachedir": False,
        "ignoreerrors": True,
        "remote_components": ["ejs:github"],
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "tv", "web_safari"],
                "fetch_pot": ["always"],
            },
            "youtubepot-bgutilhttp": {
                "base_url": ["http://127.0.0.1:4416"],
            },
        },
        "cookiesfrombrowser": ("firefox",),
    }


def download_media(
    url: str,
    format_id: str,
    output_dir: Union[str, Path],
    temp_dir: Optional[Union[str, Path]] = None,
) -> DownloadResult:
    """Download requested media format(s) using yt-dlp to a temporary location."""
    if not url or not format_id:
        raise ExtractionError("URL and format_id are required for download.")

    staging_dir = Path(temp_dir) if temp_dir else Path(tempfile.mkdtemp(prefix="siphon_dl_"))
    staging_dir.mkdir(parents=True, exist_ok=True)

    ydl_meta_opts = _get_dl_base_opts()
    ydl_meta_opts.update({
        "extract_flat": False,
        "skip_download": True,
    })

    try:
        with yt_dlp.YoutubeDL(ydl_meta_opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False)
    except DownloadError as exc:
        raise ExtractionError(f"Failed to query stream info: {exc}") from exc

    if not info:
        raise ExtractionError("Could not retrieve media metadata.")

    video_id = info.get("id") or "media"
    title = info.get("title") or "video"
    formats: List[Dict[str, Any]] = info.get("formats") or []

    requested_fmt = next((f for f in formats if str(f.get("format_id")) == str(format_id)), None)

    vcodec = requested_fmt.get("vcodec") if requested_fmt else None
    acodec = requested_fmt.get("acodec") if requested_fmt else None
    video_ext = (requested_fmt.get("ext") if requested_fmt else None) or "mp4"

    is_dash_video = bool(vcodec and vcodec != "none" and (not acodec or acodec == "none"))

    if requested_fmt is None and format_id not in ("ba", "bestaudio", "140", "251"):
        is_dash_video = True

    if is_dash_video:
        audio_candidates = [
            f for f in formats
            if f.get("acodec") and f.get("acodec") != "none" and (not f.get("vcodec") or f.get("vcodec") == "none")
        ]
        audio_candidates.sort(key=lambda x: (x.get("abr") or x.get("tbr") or 0), reverse=True)
        best_audio = audio_candidates[0] if audio_candidates else None
        audio_format_id = str(best_audio.get("format_id")) if best_audio else "bestaudio"
        audio_ext = (best_audio.get("ext") if best_audio else None) or "m4a"

        video_path = staging_dir / f"{video_id}_{format_id}.{video_ext}"
        audio_path = staging_dir / f"{video_id}_{audio_format_id}_audio.{audio_ext}"

        ydl_v_opts = _get_dl_base_opts()
        ydl_v_opts.update({
            "format": f"{format_id}/bestvideo",
            "outtmpl": str(video_path),
        })
        with yt_dlp.YoutubeDL(ydl_v_opts) as ydl_v:
            ydl_v.download([url])

        ydl_a_opts = _get_dl_base_opts()
        ydl_a_opts.update({
            "format": str(audio_format_id),
            "outtmpl": str(audio_path),
        })
        with yt_dlp.YoutubeDL(ydl_a_opts) as ydl_a:
            ydl_a.download([url])

        return DownloadResult(
            video_path=video_path,
            audio_path=audio_path,
            is_dash=True,
            title=title,
            video_id=video_id,
            ext=video_ext,
        )

    is_audio_only = bool(acodec and acodec != "none" and (not vcodec or vcodec == "none"))
    file_ext = (requested_fmt.get("ext") if requested_fmt else None) or ("m4a" if is_audio_only else "mp4")
    dest_path = staging_dir / f"{video_id}_{format_id}.{file_ext}"

    ydl_single_opts = _get_dl_base_opts()
    ydl_single_opts.update({
        "format": f"{format_id}/best",
        "outtmpl": str(dest_path),
    })
    with yt_dlp.YoutubeDL(ydl_single_opts) as ydl_s:
        ydl_s.download([url])

    if is_audio_only:
        return DownloadResult(
            video_path=None,
            audio_path=dest_path,
            is_dash=False,
            title=title,
            video_id=video_id,
            ext=file_ext,
        )

    return DownloadResult(
        video_path=dest_path,
        audio_path=None,
        is_dash=False,
        title=title,
        video_id=video_id,
        ext=file_ext,
    )