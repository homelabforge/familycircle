"""Add compound indexes for common query patterns.

Migration: 019_add_compound_indexes
Created: 2026-03-27

Adds compound indexes to improve performance on the most frequent queries:
- events(family_id, event_date): list/upcoming events filtered by family, ordered by date
- event_rsvps(event_id, user_id): RSVP lookup for a specific user on a specific event
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Add compound indexes."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # events(family_id, event_date) — list and upcoming queries
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_events_family_date ON events (family_id, event_date)"
            )
        )
        print("  Migration 019: Added compound index ix_events_family_date")

        # event_rsvps(event_id, user_id) — RSVP lookup per user per event
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_event_rsvps_event_user "
                "ON event_rsvps (event_id, user_id)"
            )
        )
        print("  Migration 019: Added compound index ix_event_rsvps_event_user")

    engine.dispose()


def downgrade() -> None:
    """Remove compound indexes."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP INDEX IF EXISTS ix_events_family_date"))
        conn.execute(text("DROP INDEX IF EXISTS ix_event_rsvps_event_user"))

    engine.dispose()
