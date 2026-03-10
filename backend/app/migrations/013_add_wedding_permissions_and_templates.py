"""Add wedding party permissions and sub-event template column.

Migration: 013_add_wedding_permissions_and_templates
Created: 2026-02-15

- ALTER TABLE wedding_details ADD COLUMN sub_event_template
- CREATE TABLE wedding_party_permissions (per-member permission flags)
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Apply migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Add sub_event_template to wedding_details (idempotent)
        result = conn.execute(text("PRAGMA table_info(wedding_details)"))
        columns = {row[1] for row in result.fetchall()}
        if "sub_event_template" not in columns:
            conn.execute(
                text("ALTER TABLE wedding_details ADD COLUMN sub_event_template VARCHAR(50)")
            )
            print("  Migration 013: Added sub_event_template column to wedding_details")

        # Wedding party permissions table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS wedding_party_permissions (
                    id VARCHAR(36) PRIMARY KEY,
                    member_id VARCHAR(36) NOT NULL REFERENCES wedding_party_members(id) ON DELETE CASCADE,
                    can_manage_sub_events INTEGER NOT NULL DEFAULT 0,
                    can_view_rsvps INTEGER NOT NULL DEFAULT 0,
                    can_post_updates INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(member_id)
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_wedding_party_permissions_member_id "
                "ON wedding_party_permissions(member_id)"
            )
        )
        print("  Migration 013: Created wedding_party_permissions table")


def downgrade() -> None:
    """Reverse migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS wedding_party_permissions"))
        # SQLite doesn't support DROP COLUMN, so sub_event_template stays
