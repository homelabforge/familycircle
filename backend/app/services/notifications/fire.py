"""Background notification helper — decouples notification dispatch from request lifecycle.

Uses FastAPI BackgroundTasks for lifecycle-managed execution.
Creates its own database session via async_session_maker so it never
reuses the request-scoped session.

Delivery guarantee: best-effort within a single request lifecycle.
If the app crashes mid-notification, the notification is lost.
This is acceptable for a family coordination app — notifications
are informational, not transactional.
"""

import logging

from app.db import async_session_maker
from app.services.notifications.dispatcher import NotificationDispatcher

logger = logging.getLogger(__name__)


async def send_notification_background(method_name: str, **kwargs) -> None:
    """Run notification dispatch with its own db session.

    Designed to be called via FastAPI BackgroundTasks:
        background_tasks.add_task(send_notification_background, "notify_event_created", ...)

    NOT via bare asyncio.create_task() — that drops silently on shutdown.
    """
    async with async_session_maker() as db:
        try:
            dispatcher = NotificationDispatcher(db)
            method = getattr(dispatcher, method_name)
            await method(**kwargs)
        except Exception:
            logger.error("Notification %s failed", method_name, exc_info=True)
