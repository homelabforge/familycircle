"""APScheduler service for periodic tasks like event reminders."""

import logging
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import DEFAULT_EVENT_REMINDER_DAYS
from app.db import async_session_maker
from app.models import Event
from app.models.token import Token
from app.services.notifications.dispatcher import NotificationDispatcher
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _get_global_setting(db: AsyncSession, key: str, default: str = "") -> str:
    """Get a global setting value via SettingsService."""
    return await SettingsService(db).get_setting(key, default)


async def generate_recurring_events() -> None:
    """Generate upcoming occurrences for recurring events.

    Runs daily. Creates new event instances for recurrences
    whose next_occurrence falls within the lookahead window (30 days).
    """
    logger.info("Running recurring event generation...")

    async with async_session_maker() as db:
        try:
            from app.services.recurrence import generate_pending_occurrences

            created = await generate_pending_occurrences(db)
            await db.commit()
            logger.info("Generated %d recurring event occurrences", created)
        except Exception:
            logger.exception("Error generating recurring events")


async def check_event_reminders() -> None:
    """Check for upcoming events and send reminder notifications.

    Runs daily. Sends reminders for events within `event_reminder_days` days.
    Only reminds about non-cancelled, non-secret-birthday events.
    """
    logger.info("Running event reminder check...")

    async with async_session_maker() as db:
        try:
            reminder_days_str = await _get_global_setting(
                db, "event_reminder_days", str(DEFAULT_EVENT_REMINDER_DAYS)
            )
            try:
                reminder_days = int(reminder_days_str)
            except ValueError:
                reminder_days = DEFAULT_EVENT_REMINDER_DAYS

            now = datetime.now(UTC)
            reminder_cutoff = now + timedelta(days=reminder_days)

            # Find upcoming events within the reminder window
            result = await db.execute(
                select(Event).where(
                    Event.event_date >= now,
                    Event.event_date <= reminder_cutoff,
                    Event.cancelled_at.is_(None),
                )
            )
            events = result.scalars().all()

            if not events:
                logger.info("No upcoming events within %d days", reminder_days)
                return

            dispatcher = NotificationDispatcher(db)
            sent_count = 0

            for event in events:
                # Skip secret birthdays — don't reveal via notification
                # birthday_detail is selectin-loaded, so it's already available
                if (
                    event.event_type == "birthday"
                    and event.birthday_detail
                    and event.birthday_detail.is_secret
                ):
                    continue

                days_until = (event.event_date.replace(tzinfo=UTC) - now).days
                event_date_str = event.event_date.strftime("%B %d, %Y")

                await dispatcher.notify_event_reminder(
                    event_title=event.title,
                    event_date=event_date_str,
                    days_until=max(days_until, 0),
                )
                sent_count += 1

            logger.info("Sent reminders for %d upcoming events", sent_count)

        except Exception:
            logger.exception("Error checking event reminders")


async def cleanup_expired_tokens() -> None:
    """Delete expired tokens from the tokens table.

    Runs daily. Prevents table bloat from accumulated expired sessions.
    Uses Python-generated UTC timestamp (SQLite-safe — raw NOW() is not valid SQLite).
    """
    logger.info("Running expired token cleanup...")

    async with async_session_maker() as db:
        try:
            now = datetime.now(UTC)
            result = await db.execute(delete(Token).where(Token.expires_at < now))
            deleted = result.rowcount
            await db.commit()
            if deleted:
                logger.info("Cleaned up %d expired token(s)", deleted)
            else:
                logger.info("No expired tokens to clean up")
        except Exception:
            logger.exception("Error cleaning up expired tokens")


def start_scheduler() -> None:
    """Start the APScheduler instance with periodic jobs."""
    # Event reminder check — runs daily at 8 AM UTC
    scheduler.add_job(check_event_reminders, "cron", hour=8, minute=0)

    # Recurring event generation — runs daily at 2 AM UTC
    scheduler.add_job(generate_recurring_events, "cron", hour=2, minute=0)

    # Expired token cleanup — runs daily at 3 AM UTC
    scheduler.add_job(cleanup_expired_tokens, "cron", hour=3, minute=0)

    scheduler.start()
    logger.info("Scheduler started with event reminder + recurrence + token cleanup jobs")


def stop_scheduler() -> None:
    """Stop the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
