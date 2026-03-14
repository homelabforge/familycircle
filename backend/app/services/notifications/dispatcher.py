"""Notification dispatcher for routing to enabled services."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.notifications.base import NotificationService
from app.services.notifications.discord import DiscordNotificationService
from app.services.notifications.email_service import EmailNotificationService
from app.services.notifications.gotify import GotifyNotificationService
from app.services.notifications.ntfy import NtfyNotificationService
from app.services.notifications.pushover import PushoverNotificationService
from app.services.notifications.slack import SlackNotificationService
from app.services.notifications.telegram import TelegramNotificationService
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

# FamilyCircle notification event types → settings key for per-event toggle
EVENT_SETTINGS_MAP: dict[str, str] = {
    "event_created": "notify_event_created",
    "event_updated": "notify_event_updated",
    "event_cancelled": "notify_event_cancelled",
    "event_reminder": "notify_event_reminder",
    "rsvp_received": "notify_rsvp_received",
    "poll_created": "notify_poll_created",
    "poll_closing_soon": "notify_poll_closing_soon",
    "comment_added": "notify_comment_added",
    "comment_mention": "notify_comment_mention",
    "family_member_joined": "notify_family_member_joined",
}

# Priority mapping for different event types
EVENT_PRIORITY_MAP: dict[str, str] = {
    "event_created": "default",
    "event_updated": "low",
    "event_cancelled": "high",
    "event_reminder": "default",
    "rsvp_received": "low",
    "poll_created": "default",
    "poll_closing_soon": "default",
    "comment_added": "low",
    "comment_mention": "default",
    "family_member_joined": "default",
}

# Tags mapping for different event types (emoji names for ntfy)
EVENT_TAGS_MAP: dict[str, list[str]] = {
    "event_created": ["calendar", "family"],
    "event_updated": ["pencil", "calendar"],
    "event_cancelled": ["warning", "calendar"],
    "event_reminder": ["bell", "calendar"],
    "rsvp_received": ["white_check_mark"],
    "poll_created": ["bar_chart"],
    "poll_closing_soon": ["hourglass"],
    "comment_added": ["speech_balloon"],
    "comment_mention": ["mega", "speech_balloon"],
    "family_member_joined": ["tada", "family"],
}


class NotificationDispatcher:
    """Routes notifications to enabled services with priority-based retry."""

    SERVICE_RETRY_MULTIPLIERS = {
        "discord": 1.5,
        "slack": 1.2,
        "telegram": 1.0,
        "ntfy": 1.0,
        "gotify": 1.0,
        "pushover": 1.0,
        "email": 2.0,
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._settings = SettingsService(db)

    async def _get_setting(self, key: str, default: str = "") -> str:
        """Get a global setting value."""
        return await self._settings.get_setting(key, default)

    async def _get_setting_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean setting value."""
        return await self._settings.get_setting_bool(key, default)

    async def _get_setting_int(self, key: str, default: int = 0) -> int:
        """Get an integer setting value."""
        return await self._settings.get_setting_int(key, default)

    async def _is_event_enabled(self, event_type: str) -> bool:
        """Check if an event type is enabled in settings."""
        if event_type not in EVENT_SETTINGS_MAP:
            return True

        event_key = EVENT_SETTINGS_MAP[event_type]

        # Check if any notification service is enabled at all
        if not await self._has_any_service_enabled():
            return False

        # Check specific event toggle
        return await self._get_setting_bool(event_key, default=True)

    async def _has_any_service_enabled(self) -> bool:
        """Check if at least one notification service is enabled."""
        services = [
            "ntfy_enabled",
            "gotify_enabled",
            "pushover_enabled",
            "slack_enabled",
            "discord_enabled",
            "telegram_enabled",
            "notification_email_enabled",
        ]
        for key in services:
            if await self._get_setting_bool(key, default=False):
                return True
        return False

    async def _get_enabled_services(self) -> list[NotificationService]:
        """Get list of enabled and configured notification services."""
        services: list[NotificationService] = []

        # ntfy
        if await self._get_setting_bool("ntfy_enabled", default=False):
            server = await self._get_setting("ntfy_server")
            topic = await self._get_setting("ntfy_topic", default="familycircle")
            api_key = await self._get_setting("ntfy_token")
            if server and topic:
                services.append(NtfyNotificationService(server, topic, api_key))

        # gotify
        if await self._get_setting_bool("gotify_enabled", default=False):
            server = await self._get_setting("gotify_server")
            token = await self._get_setting("gotify_token")
            if server and token:
                services.append(GotifyNotificationService(server, token))

        # pushover
        if await self._get_setting_bool("pushover_enabled", default=False):
            user_key = await self._get_setting("pushover_user_key")
            api_token = await self._get_setting("pushover_api_token")
            if user_key and api_token:
                services.append(PushoverNotificationService(user_key, api_token))

        # slack
        if await self._get_setting_bool("slack_enabled", default=False):
            webhook_url = await self._get_setting("slack_webhook_url")
            if webhook_url:
                services.append(SlackNotificationService(webhook_url))

        # discord
        if await self._get_setting_bool("discord_enabled", default=False):
            webhook_url = await self._get_setting("discord_webhook_url")
            if webhook_url:
                services.append(DiscordNotificationService(webhook_url))

        # telegram
        if await self._get_setting_bool("telegram_enabled", default=False):
            bot_token = await self._get_setting("telegram_bot_token")
            chat_id = await self._get_setting("telegram_chat_id")
            if bot_token and chat_id:
                services.append(TelegramNotificationService(bot_token, chat_id))

        # email (reuses existing SMTP settings from FamilyCircle)
        if await self._get_setting_bool("notification_email_enabled", default=False):
            smtp_host = await self._get_setting("smtp_host")
            smtp_port = await self._get_setting_int("smtp_port", default=587)
            smtp_user = await self._get_setting("smtp_username")
            smtp_password = await self._get_setting("smtp_password")
            from_email = await self._get_setting("smtp_from_email")
            to_email = await self._get_setting("notification_email_to")
            use_tls = await self._get_setting_bool("smtp_use_tls", default=True)
            if smtp_host and smtp_password and from_email and to_email:
                services.append(
                    EmailNotificationService(
                        smtp_host,
                        smtp_port,
                        smtp_user,
                        smtp_password,
                        from_email,
                        to_email,
                        use_tls,
                    )
                )

        return services

    async def dispatch(
        self,
        event_type: str,
        title: str,
        message: str,
        priority: str | None = None,
        tags: list[str] | None = None,
        url: str | None = None,
    ) -> dict[str, bool]:
        """Dispatch notification to all enabled services.

        Args:
            event_type: Type of event (e.g., "event_created", "poll_created")
            title: Notification title
            message: Notification message body
            priority: Optional priority override (min, low, default, high, urgent)
            tags: Optional tags override for ntfy
            url: Optional URL to include in notification

        Returns:
            Dict mapping service names to success status
        """
        results: dict[str, bool] = {}

        if not await self._is_event_enabled(event_type):
            logger.debug("Event type '%s' is disabled", event_type)
            return results

        services = await self._get_enabled_services()
        if not services:
            logger.debug("No notification services enabled")
            return results

        final_priority = priority or EVENT_PRIORITY_MAP.get(event_type, "default")
        final_tags = tags or EVENT_TAGS_MAP.get(event_type, [])

        max_attempts = await self._get_setting_int("notification_retry_attempts", default=3)
        base_delay = float(await self._get_setting("notification_retry_delay", default="2.0"))

        for service in services:
            try:
                multiplier = self.SERVICE_RETRY_MULTIPLIERS.get(service.service_name, 1.0)
                service_delay = base_delay * multiplier

                if final_priority in ("urgent", "high"):
                    success = await service.send_with_retry(
                        title=title,
                        message=message,
                        priority=final_priority,
                        tags=final_tags,
                        url=url,
                        max_attempts=max_attempts,
                        retry_delay=service_delay,
                    )
                else:
                    success = await service.send(
                        title=title,
                        message=message,
                        priority=final_priority,
                        tags=final_tags,
                        url=url,
                    )

                results[service.service_name] = success
            except Exception as e:
                logger.error("Error sending to %s: %s", service.service_name, e)
                results[service.service_name] = False
            finally:
                await service.close()

        return results

    # Convenience methods for FamilyCircle-specific notifications

    async def notify_event_created(
        self,
        event_title: str,
        family_name: str,
        creator_name: str,
        event_date: str,
        url: str | None = None,
    ) -> dict[str, bool]:
        """Send notification about a new event."""
        return await self.dispatch(
            event_type="event_created",
            title=f"New Event: {event_title}",
            message=f'{creator_name} created "{event_title}" in {family_name}, scheduled for {event_date}.',
            url=url,
        )

    async def notify_event_updated(
        self,
        event_title: str,
        updater_name: str,
        url: str | None = None,
    ) -> dict[str, bool]:
        """Send notification about an event update."""
        return await self.dispatch(
            event_type="event_updated",
            title=f"Event Updated: {event_title}",
            message=f'{updater_name} updated "{event_title}".',
            url=url,
        )

    async def notify_event_cancelled(
        self,
        event_title: str,
        cancelled_by: str,
        reason: str | None = None,
        url: str | None = None,
    ) -> dict[str, bool]:
        """Send notification about event cancellation."""
        msg = f'{cancelled_by} cancelled "{event_title}".'
        if reason:
            msg += f" Reason: {reason}"
        return await self.dispatch(
            event_type="event_cancelled",
            title=f"Event Cancelled: {event_title}",
            message=msg,
            url=url,
        )

    async def notify_event_reminder(
        self,
        event_title: str,
        event_date: str,
        days_until: int,
        url: str | None = None,
    ) -> dict[str, bool]:
        """Send event reminder notification."""
        return await self.dispatch(
            event_type="event_reminder",
            title=f"Reminder: {event_title}",
            message=f'"{event_title}" is in {days_until} day(s) ({event_date}).',
            url=url,
        )

    async def notify_rsvp_received(
        self,
        event_title: str,
        member_name: str,
        status: str,
        url: str | None = None,
    ) -> dict[str, bool]:
        """Send notification about a new RSVP."""
        return await self.dispatch(
            event_type="rsvp_received",
            title=f"RSVP: {event_title}",
            message=f'{member_name} responded "{status}" to "{event_title}".',
            url=url,
        )

    async def notify_poll_created(
        self,
        poll_question: str,
        creator_name: str,
        url: str | None = None,
    ) -> dict[str, bool]:
        """Send notification about a new poll."""
        return await self.dispatch(
            event_type="poll_created",
            title="New Poll",
            message=f'{creator_name} created a poll: "{poll_question}"',
            url=url,
        )

    async def notify_poll_closing_soon(
        self,
        poll_question: str,
        hours_remaining: int,
        url: str | None = None,
    ) -> dict[str, bool]:
        """Send notification about a poll closing soon."""
        return await self.dispatch(
            event_type="poll_closing_soon",
            title="Poll Closing Soon",
            message=f'Poll "{poll_question}" closes in {hours_remaining} hour(s).',
            url=url,
        )

    async def notify_comment_added(
        self,
        event_title: str,
        commenter_name: str,
        url: str | None = None,
    ) -> dict[str, bool]:
        """Send notification about a new comment."""
        return await self.dispatch(
            event_type="comment_added",
            title=f"New Comment: {event_title}",
            message=f'{commenter_name} commented on "{event_title}".',
            url=url,
        )

    async def notify_comment_mention(
        self,
        event_title: str,
        mentioner_name: str,
        mentioned_name: str,
        url: str | None = None,
    ) -> dict[str, bool]:
        """Send notification about being @mentioned in a comment."""
        return await self.dispatch(
            event_type="comment_mention",
            title=f"Mentioned in {event_title}",
            message=f'{mentioner_name} mentioned {mentioned_name} in a comment on "{event_title}".',
            url=url,
        )

    async def notify_family_member_joined(
        self,
        member_name: str,
        family_name: str,
    ) -> dict[str, bool]:
        """Send notification about a new family member."""
        return await self.dispatch(
            event_type="family_member_joined",
            title=f"Welcome to {family_name}!",
            message=f"{member_name} has joined {family_name}.",
        )
