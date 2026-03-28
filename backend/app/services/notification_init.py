"""Notification settings initialization.

Ensures default notification settings exist in the database on startup.
FamilyCircle's Setting model is simple key/value with optional family_id,
so we just insert missing keys with default values.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import DEFAULT_EVENT_REMINDER_DAYS
from app.models import Setting

logger = logging.getLogger(__name__)

# Default notification settings (global, family_id=NULL)
# These are inserted on startup if they don't exist.
# User-modified values are never overwritten.
DEFAULT_NOTIFICATION_SETTINGS: dict[str, str] = {
    # Global retry settings
    "notification_retry_attempts": "3",
    "notification_retry_delay": "2.0",
    # ntfy
    "ntfy_enabled": "false",
    "ntfy_server": "",
    "ntfy_topic": "familycircle",
    "ntfy_token": "",
    # Gotify
    "gotify_enabled": "false",
    "gotify_server": "",
    "gotify_token": "",
    # Pushover
    "pushover_enabled": "false",
    "pushover_user_key": "",
    "pushover_api_token": "",
    # Slack
    "slack_enabled": "false",
    "slack_webhook_url": "",
    # Discord
    "discord_enabled": "false",
    "discord_webhook_url": "",
    # Telegram
    "telegram_enabled": "false",
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    # Email notifications (reuses existing SMTP settings, just needs toggle + recipient)
    "notification_email_enabled": "false",
    "notification_email_to": "",
    # Per-event notification toggles
    "notify_event_created": "true",
    "notify_event_updated": "false",
    "notify_event_cancelled": "true",
    "notify_event_reminder": "true",
    "notify_rsvp_received": "false",
    "notify_poll_created": "true",
    "notify_poll_closing_soon": "true",
    "notify_comment_added": "false",
    "notify_comment_mention": "true",
    "notify_family_member_joined": "true",
    # Event reminder configuration
    "event_reminder_days": str(DEFAULT_EVENT_REMINDER_DAYS),
}


async def initialize_notification_settings(db: AsyncSession) -> None:
    """Initialize default notification settings if they don't exist.

    Only inserts new settings — never overwrites existing values.
    """
    logger.info("Checking notification settings...")

    settings_added = 0

    for key, default_value in DEFAULT_NOTIFICATION_SETTINGS.items():
        result = await db.execute(
            select(Setting).where(Setting.key == key, Setting.family_id.is_(None))
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            db.add(Setting(key=key, value=default_value, family_id=None))
            settings_added += 1

    if settings_added > 0:
        await db.commit()
        logger.info("Added %d notification settings", settings_added)
    else:
        logger.info("All notification settings already present")
