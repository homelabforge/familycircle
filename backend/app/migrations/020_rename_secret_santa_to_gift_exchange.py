"""Rename secret_santa columns to gift_exchange on the events table.

Migration: 020_rename_secret_santa_to_gift_exchange
Created: 2026-03-27

M1 fix: The feature was renamed from "Secret Santa" to "Gift Exchange" at the
API/UI layer but the database schema was never updated. SQLite 3.25.0+ supports
ALTER TABLE RENAME COLUMN natively — no table rebuild needed.
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")

# Map of old column names to new column names
RENAMES = {
    "has_secret_santa": "has_gift_exchange",
    "secret_santa_assigned": "gift_exchange_assigned",
    "secret_santa_assigned_at": "gift_exchange_assigned_at",
    "secret_santa_budget_min": "gift_exchange_budget_min",
    "secret_santa_budget_max": "gift_exchange_budget_max",
    "secret_santa_notes": "gift_exchange_notes",
}


def upgrade() -> None:
    """Rename secret_santa columns to gift_exchange."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Check which columns still have the old names
        result = conn.execute(text("PRAGMA table_info(events)"))
        existing_columns = {row[1] for row in result.fetchall()}

        for old_name, new_name in RENAMES.items():
            if old_name in existing_columns and new_name not in existing_columns:
                conn.execute(text(f"ALTER TABLE events RENAME COLUMN {old_name} TO {new_name}"))
                print(f"  Migration 020: Renamed {old_name} → {new_name}")
            elif new_name in existing_columns:
                print(f"  Migration 020: {new_name} already exists, skipping")

    engine.dispose()


def downgrade() -> None:
    """Rename gift_exchange columns back to secret_santa."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(events)"))
        existing_columns = {row[1] for row in result.fetchall()}

        for old_name, new_name in RENAMES.items():
            if new_name in existing_columns and old_name not in existing_columns:
                conn.execute(text(f"ALTER TABLE events RENAME COLUMN {new_name} TO {old_name}"))

    engine.dispose()
