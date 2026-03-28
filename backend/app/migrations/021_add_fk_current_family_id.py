"""Add foreign key constraint on users.current_family_id → families.id.

Migration: 021_add_fk_current_family_id
Created: 2026-03-27

H4 fix: current_family_id was a bare String(36) with no FK constraint.
If a family is deleted, users could retain a stale pointer.

SQLite cannot add a FK to an existing column — this requires a table rebuild:
1. Clean up orphaned current_family_id values (point to nonexistent families)
2. Create new table with the FK constraint
3. Copy data from old table
4. Drop old table
5. Rename new table
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Add FK constraint on users.current_family_id."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Check if the FK already exists by inspecting the table DDL
        result = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        )
        row = result.fetchone()
        if row and "REFERENCES families" in (row[0] or ""):
            print("  Migration 021: FK on current_family_id already exists, skipping")
            engine.dispose()
            return

        # Step 1: Clean up orphaned current_family_id values
        conn.execute(
            text("""
                UPDATE users
                SET current_family_id = NULL
                WHERE current_family_id IS NOT NULL
                  AND current_family_id NOT IN (SELECT id FROM families)
            """)
        )
        orphans = conn.execute(text("SELECT changes()")).scalar()
        if orphans:
            print(f"  Migration 021: Cleaned up {orphans} orphaned current_family_id values")

        # Step 2: Get current column info to rebuild table accurately
        # We read PRAGMA table_info to get the exact schema
        cols = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        col_names = [c[1] for c in cols]

        # Step 3: Create new table with FK constraint
        # Reproduce the exact schema from the ORM model
        conn.execute(
            text("""
                CREATE TABLE users_new (
                    id VARCHAR(36) NOT NULL,
                    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    email VARCHAR(255) NOT NULL,
                    password_hash VARCHAR(255),
                    is_super_admin BOOLEAN NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    magic_token VARCHAR(64),
                    magic_token_expires DATETIME,
                    session_token VARCHAR(64),
                    session_expires DATETIME,
                    current_family_id VARCHAR(36) REFERENCES families(id) ON DELETE SET NULL,
                    theme VARCHAR(20) NOT NULL DEFAULT 'system',
                    big_mode BOOLEAN NOT NULL DEFAULT 0,
                    PRIMARY KEY (id),
                    UNIQUE (email)
                )
            """)
        )

        # Step 4: Copy data — use only columns that exist in both tables
        copy_cols = ", ".join(col_names)
        conn.execute(text(f"INSERT INTO users_new ({copy_cols}) SELECT {copy_cols} FROM users"))

        # Step 5: Recreate indexes that existed on the old table
        # (We'll recreate them after the rename)
        conn.execute(text("DROP TABLE users"))
        conn.execute(text("ALTER TABLE users_new RENAME TO users"))

        # Step 6: Recreate indexes
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_magic_token ON users (magic_token)"))
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_users_session_token ON users (session_token)")
        )

        print("  Migration 021: Added FK constraint on users.current_family_id → families.id")

    engine.dispose()


def downgrade() -> None:
    """Remove FK constraint (rebuild without it)."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        cols = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        col_names = [c[1] for c in cols]

        conn.execute(
            text("""
                CREATE TABLE users_new (
                    id VARCHAR(36) NOT NULL,
                    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP),
                    email VARCHAR(255) NOT NULL,
                    password_hash VARCHAR(255),
                    is_super_admin BOOLEAN NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    magic_token VARCHAR(64),
                    magic_token_expires DATETIME,
                    session_token VARCHAR(64),
                    session_expires DATETIME,
                    current_family_id VARCHAR(36),
                    theme VARCHAR(20) NOT NULL DEFAULT 'system',
                    big_mode BOOLEAN NOT NULL DEFAULT 0,
                    PRIMARY KEY (id),
                    UNIQUE (email)
                )
            """)
        )

        copy_cols = ", ".join(col_names)
        conn.execute(text(f"INSERT INTO users_new ({copy_cols}) SELECT {copy_cols} FROM users"))
        conn.execute(text("DROP TABLE users"))
        conn.execute(text("ALTER TABLE users_new RENAME TO users"))

        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_magic_token ON users (magic_token)"))
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_users_session_token ON users (session_token)")
        )

    engine.dispose()
