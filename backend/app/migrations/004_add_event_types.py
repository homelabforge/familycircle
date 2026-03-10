"""Add event type system with holiday and birthday detail tables.

Migration: 004_add_event_types
Created: 2026-02-15
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade():
    """Add event_type, parent_event_id to events; create detail tables."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # --- Events table changes ---
        result = conn.execute(text("PRAGMA table_info(events)"))
        event_columns = {row[1]: row for row in result}

        if "event_type" not in event_columns:
            conn.execute(
                text(
                    "ALTER TABLE events "
                    "ADD COLUMN event_type VARCHAR(20) NOT NULL DEFAULT 'general'"
                )
            )
            print("  Added event_type to events (default: general)")
        else:
            print("  events.event_type already exists")

        if "parent_event_id" not in event_columns:
            conn.execute(
                text(
                    "ALTER TABLE events "
                    "ADD COLUMN parent_event_id VARCHAR(36) NULL "
                    "REFERENCES events(id) ON DELETE CASCADE"
                )
            )
            print("  Added parent_event_id to events")
        else:
            print("  events.parent_event_id already exists")

        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_events_parent_event_id ON events(parent_event_id)")
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_events_event_type ON events(event_type)"))

        # --- Holiday details table ---
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS holiday_details (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    event_id VARCHAR(36) NOT NULL UNIQUE
                        REFERENCES events(id) ON DELETE CASCADE,
                    holiday_name VARCHAR(100) NOT NULL,
                    custom_holiday_name VARCHAR(200) NULL,
                    year INTEGER NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_holiday_details_event_id "
                "ON holiday_details(event_id)"
            )
        )
        print("  Created holiday_details table")

        # --- Birthday details table ---
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS birthday_details (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    event_id VARCHAR(36) NOT NULL UNIQUE
                        REFERENCES events(id) ON DELETE CASCADE,
                    birthday_person_id VARCHAR(36) NULL
                        REFERENCES users(id) ON DELETE SET NULL,
                    birthday_person_name VARCHAR(200) NOT NULL,
                    birth_date DATE NULL,
                    age_turning INTEGER NULL,
                    is_secret INTEGER NOT NULL DEFAULT 0,
                    theme VARCHAR(200) NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_birthday_details_event_id "
                "ON birthday_details(event_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_birthday_details_birthday_person_id "
                "ON birthday_details(birthday_person_id)"
            )
        )
        print("  Created birthday_details table")

    print("Migration 004_add_event_types complete")


def downgrade():
    """Remove event type system."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS birthday_details"))
        conn.execute(text("DROP TABLE IF EXISTS holiday_details"))
        print("  Downgrade: dropped detail tables (event columns remain)")


if __name__ == "__main__":
    upgrade()
