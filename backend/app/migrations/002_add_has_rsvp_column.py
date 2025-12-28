"""Add has_rsvp column to events table."""

from sqlalchemy import text, create_engine

from app.config import DATABASE_PATH


def upgrade():
    """Add has_rsvp column to events table."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # =================================================================
        # EVENTS TABLE: Add has_rsvp column
        # =================================================================
        result = conn.execute(text("PRAGMA table_info(events)"))
        event_columns = {row[1]: row for row in result}

        if 'has_rsvp' not in event_columns:
            # Add has_rsvp column with default TRUE for backward compatibility
            # All existing events will have RSVP enabled
            conn.execute(text("""
                ALTER TABLE events
                ADD COLUMN has_rsvp BOOLEAN NOT NULL DEFAULT 1
            """))
            print("✓ Added has_rsvp to events (default: TRUE)")
        else:
            print("✓ events.has_rsvp already exists")


if __name__ == "__main__":
    upgrade()
