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

    # Track the highest-quality direct URL for a progressive (muxed) stream so the
    # frontend can stream playback via an HTML5 <video> tag without a second extraction.
    best_progressive_url: Optional[str] = None
    best_progressive_height: int = -1

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

            # Remember the best (highest) progressive direct URL for streaming playback.
            direct_url = f.get("url")
            if direct_url and (height or 0) > best_progressive_height:
                best_progressive_height = height or 0
                best_progressive_url = direct_url

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
        "stream_url": best_progressive_url,
        "progressive_options": progressive_options,
        "video_options": video_options,
        "audio_options": audio_options,
    }


def search_youtube(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search YouTube and return basic metadata for each result (flat, fast).

    Uses the ``ytsearch<limit>:<query>`` pseudo-URL with ``extract_flat=True`` so
    yt-dlp only resolves each entry's basic metadata (id, title, duration, thumbnail)
    without fetching the full format list for every result. This keeps search responsive.

    Args:
        query: Free-text search terms.
        limit: Maximum number of results to return (default 10).

    Returns:
        A list of dictionaries, each with:
            id, title, uploader, duration, thumbnail, url.

    Raises:
        ExtractionError: If the query is empty or the search fails.
    """
    if not query or not isinstance(query, str) or not query.strip():
        raise ExtractionError("A valid search query must be provided.")

    clamped_limit = max(1, min(int(limit), 50))
    search_target = f"ytsearch{clamped_limit}:{query.strip()}"

    ydl_opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_target, download=False)
    except DownloadError as exc:
        raise ExtractionError(f"Search failed: {exc}") from exc
    except Exception as exc:
        raise ExtractionError(f"Unexpected search error: {exc}") from exc

    entries: List[Dict[str, Any]] = (info or {}).get("entries") or []

    results: List[Dict[str, Any]] = []
    for entry in entries:
        if not entry:
            continue
        video_id = entry.get("id") or ""
        results.append({
            "id": video_id,
            "title": entry.get("title") or "Untitled",
            "uploader": entry.get("uploader") or entry.get("channel") or "",
            "duration": entry.get("duration"),
            "thumbnail": entry.get("thumbnail") or "",
            "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else (entry.get("url") or ""),
        })

    return results


def extract_stream_url(url: str) -> Dict[str, Any]:
    """Extract a directly-playable progressive (muxed) stream URL for a video.

    Selects the best format that contains BOTH video and audio (a progressive /
    muxed stream) so it can be played directly in an HTML5 ``<video>`` element.

    Args:
        url: The YouTube video URL.

    Returns:
        A dictionary with ``stream_url`` (direct URL or None) and ``title``.

    Raises:
        ExtractionError: If the URL is empty or extraction fails.
    """
    if not url or not isinstance(url, str) or not url.strip():
        raise ExtractionError("A valid YouTube URL must be provided.")

    ydl_opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        # Best progressive (video+audio) stream; fall back to any single best.
        "format": "best[acodec!=none][vcodec!=none]/best",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False)
    except DownloadError as exc:
        raise ExtractionError(f"Failed to resolve stream URL: {exc}") from exc
    except Exception as exc:
        raise ExtractionError(f"Unexpected stream resolution error: {exc}") from exc

    if not info:
        raise ExtractionError("No stream information could be retrieved.")

    return {
        "stream_url": info.get("url"),
        "title": info.get("title") or "",
    }
