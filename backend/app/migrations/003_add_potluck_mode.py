"""Add potluck mode and host providing fields to events table.

Migration: 003_add_potluck_mode
Created: 2025-12-28
"""

from pathlib import Path
from sqlalchemy import create_engine, text

# Database path (same as app config)
DATABASE_PATH = Path("/data/familycircle.db")


def upgrade():
    """Add potluck_mode and potluck_host_providing columns."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(events)"))
        event_columns = {row[1]: row for row in result}

        if 'potluck_mode' not in event_columns:
            conn.execute(text("""
                ALTER TABLE events
                ADD COLUMN potluck_mode VARCHAR(20) NULL
            """))
            print("✓ Added potluck_mode to events")
        else:
            print("✓ events.potluck_mode already exists")

        if 'potluck_host_providing' not in event_columns:
            conn.execute(text("""
                ALTER TABLE events
                ADD COLUMN potluck_host_providing TEXT NULL
            """))
            print("✓ Added potluck_host_providing to events")
        else:
            print("✓ events.potluck_host_providing already exists")


def downgrade():
    """Remove potluck_mode and potluck_host_providing columns."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # SQLite doesn't support DROP COLUMN directly, would need table recreation
        print("⚠ Downgrade not implemented for SQLite (requires table recreation)")


if __name__ == "__main__":
    upgrade()
