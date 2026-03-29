"""FamilyCircle - Main FastAPI application."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import (
    auth,
    baby_shower_updates,
    calendar,
    event_comments,
    event_photos,
    event_templates,
    events,
    family,
    gift_exchange,
    health,
    notifications,
    poll_templates,
    polls,
    potluck,
    profile,
    registry,
    rsvp,
    settings,
    wishlist,
)
from app.db import init_db
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()

    # Initialize notification default settings
    from app.db import async_session_maker
    from app.services.notification_init import initialize_notification_settings

    async with async_session_maker() as db:
        await initialize_notification_settings(db)

    # Start background scheduler (event reminders)
    start_scheduler()

    yield

    # Shutdown
    stop_scheduler()


app = FastAPI(
    title="FamilyCircle",
    description="Family event coordination platform",
    version=__version__,
    lifespan=lifespan,
)

# CORS middleware — configurable via CORS_ORIGINS env var (comma-separated)
_default_origins = "http://localhost:5173,http://localhost:8080"
_cors_origins = [
    o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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
app.include_router(gift_exchange.router, prefix="/api/gift-exchange", tags=["gift-exchange"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(wishlist.router, prefix="/api/wishlist", tags=["wishlist"])
app.include_router(polls.router, prefix="/api/polls", tags=["polls"])
app.include_router(event_comments.router, prefix="/api/events", tags=["event-comments"])
app.include_router(event_photos.router, prefix="/api/events", tags=["event-photos"])
app.include_router(poll_templates.router, prefix="/api/poll-templates", tags=["poll-templates"])
app.include_router(calendar.router, prefix="/api", tags=["calendar"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(baby_shower_updates.router, prefix="/api/events", tags=["baby-shower-updates"])
app.include_router(registry.router, prefix="/api/events", tags=["registry"])
app.include_router(rsvp.router, prefix="/api/events", tags=["rsvp"])
app.include_router(event_templates.router, prefix="/api/event-templates", tags=["event-templates"])

# Serve uploaded files (photos)
UPLOAD_DIR = Path("/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

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

        # Check if file exists in static (resolve to prevent traversal)
        file_path = (STATIC_DIR / full_path).resolve()
        if file_path.is_relative_to(STATIC_DIR) and file_path.is_file():
            return FileResponse(file_path)

        # Return index.html for SPA routing
        return FileResponse(STATIC_DIR / "index.html")
