"""Purge orphaned gift-exchange assignment rows.

Migration: 022_cleanup_orphan_gift_assignments
Created: 2026-06-02

F7 fix: ``GiftExchangeAssignment.event_id`` (table ``secret_santa_assignments``)
is an unconstrained string with no foreign key, so assignments whose event was
hard-deleted — or that otherwise point at a non-existent event — linger
forever. Those stale rows used to keep unlocking a target member's wishlist.

The read path (`api/wishlist.py get_user_wishlist`) now re-checks a live,
same-family, non-cancelled gift-exchange event before honoring an assignment,
so orphan rows can no longer grant access. This migration is the one-time
cleanup of the existing dead rows.

Why not a real FK with ON DELETE CASCADE: this app does not enable
``PRAGMA foreign_keys=ON`` per connection (only on the single init_db
connection), so SQLite does not enforce FKs / fire cascades at runtime —
cleanup is handled in app/ORM logic, not DB-level cascades. A decorative FK
plus a table rebuild would add risk without changing runtime behavior, so we
purge the orphans directly instead.

Idempotent: a DELETE that matches nothing once the table is clean.
"""

from pathlib import Path

from sqlalchemy import create_engine, text

DATABASE_PATH = Path("/data/familycircle.db")


def upgrade() -> None:
    """Delete gift-exchange assignment rows that reference a missing event."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # On a brand-new DB the table is created from ORM metadata before
        # migrations run, but guard anyway so the migration is safe in any order.
        table = conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='secret_santa_assignments'"
            )
        ).fetchone()
        if not table:
            print("  Migration 022: secret_santa_assignments table absent, skipping")
            engine.dispose()
            return

        conn.execute(
            text(
                """
                DELETE FROM secret_santa_assignments
                WHERE event_id NOT IN (SELECT id FROM events)
                """
            )
        )
        removed = conn.execute(text("SELECT changes()")).scalar()
        if removed:
            print(f"  Migration 022: purged {removed} orphaned gift-exchange assignment(s)")
        else:
            print("  Migration 022: no orphaned gift-exchange assignments")

    engine.dispose()


def downgrade() -> None:
    """No-op — deleted orphan rows cannot be reconstructed."""
    pass
