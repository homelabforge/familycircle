"""Add registry items table for gift registries on events.

Migration: 014_add_registry_items
Created: 2026-02-15

- CREATE TABLE registry_items (manual gift registry for weddings, baby showers, etc.)
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
                CREATE TABLE IF NOT EXISTS registry_items (
                    id VARCHAR(36) PRIMARY KEY,
                    event_id VARCHAR(36) NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                    item_name VARCHAR(300) NOT NULL,
                    item_url TEXT,
                    price DECIMAL(10, 2),
                    image_url TEXT,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    claimed_by_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    purchased_at DATETIME,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_registry_items_event_id ON registry_items(event_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_registry_items_claimed_by_id "
                "ON registry_items(claimed_by_id)"
            )
        )
        print("  Migration 014: Created registry_items table")


def downgrade() -> None:
    """Reverse migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS registry_items"))
