"""Add poll templates table with built-in templates.

Migration: 011_add_poll_templates
Created: 2026-02-15

- CREATE TABLE poll_templates
- INSERT built-in templates: Yes/No, Rating 1-5, Thumbs Up/Down
"""

import uuid
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
                CREATE TABLE IF NOT EXISTS poll_templates (
                    id VARCHAR(36) PRIMARY KEY,
                    family_id VARCHAR(36) REFERENCES families(id) ON DELETE CASCADE,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    options_json TEXT NOT NULL,
                    allow_multiple INTEGER NOT NULL DEFAULT 0,
                    is_builtin INTEGER NOT NULL DEFAULT 0,
                    created_by_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_poll_templates_family_id "
                "ON poll_templates(family_id)"
            )
        )
        print("  Migration 011: Created poll_templates table")

        # Insert built-in templates (family_id = NULL means global)
        result = conn.execute(text("SELECT COUNT(*) FROM poll_templates WHERE is_builtin = 1"))
        count = result.scalar() or 0
        if count == 0:
            templates = [
                {
                    "id": uuid.uuid4().hex,
                    "name": "Yes / No",
                    "description": "Simple yes or no question",
                    "options_json": '["Yes", "No"]',
                    "allow_multiple": 0,
                },
                {
                    "id": uuid.uuid4().hex,
                    "name": "Rating 1-5",
                    "description": "Rate on a scale of 1 to 5",
                    "options_json": '["1", "2", "3", "4", "5"]',
                    "allow_multiple": 0,
                },
                {
                    "id": uuid.uuid4().hex,
                    "name": "Thumbs Up / Down",
                    "description": "Quick thumbs up or down vote",
                    "options_json": '["\\ud83d\\udc4d Thumbs Up", "\\ud83d\\udc4e Thumbs Down"]',
                    "allow_multiple": 0,
                },
            ]
            for t in templates:
                conn.execute(
                    text("""
                        INSERT INTO poll_templates
                            (id, family_id, name, description, options_json, allow_multiple, is_builtin,
                             created_at, updated_at)
                        VALUES
                            (:id, NULL, :name, :description, :options_json, :allow_multiple, 1,
                             CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """),
                    t,
                )
            print(f"  Migration 011: Inserted {len(templates)} built-in poll templates")


def downgrade() -> None:
    """Reverse migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS poll_templates"))
