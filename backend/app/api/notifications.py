"""Notification configuration API endpoints.

Super admin only — manages global notification service configuration
and per-event notification toggles.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.api.settings import get_global_setting, set_global_setting
from app.db import get_db_session
from app.models import User
from app.services.notifications.discord import DiscordNotificationService
from app.services.notifications.email_service import EmailNotificationService
from app.services.notifications.gotify import GotifyNotificationService
from app.services.notifications.ntfy import NtfyNotificationService
from app.services.notifications.pushover import PushoverNotificationService
from app.services.notifications.slack import SlackNotificationService
from app.services.notifications.telegram import TelegramNotificationService
from app.services.permissions import permissions

logger = logging.getLogger(__name__)

router = APIRouter()

# Settings keys that contain sensitive values — returned masked
SENSITIVE_KEYS = {
    "ntfy_token",
    "gotify_token",
    "pushover_user_key",
    "pushover_api_token",
    "slack_webhook_url",
    "discord_webhook_url",
    "telegram_bot_token",
}

# All notification setting keys
NOTIFICATION_KEYS = [
    # Retry
    "notification_retry_attempts",
    "notification_retry_delay",
    # ntfy
    "ntfy_enabled",
    "ntfy_server",
    "ntfy_topic",
    "ntfy_token",
    # Gotify
    "gotify_enabled",
    "gotify_server",
    "gotify_token",
    # Pushover
    "pushover_enabled",
    "pushover_user_key",
    "pushover_api_token",
    # Slack
    "slack_enabled",
    "slack_webhook_url",
    # Discord
    "discord_enabled",
    "discord_webhook_url",
    # Telegram
    "telegram_enabled",
    "telegram_bot_token",
    "telegram_chat_id",
    # Email
    "notification_email_enabled",
    "notification_email_to",
    # Event toggles
    "notify_event_created",
    "notify_event_updated",
    "notify_event_cancelled",
    "notify_event_reminder",
    "notify_rsvp_received",
    "notify_poll_created",
    "notify_poll_closing_soon",
    "notify_comment_added",
    "notify_comment_mention",
    "notify_family_member_joined",
    # Reminder config
    "event_reminder_days",
]


def _require_super_admin(user: User) -> None:
    """Raise 403 if user is not super admin."""
    if not permissions.is_super_admin(user):
        raise HTTPException(
            status_code=403, detail="Only super admins can manage notification settings"
        )


@router.get("")
async def get_notification_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get all notification settings (super admin only).

    Sensitive values (tokens, webhooks) are masked.
    """
    _require_super_admin(user)

    result = {}
    for key in NOTIFICATION_KEYS:
        value = await get_global_setting(db, key) or ""
        if key in SENSITIVE_KEYS and value:
            result[key] = "********"
        else:
            result[key] = value

    # Also include SMTP configured status (email notifications reuse existing SMTP)
    smtp_host = await get_global_setting(db, "smtp_host")
    smtp_password = await get_global_setting(db, "smtp_password")
    result["smtp_configured"] = bool(smtp_host and smtp_password)

    return {"settings": result}


class UpdateNotificationSettingsRequest(BaseModel):
    """Update notification settings request.

    All fields optional — only provided fields are updated.
    """

    # Retry
    notification_retry_attempts: str | None = None
    notification_retry_delay: str | None = None
    # ntfy
    ntfy_enabled: str | None = None
    ntfy_server: str | None = None
    ntfy_topic: str | None = None
    ntfy_token: str | None = None
    # Gotify
    gotify_enabled: str | None = None
    gotify_server: str | None = None
    gotify_token: str | None = None
    # Pushover
    pushover_enabled: str | None = None
    pushover_user_key: str | None = None
    pushover_api_token: str | None = None
    # Slack
    slack_enabled: str | None = None
    slack_webhook_url: str | None = None
    # Discord
    discord_enabled: str | None = None
    discord_webhook_url: str | None = None
    # Telegram
    telegram_enabled: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    # Email
    notification_email_enabled: str | None = None
    notification_email_to: str | None = None
    # Event toggles
    notify_event_created: str | None = None
    notify_event_updated: str | None = None
    notify_event_cancelled: str | None = None
    notify_event_reminder: str | None = None
    notify_rsvp_received: str | None = None
    notify_poll_created: str | None = None
    notify_poll_closing_soon: str | None = None
    notify_comment_added: str | None = None
    notify_comment_mention: str | None = None
    notify_family_member_joined: str | None = None
    # Reminder config
    event_reminder_days: str | None = None


@router.put("")
async def update_notification_settings(
    request: UpdateNotificationSettingsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update notification settings (super admin only).

    Masked values (********) are ignored to avoid overwriting secrets.
    """
    _require_super_admin(user)

    updates = request.model_dump(exclude_none=True)
    updated_count = 0

    for key, value in updates.items():
        # Skip masked values — don't overwrite secrets with the mask
        if value == "********":
            continue
        await set_global_setting(db, key, value)
        updated_count += 1

    return {"message": f"Updated {updated_count} notification settings"}


class TestServiceRequest(BaseModel):
    """Request to test a notification service."""

    service: str  # ntfy, gotify, pushover, slack, discord, telegram, email


@router.post("/test")
async def test_notification_service(
    request: TestServiceRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Test a notification service by sending a test message (super admin only)."""
    _require_super_admin(user)

    service_name = request.service.lower()
    success = False
    message = "Unknown service"

    try:
        if service_name == "ntfy":
            server = await get_global_setting(db, "ntfy_server") or ""
            topic = await get_global_setting(db, "ntfy_topic") or "familycircle"
            token = await get_global_setting(db, "ntfy_token")
            if not server:
                return {"success": False, "message": "ntfy server URL not configured"}
            async with NtfyNotificationService(server, topic, token) as svc:
                success, message = await svc.test_connection()

        elif service_name == "gotify":
            server = await get_global_setting(db, "gotify_server") or ""
            token = await get_global_setting(db, "gotify_token") or ""
            if not server or not token:
                return {"success": False, "message": "Gotify server or token not configured"}
            async with GotifyNotificationService(server, token) as svc:
                success, message = await svc.test_connection()

        elif service_name == "pushover":
            user_key = await get_global_setting(db, "pushover_user_key") or ""
            api_token = await get_global_setting(db, "pushover_api_token") or ""
            if not user_key or not api_token:
                return {"success": False, "message": "Pushover credentials not configured"}
            async with PushoverNotificationService(user_key, api_token) as svc:
                success, message = await svc.test_connection()

        elif service_name == "slack":
            webhook_url = await get_global_setting(db, "slack_webhook_url") or ""
            if not webhook_url:
                return {"success": False, "message": "Slack webhook URL not configured"}
            async with SlackNotificationService(webhook_url) as svc:
                success, message = await svc.test_connection()

        elif service_name == "discord":
            webhook_url = await get_global_setting(db, "discord_webhook_url") or ""
            if not webhook_url:
                return {"success": False, "message": "Discord webhook URL not configured"}
            async with DiscordNotificationService(webhook_url) as svc:
                success, message = await svc.test_connection()

        elif service_name == "telegram":
            bot_token = await get_global_setting(db, "telegram_bot_token") or ""
            chat_id = await get_global_setting(db, "telegram_chat_id") or ""
            if not bot_token or not chat_id:
                return {"success": False, "message": "Telegram bot token or chat ID not configured"}
            async with TelegramNotificationService(bot_token, chat_id) as svc:
                success, message = await svc.test_connection()

        elif service_name == "email":
            smtp_host = await get_global_setting(db, "smtp_host") or ""
            smtp_port = int(await get_global_setting(db, "smtp_port") or "587")
            smtp_user = await get_global_setting(db, "smtp_username") or ""
            smtp_password = await get_global_setting(db, "smtp_password") or ""
            from_email = await get_global_setting(db, "smtp_from_email") or ""
            to_email = await get_global_setting(db, "notification_email_to") or ""
            use_tls = (await get_global_setting(db, "smtp_use_tls") or "true").lower() == "true"
            if not smtp_host or not smtp_password or not from_email:
                return {"success": False, "message": "SMTP not configured (check Settings > SMTP)"}
            if not to_email:
                return {"success": False, "message": "Notification email recipient not configured"}
            async with EmailNotificationService(
                smtp_host, smtp_port, smtp_user, smtp_password, from_email, to_email, use_tls
            ) as svc:
                success, message = await svc.test_connection()

        else:
            return {"success": False, "message": f"Unknown service: {service_name}"}

    except Exception as e:
        logger.error("Error testing %s: %s", service_name, e)
        return {"success": False, "message": f"Error: {str(e)}"}

    return {"success": success, "message": message}
