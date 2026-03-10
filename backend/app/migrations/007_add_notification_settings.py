"""Add default notification settings to the settings table.

Migration: 007_add_notification_settings
Created: 2026-02-15

No new tables — inserts default global settings (family_id=NULL)
for the notification service configuration and per-event toggles.
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")

# Default notification settings to insert
NOTIFICATION_SETTINGS = {
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
    # Email notifications (reuses existing SMTP config)
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
    "event_reminder_days": "3",
}


def upgrade():
    """Insert default notification settings."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        for key, value in NOTIFICATION_SETTINGS.items():
            # Idempotent: only insert if not already present
            result = conn.execute(
                text("SELECT 1 FROM settings WHERE key = :key AND family_id IS NULL"),
                {"key": key},
            )
            if result.fetchone() is None:
                conn.execute(
                    text(
                        "INSERT INTO settings (key, value, family_id, created_at, updated_at) "
                        "VALUES (:key, :value, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                    ),
                    {"key": key, "value": value},
                )

        print("  Migration 007: Inserted notification default settings")


def downgrade():
    """Remove notification settings."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        for key in NOTIFICATION_SETTINGS:
            conn.execute(
                text("DELETE FROM settings WHERE key = :key AND family_id IS NULL"),
                {"key": key},
            )

        print("  Migration 007 downgrade: Removed notification settings")
