"""Add event templates table.

Migration: 017_add_event_templates
Created: 2026-02-15

- CREATE TABLE event_templates (reusable event templates per family)
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Create event_templates table."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='event_templates'")
        )
        if result.scalar_one_or_none():
            print("  Migration 017: Table event_templates already exists, skipping")
            return

        conn.execute(
            text("""
                CREATE TABLE event_templates (
                    id VARCHAR(36) PRIMARY KEY,
                    family_id VARCHAR(36) NOT NULL REFERENCES families(id) ON DELETE CASCADE,
                    name VARCHAR(200) NOT NULL,
                    description VARCHAR(500),
                    template_json TEXT NOT NULL,
                    created_by_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_event_templates_family_id "
                "ON event_templates(family_id)"
            )
        )
        print("  Migration 017: Created event_templates table")


def downgrade() -> None:
    """Reverse migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS event_templates"))
