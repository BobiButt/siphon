"""FastAPI application factory for Siphon."""

from typing import Any


def create_app() -> Any:
    """Create and configure the FastAPI application instance.

    Stub implementation for project scaffolding.
    Full routing and endpoints will be implemented in Milestone 1.
    """
    try:
        from fastapi import FastAPI
        app = FastAPI(title="Siphon", version="0.1.0")
        return app
    except ImportError:
        # Fallback stub for environments where fastapi is not yet installed
        return None
