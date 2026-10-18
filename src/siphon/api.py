"""FastAPI router for Siphon API endpoints."""

from pathlib import Path
import shutil
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from siphon.downloader import DownloadResult, MuxingError, download_media, mux_streams
from siphon.extractors import (
    ExtractionError,
    extract_stream_url,
    extract_video_info,
    search_youtube,
)

router = APIRouter()


class DownloadRequest(BaseModel):
    """Schema for media download request."""
    url: str = Field(..., description="YouTube video or media URL")
    format_id: str = Field(..., description="Target stream format ID")
    output_dir: str = Field(..., description="Directory where final output file will be saved")


@router.get("/info", response_model=Dict[str, Any])
async def get_video_info(url: str = Query(..., description="YouTube video URL to inspect")) -> Dict[str, Any]:
    """Retrieve metadata and stream format options for a YouTube video URL.

    Returns:
        Structured dictionary containing video metadata and separated formats.

    Raises:
        HTTPException: 400 Bad Request if the URL is invalid or extraction fails.
    """
    if not url.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'url' must not be empty.")

    try:
        info = extract_video_info(url)
        return info
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unexpected error inspecting URL: {exc}")


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_videos(
    q: str = Query(..., min_length=1, description="YouTube search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
) -> List[Dict[str, Any]]:
    """Search YouTube and return basic metadata for each result (flat, fast).

    Uses yt-dlp's ``extract_flat`` mode so only light-weight metadata is resolved
    per entry (no per-result format extraction), keeping search responsive.

    Returns:
        List of ``{id, title, uploader, duration, thumbnail, url}`` dictionaries.

    Raises:
        HTTPException: 400 Bad Request if the query is empty or search fails.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' must not be empty.")

    try:
        return search_youtube(q, limit=limit)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unexpected search error: {exc}")


@router.get("/stream", response_model=Dict[str, Any])
async def get_stream_url(
    url: str = Query(..., description="YouTube video URL to resolve a direct stream for"),
) -> Dict[str, Any]:
    """Resolve a directly-playable progressive (muxed) stream URL for a video.

    Returns:
        Dict with ``stream_url`` (direct URL, or None when no progressive stream
        exists) and ``title``. Feed ``stream_url`` into an HTML5 ``<video>`` element.

    Raises:
        HTTPException: 400 Bad Request if the URL is empty or extraction fails.
    """
    if not url.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'url' must not be empty.")

    try:
        return extract_stream_url(url)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unexpected error resolving stream: {exc}")


@router.post("/download")
async def execute_download(payload: DownloadRequest) -> Dict[str, Any]:
    """Execute media download and muxing pipeline for requested stream.

    Downloads streams via yt-dlp. If the stream is a DASH video stream,
    automatically downloads matching audio and muxes using bundled static FFmpeg.

    Returns:
        JSON response with status and final output path.
    """
    url = payload.url.strip()
    format_id = payload.format_id.strip()
    output_dir = Path(payload.output_dir.strip())

    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")
    if not format_id:
        raise HTTPException(status_code=400, detail="format_id cannot be empty.")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid output directory: {exc}")

    try:
        # Step 1: Download stream(s) via yt-dlp
        result: DownloadResult = download_media(url=url, format_id=format_id, output_dir=output_dir)

        # Step 2: Handle DASH video muxing or single-stream placement
        if result.is_dash and result.video_path and result.audio_path:
            raw_title = result.get("title") or result.get("video_id") or "video"
            safe_title = "".join(c for c in raw_title if c.isalnum() or c in (" ", "_", "-")).strip()
            ext = result.get("ext") or "mp4"
            final_output_path = output_dir / f"{safe_title}.{ext}"

            # Mux streams using bundled FFmpeg
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

        # Single progressive video or audio stream
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
        raise HTTPException(status_code=500, detail=f"Download pipeline failed: {exc}")
