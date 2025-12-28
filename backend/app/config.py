"""Application configuration."""

import os
from pathlib import Path

# Database path - only env var needed before DB is available
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "/data/familycircle.db"))

# Server configuration
PORT = int(os.getenv("PORT", "8080"))
HOST = os.getenv("HOST", "0.0.0.0")

# Ensure data directory exists
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
