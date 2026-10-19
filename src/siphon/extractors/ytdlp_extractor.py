"""yt-dlp extraction engine for Siphon."""

import datetime
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
        if not entry:
            continue
        video_id = entry.get("id") or ""

        if not video_id or len(video_id) != 11:
            continue

        thumbnail_url = entry.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"

        upload_date = entry.get("upload_date")
        if not upload_date and entry.get("timestamp"):
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


# ---------------------------------------------------------------------------
# Streaming (in-app playback)
# ---------------------------------------------------------------------------
DEFAULT_STREAM_HEIGHT = 720
_HTTP_PROTOCOLS = {"http", "https"}
_STANDARD_HEIGHTS = {144, 240, 360, 480, 720, 1080, 1440, 2160, 4320}

_VIDEO_CODEC_RANK = (("vp9", 0), ("vp09", 0), ("av01", 1), ("vp8", 2))
_AUDIO_CODEC_PREFIXES = ("opus", "vorbis")


def _norm_codec(value: Optional[str]) -> str:
    return (value or "none").lower()


def _is_direct_http(fmt: Dict[str, Any]) -> bool:
    protocol = (fmt.get("protocol") or "https").lower()
    return bool(fmt.get("url")) and protocol in _HTTP_PROTOCOLS


def _video_codec_rank(fmt: Dict[str, Any]) -> Optional[int]:
    vcodec = _norm_codec(fmt.get("vcodec"))
    for prefix, rank in _VIDEO_CODEC_RANK:
        if vcodec.startswith(prefix):
            return rank
    return None


def _playable_video_formats(formats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        f for f in formats
        if _is_direct_http(f)
        and _norm_codec(f.get("acodec")) == "none"
        and _video_codec_rank(f) is not None
        and (f.get("height") or 0) > 0
    ]


def _playable_audio_formats(formats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        f for f in formats
        if _is_direct_http(f)
        and _norm_codec(f.get("vcodec")) == "none"
        and _norm_codec(f.get("acodec")).startswith(_AUDIO_CODEC_PREFIXES)
    ]


def _resolve_target_height(formats: List[Dict[str, Any]], format_id: Optional[str]) -> Optional[int]:
    if not format_id:
        return None
    wanted = str(format_id).strip()
    for f in formats:
        if str(f.get("format_id")) == wanted and f.get("height"):
            return int(f["height"])
    text = wanted.lower().rstrip("p")
    if text.isdigit() and int(text) in _STANDARD_HEIGHTS:
        return int(text)
    return None


def pick_playable_streams(
    formats: List[Dict[str, Any]],
    format_id: Optional[str] = None,
    default_height: int = DEFAULT_STREAM_HEIGHT,
) -> Dict[str, Any]:
    videos = _playable_video_formats(formats)
    audios = _playable_audio_formats(formats)
    heights = sorted({int(f["height"]) for f in videos})

    video: Optional[Dict[str, Any]] = None
    if videos:
        target = _resolve_target_height(formats, format_id) or default_height
        not_above = [h for h in heights if h <= target]
        chosen_height = max(not_above) if not_above else min(heights)
        at_height = [f for f in videos if int(f["height"]) == chosen_height]
        video = min(at_height, key=lambda f: (_video_codec_rank(f), -(f.get("tbr") or 0)))

    audio: Optional[Dict[str, Any]] = None
    if audios:
        audio = max(
            audios,
            key=lambda f: (f.get("language_preference") or 0, f.get("abr") or f.get("tbr") or 0),
        )

    return {"video": video, "audio": audio, "heights": heights}


def _pick_muxed_fallback(formats: List[Dict[str, Any]], default_height: int) -> Optional[Dict[str, Any]]:
    muxed = [
        f for f in formats
        if _is_direct_http(f)
        and _norm_codec(f.get("vcodec")) != "none"
        and _norm_codec(f.get("acodec")) != "none"
    ]
    if not muxed:
        return None
    not_above = [f for f in muxed if (f.get("height") or 0) <= default_height]
    pool = not_above or muxed
    return max(pool, key=lambda f: f.get("height") or 0)


def extract_stream_url(url: str, format_id: Optional[str] = None) -> Dict[str, Any]:
    if not url or not isinstance(url, str) or not url.strip():
        raise ExtractionError("A valid YouTube URL must be provided.")

    ydl_opts: Dict[str, Any] = _build_ydl_opts({"ignoreerrors": False})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False)
    except DownloadError as exc:
        raise _to_extraction_error("Failed to resolve stream URL", exc) from exc
    except Exception as exc:
        raise ExtractionError(f"Unexpected stream resolution error: {exc}") from exc

    if not info:
        raise ExtractionError("No stream information could be retrieved.")

    formats: List[Dict[str, Any]] = info.get("formats") or []
    picked = pick_playable_streams(formats, format_id=format_id)
    video, audio = picked["video"], picked["audio"]

    result: Dict[str, Any] = {
        "title": info.get("title") or "",
        "duration": info.get("duration"),
        "heights": picked["heights"],
    }

    if video:
        height = int(video["height"])
        result.update({
            "stream_url": video["url"],
            "audio_url": audio["url"] if audio else None,
            "separate_audio": audio is not None,
            "quality": f"{height}p",
            "height": height,
            "vcodec": video.get("vcodec"),
            "acodec": audio.get("acodec") if audio else None,
            "container": video.get("ext") or "webm",
        })
        if audio is None:
            result["warning"] = "No Opus audio stream was found; video will play without sound."
        return result

    muxed = _pick_muxed_fallback(formats, DEFAULT_STREAM_HEIGHT)
    if not muxed:
        raise ExtractionError("No playable stream found for this video.")
    height = muxed.get("height")
    result.update({
        "stream_url": muxed["url"],
        "audio_url": None,
        "separate_audio": False,
        "quality": f"{height}p" if height else "360p",
        "height": height,
        "vcodec": muxed.get("vcodec"),
        "acodec": muxed.get("acodec"),
        "container": muxed.get("ext") or "mp4",
        "warning": "Only H.264/AAC streams are available; the embedded player may not be able to decode them.",
    })
    return result