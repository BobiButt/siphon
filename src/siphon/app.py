"""FastAPI application factory for Siphon."""

from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def create_app(frontend_dir: Optional[Path] = None) -> FastAPI:
    """Create and configure the FastAPI application instance.

    Sets up health and status routes, then mounts the static frontend
    directory at the root route `/`.
    """
    app = FastAPI(
        title="Siphon",
        version="0.1.0",
        description="Backend API for Siphon YouTube Downloader",
    )

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint confirming backend availability."""
        return {"status": "ok", "app": "siphon"}

    # Resolve frontend directory path
    if frontend_dir is None:
        frontend_dir = Path(__file__).resolve().parents[2] / "frontend"

    if frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    return app
