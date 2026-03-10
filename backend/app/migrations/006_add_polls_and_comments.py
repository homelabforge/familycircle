"""Add polls, poll options, poll votes, and event comments tables.

Migration: 006_add_polls_and_comments
Created: 2026-02-15
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade():
    """Create polls, poll_options, poll_votes, and event_comments tables."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # --- Polls table ---
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS polls (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    family_id VARCHAR(36) NOT NULL
                        REFERENCES families(id) ON DELETE CASCADE,
                    event_id VARCHAR(36) NULL
                        REFERENCES events(id) ON DELETE CASCADE,
                    created_by_id VARCHAR(36) NULL
                        REFERENCES users(id) ON DELETE SET NULL,
                    title VARCHAR(300) NOT NULL,
                    description TEXT NULL,
                    allow_multiple INTEGER NOT NULL DEFAULT 0,
                    is_anonymous INTEGER NOT NULL DEFAULT 0,
                    close_date DATETIME NULL,
                    closed_at DATETIME NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_polls_family_id ON polls(family_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_polls_event_id ON polls(event_id)"))
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_polls_created_by_id ON polls(created_by_id)")
        )
        print("  Created polls table")

        # --- Poll options table ---
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS poll_options (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    poll_id VARCHAR(36) NOT NULL
                        REFERENCES polls(id) ON DELETE CASCADE,
                    text VARCHAR(500) NOT NULL,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_poll_options_poll_id ON poll_options(poll_id)")
        )
        print("  Created poll_options table")

        # --- Poll votes table ---
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS poll_votes (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    poll_id VARCHAR(36) NOT NULL
                        REFERENCES polls(id) ON DELETE CASCADE,
                    option_id VARCHAR(36) NOT NULL
                        REFERENCES poll_options(id) ON DELETE CASCADE,
                    user_id VARCHAR(36) NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_poll_votes_poll_id ON poll_votes(poll_id)")
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_poll_votes_option_id ON poll_votes(option_id)")
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_poll_votes_user_id ON poll_votes(user_id)")
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_poll_votes_option_user "
                "ON poll_votes(option_id, user_id)"
            )
        )
        print("  Created poll_votes table")

        # --- Event comments table ---
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS event_comments (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    event_id VARCHAR(36) NOT NULL
                        REFERENCES events(id) ON DELETE CASCADE,
                    user_id VARCHAR(36) NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    edited_at DATETIME NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_event_comments_event_id ON event_comments(event_id)"
            )
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_event_comments_user_id ON event_comments(user_id)")
        )
        print("  Created event_comments table")

    print("Migration 006_add_polls_and_comments complete")


def downgrade():
    """Remove polls and comments tables."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS poll_votes"))
        conn.execute(text("DROP TABLE IF EXISTS poll_options"))
        conn.execute(text("DROP TABLE IF EXISTS polls"))
        conn.execute(text("DROP TABLE IF EXISTS event_comments"))
        print("  Downgrade: dropped polls and comments tables")


if __name__ == "__main__":
    upgrade()
