"""Add comment reactions, mentions, and pinning support.

Migration: 010_add_comment_enhancements
Created: 2026-02-15

- CREATE TABLE comment_reactions (toggle emoji reactions on comments)
- CREATE TABLE comment_mentions (@mention tracking)
- ALTER TABLE event_comments ADD COLUMN pinned_at (pin/unpin support)
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Apply migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Comment reactions table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS comment_reactions (
                    id VARCHAR(36) PRIMARY KEY,
                    comment_id VARCHAR(36) NOT NULL REFERENCES event_comments(id) ON DELETE CASCADE,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    emoji VARCHAR(10) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(comment_id, user_id, emoji)
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_comment_reactions_comment_id "
                "ON comment_reactions(comment_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_comment_reactions_user_id "
                "ON comment_reactions(user_id)"
            )
        )
        print("  Migration 010: Created comment_reactions table")

        # Comment mentions table
        conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS comment_mentions (
                    id VARCHAR(36) PRIMARY KEY,
                    comment_id VARCHAR(36) NOT NULL REFERENCES event_comments(id) ON DELETE CASCADE,
                    mentioned_user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_comment_mentions_comment_id "
                "ON comment_mentions(comment_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_comment_mentions_mentioned_user_id "
                "ON comment_mentions(mentioned_user_id)"
            )
        )
        print("  Migration 010: Created comment_mentions table")

        # Add pinned_at column to event_comments (idempotent)
        result = conn.execute(text("PRAGMA table_info(event_comments)"))
        columns = {row[1] for row in result.fetchall()}
        if "pinned_at" not in columns:
            conn.execute(text("ALTER TABLE event_comments ADD COLUMN pinned_at DATETIME"))
            print("  Migration 010: Added pinned_at column to event_comments")


def downgrade() -> None:
    """Reverse migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS comment_mentions"))
        conn.execute(text("DROP TABLE IF EXISTS comment_reactions"))
        # SQLite doesn't support DROP COLUMN, so pinned_at stays
