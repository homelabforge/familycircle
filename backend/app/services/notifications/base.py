"""Base class for notification services."""

import asyncio
import logging
from abc import ABC, abstractmethod
from types import TracebackType

import httpx

logger = logging.getLogger(__name__)


def safe_http_error(exc: Exception) -> str:
    """Describe an httpx error WITHOUT the secret-bearing request URL (CWE-532).

    Slack/Discord webhook URLs carry the secret in the path, Telegram embeds the
    bot token in the path, and gotify can carry a token in the query — and httpx
    puts the full request URL in ``str(exc)``. Return only the status (or error
    type) and the host, never the path/query, so notification error logs can't
    leak the destination's credentials.
    """
    if isinstance(exc, httpx.HTTPStatusError):
        detail = f"HTTP {exc.response.status_code}"
    else:
        detail = type(exc).__name__
    request = getattr(exc, "request", None)
    host = request.url.host if request is not None else "unknown"
    return f"{detail} (host={host})"


class NotificationService(ABC):
    """Abstract base class for all notification services."""

    service_name: str = "base"

    @abstractmethod
    async def send(
        self,
        title: str,
        message: str,
        priority: str = "default",
        tags: list[str] | None = None,
        url: str | None = None,
    ) -> bool:
        """Send a notification. Returns True on success."""
        pass

    async def send_with_retry(
        self,
        title: str,
        message: str,
        priority: str = "default",
        tags: list[str] | None = None,
        url: str | None = None,
        max_attempts: int = 3,
        retry_delay: float = 2.0,
    ) -> bool:
        """Send with simple retry logic for transient failures."""
        for attempt in range(max_attempts):
            try:
                if await self.send(title, message, priority, tags, url):
                    return True
            except Exception as e:
                logger.warning(
                    "[%s] Attempt %s/%s failed: %s",
                    self.service_name,
                    attempt + 1,
                    max_attempts,
                    safe_http_error(e),
                )

            if attempt < max_attempts - 1:
                await asyncio.sleep(retry_delay)

        logger.error("[%s] All %s attempts failed", self.service_name, max_attempts)
        return False

    @abstractmethod
    async def test_connection(self) -> tuple[bool, str]:
        """Test connection. Returns (success, message)."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        await self.close()
        return False
