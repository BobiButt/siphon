"""FastAPI router for Siphon API endpoints."""

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    format_id: Optional[str] = Query(None, description="Optional specific format ID to stream"),
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

@router.get("/proxy")
async def proxy_stream(request: Request, url: str = Query(...)):
    """Proxy video stream from YouTube to bypass CORS/Header restrictions in Qt WebEngine."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.youtube.com/",
        "Accept-Encoding": "identity", # Prevent compressed stream which Qt cannot decode
    }
    
    # Forward the Range header from Qt to YouTube (Crucial for video seeking/playing)
    if "range" in request.headers:
        headers["Range"] = request.headers["range"]

    # follow_redirects=True is CRITICAL because YouTube often redirects video URLs
    client = httpx.AsyncClient(follow_redirects=True)
    req = client.build_request("GET", url, headers=headers)
    response = await client.send(req, stream=True)

    async def stream_generator():
        try:
            async for chunk in response.aiter_bytes():
                yield chunk
        finally:
            await response.aclose()
            await client.aclose()

    # Pass through headers from YouTube to Qt
    resp_headers = {}
    for h in ["content-length", "content-range", "accept-ranges", "content-type"]:
        if h in response.headers:
            resp_headers[h] = response.headers[h]

    return StreamingResponse(
        stream_generator(), 
        status_code=response.status_code, 
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