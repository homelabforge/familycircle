"""Rate limiting configuration with proxy-aware client identification.

Trust model:
- If TRUSTED_PROXY_CIDRS is set and request comes from a listed network,
  use X-Real-IP or X-Forwarded-For to identify the real client.
- Otherwise, use request.client.host directly (ignores forwarded headers).
- No TRUSTED_PROXY_CIDRS = always use direct client IP = safe default.
"""

import ipaddress
import logging

from slowapi import Limiter
from starlette.requests import Request

from app.config import TRUSTED_PROXY_NETWORKS

logger = logging.getLogger(__name__)


def _is_trusted_proxy(client_ip: str) -> bool:
    """Check if the client IP belongs to a trusted proxy network."""
    if not TRUSTED_PROXY_NETWORKS:
        return False
    try:
        addr = ipaddress.ip_address(client_ip)
    except ValueError:
        return False
    return any(addr in network for network in TRUSTED_PROXY_NETWORKS)


def get_client_ip(request: Request) -> str:
    """Extract the real client IP, respecting proxy trust boundaries."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    if _is_trusted_proxy(client_ip):
        # Trust forwarded headers from known proxies
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

    return client_ip


# Shared limiter instance — imported by main.py (middleware) and route modules (decorators)
limiter = Limiter(key_func=get_client_ip)
