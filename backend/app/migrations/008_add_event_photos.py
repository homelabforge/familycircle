"""Add event_photos table for photo gallery.

Migration: 008_add_event_photos
Created: 2026-02-15

Creates the event_photos table for storing photo metadata.
Actual files are stored on the local filesystem at /data/uploads/.
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Create event_photos table."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS event_photos (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    event_id VARCHAR(36) NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                    family_id VARCHAR(36) NOT NULL REFERENCES families(id) ON DELETE CASCADE,
                    uploaded_by_id VARCHAR(36) NULL REFERENCES users(id) ON DELETE SET NULL,
                    filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_size INTEGER NOT NULL,
                    mime_type VARCHAR(50) NOT NULL,
                    caption TEXT NULL,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )

        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_event_photos_event_id ON event_photos(event_id)")
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_event_photos_family_id ON event_photos(family_id)")
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_event_photos_display_order "
                "ON event_photos(event_id, display_order)"
            )
        )

        print("  Migration 008: Created event_photos table")


def downgrade() -> None:
    """Drop event_photos table."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS event_photos"))
        print("  Migration 008 downgrade: Dropped event_photos table")
