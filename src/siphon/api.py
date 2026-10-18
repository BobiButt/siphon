"""FastAPI router for Siphon API endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query
from siphon.extractors import ExtractionError, extract_video_info

router = APIRouter()


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
