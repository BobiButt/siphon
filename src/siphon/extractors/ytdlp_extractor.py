"""yt-dlp extraction engine for Siphon."""

from typing import Any, Dict, List, Optional
import yt_dlp
from yt_dlp.utils import DownloadError


class ExtractionError(Exception):
    """Raised when media metadata or format extraction fails."""
    pass


def extract_video_info(url: str) -> Dict[str, Any]:
    """Extract metadata and categorized formats for a given YouTube URL.

    Uses the native yt-dlp Python API with quiet options.
    Separates progressive, video-only (DASH), and audio-only streams.

    Args:
        url: The YouTube video URL to inspect.

    Returns:
        A dictionary containing video metadata and separated format lists.

    Raises:
        ExtractionError: If the URL is invalid or extraction encounters an error.
    """
    if not url or not isinstance(url, str) or not url.strip():
        raise ExtractionError("A valid YouTube URL must be provided.")

    ydl_opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False)
    except DownloadError as exc:
        raise ExtractionError(f"Failed to extract video information: {exc}") from exc
    except Exception as exc:
        raise ExtractionError(f"Unexpected extraction error: {exc}") from exc

    if not info:
        raise ExtractionError("No video information could be retrieved.")

    # Extract metadata fields
    title: str = info.get("title") or ""
    duration: Optional[int] = info.get("duration")
    thumbnail: str = info.get("thumbnail") or ""
    uploader: str = info.get("uploader") or info.get("channel") or ""
    video_id: str = info.get("id") or ""

    formats: List[Dict[str, Any]] = info.get("formats") or []
    progressive_options: List[Dict[str, Any]] = []
    video_options: List[Dict[str, Any]] = []
    audio_options: List[Dict[str, Any]] = []

    for f in formats:
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        format_id = str(f.get("format_id") or "")
        ext = f.get("ext") or ""
        filesize = f.get("filesize") or f.get("filesize_approx")
        height = f.get("height")
        format_note = f.get("format_note")

        # Progressive: contains both video and audio
        if vcodec and vcodec != "none" and acodec and acodec != "none":
            quality = f"{height}p" if height else (format_note or f.get("resolution") or "progressive")
            progressive_options.append({
                "quality": quality,
                "format_id": format_id,
                "ext": ext,
                "filesize": filesize,
            })

        # Video-only: DASH video stream without audio
        elif vcodec and vcodec != "none" and (not acodec or acodec == "none"):
            quality = f"{height}p" if height else (format_note or f.get("resolution") or "video")
            video_options.append({
                "quality": quality,
                "format_id": format_id,
                "ext": ext,
                "filesize": filesize,
            })

        # Audio-only: audio stream without video
        elif acodec and acodec != "none" and (not vcodec or vcodec == "none"):
            abr = f.get("abr") or f.get("tbr")
            bitrate = f"{int(abr)} kbps" if abr else (format_note or "audio")
            audio_options.append({
                "bitrate": bitrate,
                "format_id": format_id,
                "ext": ext,
                "filesize": filesize,
            })

    return {
        "id": video_id,
        "title": title,
        "duration": duration,
        "thumbnail": thumbnail,
        "uploader": uploader,
        "url": url,
        "progressive_options": progressive_options,
        "video_options": video_options,
        "audio_options": audio_options,
    }
