"""Application configuration."""

import ipaddress
import logging
import os
from pathlib import Path

from starlette.requests import Request

logger = logging.getLogger(__name__)

# Database path - only env var needed before DB is available
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "/data/familycircle.db"))

# Server configuration
PORT = int(os.getenv("PORT", "8080"))
HOST = os.getenv("HOST", "0.0.0.0")

# Debug / production mode
IS_DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")

# Canonical base URL for emails and links — required in production
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

# Trusted proxy CIDRs for rate limiting — parsed at import time, malformed values fail fast
_raw_cidrs = os.getenv("TRUSTED_PROXY_CIDRS", "")
TRUSTED_PROXY_NETWORKS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
for _cidr in (s.strip() for s in _raw_cidrs.split(",") if s.strip()):
    try:
        TRUSTED_PROXY_NETWORKS.append(ipaddress.ip_network(_cidr, strict=False))
    except ValueError:
        logger.critical("Invalid CIDR in TRUSTED_PROXY_CIDRS: '%s'", _cidr)
        raise SystemExit(1)

# Ensure data directory exists
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def validate_production_config() -> None:
    """Validate configuration required in production. Call at startup."""
    if not IS_DEBUG and not PUBLIC_BASE_URL:
        logger.critical(
            "PUBLIC_BASE_URL must be set in production "
            "(e.g., 'https://familycircle.example.com'). "
            "Set DEBUG=true to use request-derived URLs in development."
        )
        raise SystemExit(1)


def get_base_url(request: Request) -> str:
    """Get canonical base URL for email links.

    Uses PUBLIC_BASE_URL if set, falls back to request-derived URL in debug mode only.
    """
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL
    # Debug mode fallback — only reachable if validate_production_config() passed
    return str(request.base_url).rstrip("/")
