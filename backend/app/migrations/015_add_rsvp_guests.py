"""Add RSVP guests table for +N guest tracking.

Migration: 015_add_rsvp_guests
Created: 2026-02-15

- CREATE TABLE rsvp_guests (additional guests brought by RSVP'd members)
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Create rsvp_guests table."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Check if table already exists
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='rsvp_guests'")
        )
        if result.scalar_one_or_none():
            print("  Migration 015: Table rsvp_guests already exists, skipping")
            return

        conn.execute(
            text("""
                CREATE TABLE rsvp_guests (
                    id VARCHAR(36) PRIMARY KEY,
                    rsvp_id VARCHAR(36) NOT NULL REFERENCES event_rsvps(id) ON DELETE CASCADE,
                    guest_name VARCHAR(200) NOT NULL,
                    dietary_restrictions VARCHAR(500),
                    allergies VARCHAR(500),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_rsvp_guests_rsvp_id ON rsvp_guests(rsvp_id)")
        )
        print("  Migration 015: Created rsvp_guests table")


def downgrade() -> None:
    """Reverse migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS rsvp_guests"))
