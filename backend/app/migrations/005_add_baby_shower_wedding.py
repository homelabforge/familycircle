"""Add baby shower and wedding detail tables with wedding party members.

Migration: 005_add_baby_shower_wedding
Created: 2026-02-15
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade():
    """Create baby_shower_details, wedding_details, and wedding_party_members tables."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # --- Baby shower details table ---
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS baby_shower_details (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    event_id VARCHAR(36) NOT NULL UNIQUE
                        REFERENCES events(id) ON DELETE CASCADE,
                    parent1_name VARCHAR(200) NOT NULL,
                    parent2_name VARCHAR(200) NULL,
                    baby_name VARCHAR(200) NULL,
                    gender VARCHAR(20) NULL,
                    due_date DATE NULL,
                    registry_url TEXT NULL,
                    is_gender_reveal INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_baby_shower_details_event_id "
                "ON baby_shower_details(event_id)"
            )
        )
        print("  Created baby_shower_details table")

        # --- Wedding details table ---
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS wedding_details (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    event_id VARCHAR(36) NOT NULL UNIQUE
                        REFERENCES events(id) ON DELETE CASCADE,
                    partner1_name VARCHAR(200) NOT NULL,
                    partner2_name VARCHAR(200) NOT NULL,
                    wedding_date DATE NULL,
                    venue_name VARCHAR(200) NULL,
                    registry_url TEXT NULL,
                    color_theme VARCHAR(200) NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_wedding_details_event_id "
                "ON wedding_details(event_id)"
            )
        )
        print("  Created wedding_details table")

        # --- Wedding party members table ---
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS wedding_party_members (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    event_id VARCHAR(36) NOT NULL
                        REFERENCES events(id) ON DELETE CASCADE,
                    user_id VARCHAR(36) NULL
                        REFERENCES users(id) ON DELETE SET NULL,
                    name VARCHAR(200) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    side VARCHAR(20) NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_wedding_party_members_event_id "
                "ON wedding_party_members(event_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_wedding_party_members_user_id "
                "ON wedding_party_members(user_id)"
            )
        )
        print("  Created wedding_party_members table")

    print("Migration 005_add_baby_shower_wedding complete")


def downgrade():
    """Remove baby shower and wedding tables."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS wedding_party_members"))
        conn.execute(text("DROP TABLE IF EXISTS wedding_details"))
        conn.execute(text("DROP TABLE IF EXISTS baby_shower_details"))
        print("  Downgrade: dropped baby shower and wedding tables")


if __name__ == "__main__":
    upgrade()
