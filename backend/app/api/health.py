"""Health check endpoints."""

from fastapi import APIRouter

from app import __version__

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": __version__}


@router.get("/version")
async def get_version():
    """Get application version."""
    return {"version": __version__}
