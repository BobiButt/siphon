"""Core media download pipeline utilizing yt-dlp."""

from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional, Union
import yt_dlp
from yt_dlp.utils import DownloadError
from siphon.extractors.ytdlp_extractor import ExtractionError


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


def download_media(
    url: str,
    format_id: str,
    output_dir: Union[str, Path],
    temp_dir: Optional[Union[str, Path]] = None,
) -> DownloadResult:
    """Download requested media format(s) using yt-dlp to a temporary location.

    If format_id corresponds to a DASH video-only stream, automatically identifies
    and downloads a complementary high-quality audio stream for subsequent muxing.

    Args:
        url: YouTube media URL.
        format_id: Chosen format ID from extractor info.
        output_dir: Destination directory for media.
        temp_dir: Directory used for staging stream files.

    Returns:
        DownloadResult containing paths to downloaded stream(s).

    Raises:
        ExtractionError: If media metadata cannot be retrieved or downloads fail.
    """
    if not url or not format_id:
        raise ExtractionError("URL and format_id are required for download.")

    staging_dir = Path(temp_dir) if temp_dir else Path(tempfile.mkdtemp(prefix="siphon_dl_"))
    staging_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Query formats to determine stream type (progressive vs DASH vs audio-only)
    ydl_meta_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }

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

    # Locate requested format
    requested_fmt = next((f for f in formats if str(f.get("format_id")) == str(format_id)), None)

    vcodec = requested_fmt.get("vcodec") if requested_fmt else None
    acodec = requested_fmt.get("acodec") if requested_fmt else None
    video_ext = (requested_fmt.get("ext") if requested_fmt else None) or "mp4"

    # Identify if format is DASH video-only (needs audio companion)
    is_dash_video = bool(vcodec and vcodec != "none" and (not acodec or acodec == "none"))

    # If requested format wasn't explicitly found in format list, heuristic check
    if requested_fmt is None and format_id not in ("ba", "bestaudio", "140", "251"):
        # Assume DASH if requested format indicates high resolution video without audio
        is_dash_video = True

    if is_dash_video:
        # Find best available audio format
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

        # Download video stream
        ydl_v_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": str(format_id),
            "outtmpl": str(video_path),
        }
        with yt_dlp.YoutubeDL(ydl_v_opts) as ydl_v:
            ydl_v.download([url])

        # Download audio stream
        ydl_a_opts = {
            "quiet": True,
            "no_warnings": True,
            "format": str(audio_format_id),
            "outtmpl": str(audio_path),
        }
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

    # Progressive or audio-only stream
    is_audio_only = bool(acodec and acodec != "none" and (not vcodec or vcodec == "none"))
    file_ext = (requested_fmt.get("ext") if requested_fmt else None) or ("m4a" if is_audio_only else "mp4")
    dest_path = staging_dir / f"{video_id}_{format_id}.{file_ext}"

    ydl_single_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": str(format_id),
        "outtmpl": str(dest_path),
    }
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
