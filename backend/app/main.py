"""FamilyCircle - Main FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import auth, events, family, health, potluck, profile, secret_santa, settings, wishlist
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    yield
    # Shutdown (if needed)


app = FastAPI(
    title="FamilyCircle",
    description="Family event coordination platform",
    version=__version__,
    lifespan=lifespan,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(family.router, prefix="/api/family", tags=["family"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(potluck.router, prefix="/api/potluck", tags=["potluck"])
app.include_router(secret_santa.router, prefix="/api/secret-santa", tags=["secret-santa"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(wishlist.router, prefix="/api/wishlist", tags=["wishlist"])

# Serve static frontend files in production
# In container: /app/app/main.py -> /app/static
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA for all non-API routes."""
        # Check if it's an API route
        if full_path.startswith("api/"):
            return {"detail": "Not found"}

        # Check if file exists in static
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # Return index.html for SPA routing
        return FileResponse(STATIC_DIR / "index.html")
