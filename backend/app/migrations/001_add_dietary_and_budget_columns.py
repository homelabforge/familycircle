"""Add Secret Santa budget rules and Potluck dietary information columns."""

from sqlalchemy import create_engine, text

from app.config import DATABASE_PATH


def upgrade():
    """Add budget and dietary columns if they don't exist."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # =================================================================
        # EVENTS TABLE: Add Secret Santa budget columns
        # =================================================================
        result = conn.execute(text("PRAGMA table_info(events)"))
        event_columns = {row[1]: row for row in result}

        if "secret_santa_budget_min" not in event_columns:
            conn.execute(
                text("""
                ALTER TABLE events
                ADD COLUMN secret_santa_budget_min INTEGER
            """)
            )
            print("✓ Added secret_santa_budget_min to events")
        else:
            print("✓ events.secret_santa_budget_min already exists")

        if "secret_santa_budget_max" not in event_columns:
            conn.execute(
                text("""
                ALTER TABLE events
                ADD COLUMN secret_santa_budget_max INTEGER
            """)
            )
            print("✓ Added secret_santa_budget_max to events")
        else:
            print("✓ events.secret_santa_budget_max already exists")

        if "secret_santa_notes" not in event_columns:
            conn.execute(
                text("""
                ALTER TABLE events
                ADD COLUMN secret_santa_notes TEXT
            """)
            )
            print("✓ Added secret_santa_notes to events")
        else:
            print("✓ events.secret_santa_notes already exists")

        # =================================================================
        # POTLUCK_ITEMS TABLE: Add dietary information columns
        # =================================================================
        result = conn.execute(text("PRAGMA table_info(potluck_items)"))
        potluck_columns = {row[1]: row for row in result}

        if "dietary_info" not in potluck_columns:
            conn.execute(
                text("""
                ALTER TABLE potluck_items
                ADD COLUMN dietary_info VARCHAR(200)
            """)
            )
            print("✓ Added dietary_info to potluck_items")
        else:
            print("✓ potluck_items.dietary_info already exists")

        if "allergens" not in potluck_columns:
            conn.execute(
                text("""
                ALTER TABLE potluck_items
                ADD COLUMN allergens VARCHAR(200)
            """)
            )
            print("✓ Added allergens to potluck_items")
        else:
            print("✓ potluck_items.allergens already exists")


if __name__ == "__main__":
    upgrade()
