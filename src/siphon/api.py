"""FastAPI router for Siphon API endpoints."""

import logging
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from siphon.downloader import DownloadResult, MuxingError, download_media, mux_streams
from siphon.extractors import (
    ExtractionError,
    extract_stream_url,
    extract_video_info,
    search_youtube,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# --- /proxy settings ---------------------------------------------------------
# Only these hosts may be proxied (the proxy must not become an open relay).
PROXY_ALLOWED_HOST_SUFFIXES = (".googlevideo.com", ".youtube.com", ".ytimg.com", ".googleusercontent.com")
# YouTube rejects/throttles huge open-ended ranges; fetch in bounded pieces like yt-dlp does.
PROXY_CHUNK_SIZE = 8 * 1024 * 1024
PROXY_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


class DownloadRequest(BaseModel):
    """Schema for media download request."""
    url: str = Field(..., description="YouTube video or media URL")
    format_id: str = Field(..., description="Target stream format ID")
    output_dir: str = Field(..., description="Directory where final output file will be saved")


@router.get("/info", response_model=Dict[str, Any])
async def get_video_info(url: str = Query(..., description="YouTube video URL to inspect")) -> Dict[str, Any]:
    if not url.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'url' must not be empty.")
    try:
        return extract_video_info(url)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in /info")
        raise HTTPException(status_code=400, detail=f"Unexpected error inspecting URL: {exc}")


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_videos(
    q: str = Query(..., min_length=1, description="YouTube search query"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
) -> List[Dict[str, Any]]:
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' must not be empty.")
    try:
        return search_youtube(q, limit=limit)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in /search for query: %s", q)
        raise HTTPException(status_code=400, detail=f"Unexpected search error: {exc}")


@router.get("/stream", response_model=Dict[str, Any])
async def get_stream_url(
    url: str = Query(..., description="YouTube video URL to resolve a direct stream for"),
    format_id: Optional[str] = Query(None, description="Optional format id or height (e.g. '720') to stream"),
) -> Dict[str, Any]:
    if not url.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'url' must not be empty.")
    try:
        return extract_stream_url(url, format_id=format_id)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in /stream")
        raise HTTPException(status_code=400, detail=f"Unexpected error resolving stream: {exc}")


def _check_proxy_target(url: str) -> None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not host:
        raise HTTPException(status_code=400, detail="Invalid proxy URL.")
    if not host.endswith(PROXY_ALLOWED_HOST_SUFFIXES):
        raise HTTPException(status_code=403, detail=f"Host not allowed for proxying: {host}")


def _upstream_range(range_header: Optional[str]) -> str:
    """Translate the browser's Range header into a bounded range for YouTube."""
    if not range_header:
        return f"bytes=0-{PROXY_CHUNK_SIZE - 1}"
    match = _RANGE_RE.match(range_header.strip())
    if not match or (not match.group(1) and not match.group(2)):
        return range_header  # multi-range or unusual form: pass through untouched
    start, end = match.group(1), match.group(2)
    if not start:            # suffix range "bytes=-N" (last N bytes): pass through
        return range_header
    start_i = int(start)
    max_end = start_i + PROXY_CHUNK_SIZE - 1
    end_i = min(int(end), max_end) if end else max_end
    return f"bytes={start_i}-{end_i}"


@router.get("/proxy")
async def proxy_stream(request: Request, url: str = Query(...)):
    """Proxy a YouTube media URL to the embedded player (adds headers, handles Range)."""
    _check_proxy_target(url)

    headers = {
        "User-Agent": PROXY_USER_AGENT,
        "Referer": "https://www.youtube.com/",
        "Origin": "https://www.youtube.com",
        "Accept": "*/*",
        "Accept-Encoding": "identity",  # never hand the player a compressed stream
        "Range": _upstream_range(request.headers.get("range")),
    }

    # follow_redirects: googlevideo often redirects to a different edge host
    client = httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(15.0, read=60.0),
    )
    try:
        upstream = await client.send(client.build_request("GET", url, headers=headers), stream=True)
    except httpx.HTTPError as exc:
        await client.aclose()
        logger.warning("Proxy could not reach upstream: %s", exc)
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc}")

    if upstream.status_code >= 400 and upstream.status_code != 416:
        body = (await upstream.aread())[:200]
        await upstream.aclose()
        await client.aclose()
        logger.warning("Proxy upstream returned HTTP %s: %r", upstream.status_code, body)
        raise HTTPException(
            status_code=502,
            detail=f"YouTube refused the stream request (HTTP {upstream.status_code}). "
                   "The link may have expired - reload the video.",
        )

    async def stream_generator():
        try:
            async for chunk in upstream.aiter_raw():
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    resp_headers = {"Accept-Ranges": "bytes"}
    for name in ("content-length", "content-range", "content-type"):
        if name in upstream.headers:
            resp_headers[name] = upstream.headers[name]

    return StreamingResponse(
        stream_generator(),
        status_code=upstream.status_code,
        headers=resp_headers,
    )


@router.post("/download")
async def execute_download(payload: DownloadRequest) -> Dict[str, Any]:
    url = payload.url.strip()
    format_id = payload.format_id.strip()
    output_dir = Path(payload.output_dir.strip()).expanduser()

    if not url or not format_id:
        raise HTTPException(status_code=400, detail="URL and format_id cannot be empty.")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid output directory: {exc}")

    try:
        result: DownloadResult = download_media(url=url, format_id=format_id, output_dir=output_dir)

        if result.is_dash and result.video_path and result.audio_path:
            raw_title = result.get("title") or result.get("video_id") or "video"
            safe_title = "".join(c for c in raw_title if c.isalnum() or c in (" ", "_", "-")).strip()
            ext = result.get("ext") or "mp4"
            final_output_path = output_dir / f"{safe_title}.{ext}"

            muxed_path = mux_streams(
                video_path=result.video_path,
                audio_path=result.audio_path,
                output_path=final_output_path,
            )
            return {
                "status": "ok",
                "message": "Download and muxing completed",
                "output_path": str(muxed_path),
            }

        source_file = result.video_path or result.audio_path
        if not source_file:
            raise ExtractionError("Download completed without output file.")

        final_output_path = output_dir / source_file.name
        if source_file != final_output_path:
            shutil.move(str(source_file), str(final_output_path))

        return {
            "status": "ok",
            "message": "Download completed",
            "output_path": str(final_output_path),
        }

    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except MuxingError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error in /download")
        raise HTTPException(status_code=500, detail=f"Download pipeline failed: {exc}")