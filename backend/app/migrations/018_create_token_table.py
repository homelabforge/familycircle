"""Create tokens table for session and magic link management.

Migration: 018_create_token_table
Created: 2026-03-14

Separates token concerns from the User model:
- Supports multi-session (multiple devices/browsers)
- Magic link tokens tracked independently
- token_metadata for future device info / session management UI

Existing session_token and magic_token columns on users are NOT dropped
(SQLite limitation + rollback safety). Auth service dual-writes during transition.
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Create tokens table and migrate existing token data."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Check if table already exists
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='tokens'")
        )
        if result.scalar_one_or_none():
            print("  Migration 018: Table tokens already exists, skipping")
            return

        conn.execute(
            text("""
                CREATE TABLE tokens (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(64) NOT NULL UNIQUE,
                    token_type VARCHAR(20) NOT NULL,
                    expires_at DATETIME,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    token_metadata TEXT
                )
            """)
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tokens_token ON tokens(token)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tokens_user_id ON tokens(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tokens_type ON tokens(token_type)"))
        print("  Migration 018: Created tokens table")

        # Migrate existing session tokens
        conn.execute(
            text("""
                INSERT INTO tokens (id, user_id, token, token_type, expires_at, created_at, updated_at)
                SELECT
                    lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' ||
                          substr(hex(randomblob(2)),2) || '-' ||
                          substr('89ab', abs(random()) % 4 + 1, 1) ||
                          substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6))),
                    id,
                    session_token,
                    'session',
                    session_expires,
                    COALESCE(created_at, CURRENT_TIMESTAMP),
                    CURRENT_TIMESTAMP
                FROM users
                WHERE session_token IS NOT NULL
            """)
        )
        session_count = conn.execute(
            text("SELECT COUNT(*) FROM tokens WHERE token_type = 'session'")
        ).scalar()
        print(f"  Migration 018: Migrated {session_count} existing session token(s)")

        # Migrate existing magic tokens
        conn.execute(
            text("""
                INSERT INTO tokens (id, user_id, token, token_type, expires_at, created_at, updated_at)
                SELECT
                    lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' ||
                          substr(hex(randomblob(2)),2) || '-' ||
                          substr('89ab', abs(random()) % 4 + 1, 1) ||
                          substr(hex(randomblob(2)),2) || '-' || hex(randomblob(6))),
                    id,
                    magic_token,
                    'magic_link',
                    magic_token_expires,
                    COALESCE(created_at, CURRENT_TIMESTAMP),
                    CURRENT_TIMESTAMP
                FROM users
                WHERE magic_token IS NOT NULL
            """)
        )
        magic_count = conn.execute(
            text("SELECT COUNT(*) FROM tokens WHERE token_type = 'magic_link'")
        ).scalar()
        print(f"  Migration 018: Migrated {magic_count} existing magic link token(s)")


def downgrade() -> None:
    """Reverse migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS tokens"))
