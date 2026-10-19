"""FastAPI application factory for Siphon."""

import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from siphon.api import router as api_router
from siphon.downloader import check_ffmpeg_or_warn
import sys

logger = logging.getLogger(__name__)


def create_app(frontend_dir: Optional[Path] = None) -> FastAPI:
    app = FastAPI(
        title="Siphon",
        version="0.2.1",
        description="Backend API for Siphon YouTube Clone",
    )

    check_ffmpeg_or_warn()

    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "ok", "app": "siphon"}

    app.include_router(api_router, prefix="/api")

    if frontend_dir is None:
        # PyInstaller ONEDIR puts files in the _internal folder (sys._MEIPASS)
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).resolve().parents[2]
        frontend_dir = base_path / "frontend"

    print(f"DEBUG: Looking for frontend at: {frontend_dir}")

    if frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    else:
        print(f"ERROR: Frontend not found! Available files in {base_path}: {list(base_path.iterdir())}")

    return app