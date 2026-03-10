"""Add calendar_feed_token column to families table.

Migration: 009_add_calendar_feed_token
Created: 2026-02-15

Adds a unique token per family for subscribable iCal feed URLs.
"""

import uuid
from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Add calendar_feed_token column and generate tokens for existing families."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(families)"))
        columns = {row[1] for row in result.fetchall()}

        if "calendar_feed_token" not in columns:
            conn.execute(
                text("ALTER TABLE families ADD COLUMN calendar_feed_token VARCHAR(64) NULL")
            )
            print("  Migration 009: Added calendar_feed_token column")

        # Generate tokens for existing families that don't have one
        result = conn.execute(text("SELECT id FROM families WHERE calendar_feed_token IS NULL"))
        families = result.fetchall()
        for (family_id,) in families:
            token = uuid.uuid4().hex + uuid.uuid4().hex[:32]  # 64 char token
            conn.execute(
                text("UPDATE families SET calendar_feed_token = :token WHERE id = :id"),
                {"token": token, "id": family_id},
            )

        if families:
            print(f"  Migration 009: Generated feed tokens for {len(families)} families")


def downgrade() -> None:
    """SQLite cannot DROP COLUMN — this is a no-op."""
    print("  Migration 009 downgrade: No-op (SQLite cannot drop columns)")
