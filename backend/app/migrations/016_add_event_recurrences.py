"""Add event recurrences table and is_recurring column.

Migration: 016_add_event_recurrences
Created: 2026-02-15

- ALTER TABLE events ADD COLUMN is_recurring
- CREATE TABLE event_recurrences (recurrence rules for repeating events)
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Create event_recurrences table and add is_recurring column to events."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Add is_recurring column to events if not exists
        result = conn.execute(text("PRAGMA table_info(events)"))
        columns = {row[1] for row in result.fetchall()}

        if "is_recurring" not in columns:
            conn.execute(text("ALTER TABLE events ADD COLUMN is_recurring INTEGER DEFAULT 0"))
            print("  Migration 016: Added is_recurring column to events")

        # Create event_recurrences table
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='event_recurrences'")
        )
        if result.scalar_one_or_none():
            print("  Migration 016: Table event_recurrences already exists, skipping")
            return

        conn.execute(
            text("""
                CREATE TABLE event_recurrences (
                    id VARCHAR(36) PRIMARY KEY,
                    event_id VARCHAR(36) NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                    recurrence_type VARCHAR(20) NOT NULL,
                    next_occurrence DATETIME,
                    end_date DATETIME,
                    max_occurrences INTEGER,
                    occurrences_created INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_event_recurrences_event_id "
                "ON event_recurrences(event_id)"
            )
        )
        print("  Migration 016: Created event_recurrences table")


def downgrade() -> None:
    """Reverse migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS event_recurrences"))
        # SQLite doesn't support DROP COLUMN, so is_recurring stays
