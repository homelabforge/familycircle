"""Add baby shower updates timeline table.

Migration: 012_add_baby_shower_updates
Created: 2026-02-15

- CREATE TABLE baby_shower_updates (timeline posts for baby shower events)
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Apply migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS baby_shower_updates (
                    id VARCHAR(36) PRIMARY KEY,
                    event_id VARCHAR(36) NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                    update_type VARCHAR(30) NOT NULL,
                    update_date DATE,
                    title VARCHAR(200) NOT NULL,
                    notes TEXT,
                    photo_id VARCHAR(36) REFERENCES event_photos(id) ON DELETE SET NULL,
                    posted_by_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_baby_shower_updates_event_id "
                "ON baby_shower_updates(event_id)"
            )
        )
        print("  Migration 012: Created baby_shower_updates table")


def downgrade() -> None:
    """Reverse migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS baby_shower_updates"))
