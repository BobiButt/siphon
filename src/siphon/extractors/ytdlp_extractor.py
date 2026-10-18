"""yt-dlp extraction engine for Siphon."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yt_dlp
from yt_dlp.utils import DownloadError


class ExtractionError(Exception):
    """Raised when media metadata or format extraction fails."""
    pass

BOT_CHECK_GUIDANCE = (
    "YouTube requires authentication. Siphon tried to bypass this automatically, but failed. "
    "Please ensure you are logged into YouTube in your browser (Firefox/Chrome), or export "
    "a cookies.txt file to ~/.config/siphon/cookies.txt."
)

def get_cookies_path() -> Path:
    return Path("~/.config/siphon/cookies.txt").expanduser()

def _build_ydl_opts(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
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
    if extra:
        opts.update(extra)
    return opts

def _is_bot_check_error(message: str) -> bool:
    lowered = message.lower()
    return "not a bot" in lowered or "sign in to confirm" in lowered

def _to_extraction_error(context: str, exc: DownloadError) -> ExtractionError:
    if _is_bot_check_error(str(exc)):
        return ExtractionError(BOT_CHECK_GUIDANCE)
    return ExtractionError(f"{context}: {exc}")

def extract_video_info(url: str) -> Dict[str, Any]:
    if not url or not isinstance(url, str) or not url.strip():
        raise ExtractionError("A valid YouTube URL must be provided.")

    ydl_opts: Dict[str, Any] = _build_ydl_opts({"extract_flat": False})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False)
    except DownloadError as exc:
        raise _to_extraction_error("Failed to extract video information", exc) from exc
    except Exception as exc:
        raise ExtractionError(f"Unexpected extraction error: {exc}") from exc

    if not info:
        raise ExtractionError("No video information could be retrieved.")

    title: str = info.get("title") or ""
    duration: Optional[int] = info.get("duration")
    thumbnail: str = info.get("thumbnail") or ""
    uploader: str = info.get("uploader") or info.get("channel") or ""
    video_id: str = info.get("id") or ""

    formats: List[Dict[str, Any]] = info.get("formats") or []
    progressive_options: List[Dict[str, Any]] = []
    video_options: List[Dict[str, Any]] = []
    audio_options: List[Dict[str, Any]] = []

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

        if vcodec and vcodec != "none" and acodec and acodec != "none":
            quality = f"{height}p" if height else (format_note or f.get("resolution") or "progressive")
            progressive_options.append({
                "quality": quality, "format_id": format_id, "ext": ext, "filesize": filesize,
            })
            direct_url = f.get("url")
            if direct_url and (height or 0) > best_progressive_height:
                best_progressive_height = height or 0
                best_progressive_url = direct_url

        elif vcodec and vcodec != "none" and (not acodec or acodec == "none"):
            quality = f"{height}p" if height else (format_note or f.get("resolution") or "video")
            video_options.append({
                "quality": quality, "format_id": format_id, "ext": ext, "filesize": filesize,
            })

        elif acodec and acodec != "none" and (not vcodec or vcodec == "none"):
            abr = f.get("abr") or f.get("tbr")
            bitrate = f"{int(abr)} kbps" if abr else (format_note or "audio")
            audio_options.append({
                "bitrate": bitrate, "format_id": format_id, "ext": ext, "filesize": filesize,
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

def search_youtube(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    if not query or not isinstance(query, str) or not query.strip():
        raise ExtractionError("A valid search query must be provided.")

    clamped_limit = max(1, min(int(limit), 50))
    
    ydl_opts: Dict[str, Any] = _build_ydl_opts({
        "extract_flat": "in_playlist", 
        "playlistend": clamped_limit,
    })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{clamped_limit}:{query.strip()}", download=False)
    except DownloadError as exc:
        raise _to_extraction_error("Search failed", exc) from exc
    except Exception as exc:
        raise ExtractionError(f"Unexpected search error: {exc}") from exc

    entries: List[Dict[str, Any]] = (info or {}).get("entries") or []
    results: List[Dict[str, Any]] = []

    for entry in entries:
        if not entry: continue
        video_id = entry.get("id") or ""
        
        if not video_id or len(video_id) != 11: 
            continue
            
        thumbnail_url = entry.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"

        # FIX: Try to grab exact date, fallback to relative text, fallback to Unknown
        upload_date = entry.get("upload_date")
        if not upload_date and entry.get("timestamp"):
            import datetime
            upload_date = datetime.datetime.fromtimestamp(entry["timestamp"]).strftime("%Y-%m-%d")
        if not upload_date:
            upload_date = "Unknown"

        results.append({
            "id": video_id,
            "title": entry.get("title") or "Untitled",
            "uploader": entry.get("uploader") or entry.get("channel") or "",
            "duration": entry.get("duration"),
            "upload_date": upload_date,
            "thumbnail": thumbnail_url,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        })

    return results

# ... (keep imports and previous functions) ...

# ... (keep previous code) ...
def extract_stream_url(url: str, format_id: Optional[str] = None) -> Dict[str, Any]:
    if not url or not isinstance(url, str) or not url.strip():
        raise ExtractionError("A valid YouTube URL must be provided.")

    # FORCE MP4 ONLY. Qt cannot play WebM/VP9.
    if format_id:
        target_format = f"{format_id}[ext=mp4]/18[ext=mp4]"
    else:
        target_format = "22[ext=mp4]/18[ext=mp4]"
    
    ydl_opts: Dict[str, Any] = _build_ydl_opts({
        "format": target_format,
    })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False)
    except DownloadError as exc:
        raise _to_extraction_error("Failed to resolve stream URL", exc) from exc
    except Exception as exc:
        raise ExtractionError(f"Unexpected stream resolution error: {exc}") from exc

    if not info:
        raise ExtractionError("No stream information could be retrieved.")

    height = info.get("height")
    quality = f"{height}p" if height else "360p"

    return {
        "stream_url": info.get("url"),
        "title": info.get("title") or "",
        "quality": quality,
    }