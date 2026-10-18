"""FastAPI application factory for Siphon."""

import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from siphon.api import router as api_router
from siphon.downloader import check_ffmpeg_or_warn

logger = logging.getLogger(__name__)


def create_app(frontend_dir: Optional[Path] = None) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title="Siphon",
        version="0.2.0",
        description="Backend API for Siphon YouTube Clone (Search, Stream, Download)",
    )

    check_ffmpeg_or_warn()

    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "ok", "app": "siphon"}

    # The /api/search route is handled by your api_router
    app.include_router(api_router, prefix="/api")

    # Resolve frontend directory path
    if frontend_dir is None:
        frontend_dir = Path(__file__).resolve().parents[2] / "frontend"

    if frontend_dir.is_dir():
        app.mount(
            "/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend"
        )

    return app