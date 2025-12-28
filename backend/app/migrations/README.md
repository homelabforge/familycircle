# FamilyCircle Database Migrations

## Overview

This directory contains the automated database migration system for FamilyCircle. Migrations run automatically on container startup - no manual intervention required.

## How It Works

1. On startup, `init_db()` in `db.py` calls the migration runner
2. The runner creates a `schema_migrations` tracking table
3. It discovers all `*.py` files in this directory (sorted by filename)
4. It skips migrations already recorded in `schema_migrations`
5. Pending migrations are executed in order and marked complete

## File Structure

```
app/migrations/
├── __init__.py          # Package init
├── runner.py            # Migration runner (do not modify)
├── README.md            # This file
├── 001_description.py   # First migration
├── 002_description.py   # Second migration
└── ...
```

## Standard Operating Procedure (SOP)

### Adding a New Migration

#### Step 1: Determine the Next Sequence Number

```bash
ls backend/app/migrations/*.py | grep -E "^[0-9]" | tail -1
```

The next migration should use the next number (e.g., if 001 exists, use 002).

#### Step 2: Create the Migration File

Create a new file following the naming convention:

```
NNN_short_description.py
```

- `NNN`: 3-digit sequence number (001, 002, 003...)
- `short_description`: Brief snake_case description

**Examples:**
- `001_add_dietary_and_budget_columns.py`
- `002_add_notification_preferences.py`
- `003_add_photo_gallery_table.py`

#### Step 3: Write the Migration

Use this template:

```python
"""Brief description of what this migration does."""

from pathlib import Path
from sqlalchemy import text, create_engine

from app.config import DATABASE_PATH


def upgrade():
    """Apply this migration."""
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Check if column/table already exists (idempotency)
        result = conn.execute(text("PRAGMA table_info(table_name)"))
        columns = {row[1]: row for row in result}

        if 'new_column' not in columns:
            conn.execute(text("""
                ALTER TABLE table_name
                ADD COLUMN new_column TYPE
            """))
            print("✓ Added new_column to table_name")
        else:
            print("✓ table_name.new_column already exists")


if __name__ == "__main__":
    upgrade()
```

#### Step 4: Test Locally

```bash
# Rebuild and restart the container
docker compose build familycircle
docker compose up -d familycircle

# Check logs for migration output
docker compose logs familycircle | grep -E "(migration|Migration|✓|✗)"
```

#### Step 5: Verify

```bash
# Check the schema_migrations table
docker exec familycircle-dev sqlite3 /data/familycircle.db \
  "SELECT * FROM schema_migrations ORDER BY id;"

# Verify the column was added
docker exec familycircle-dev sqlite3 /data/familycircle.db \
  "PRAGMA table_info(table_name);"
```

### Key Requirements

1. **Function Name**: Must be `upgrade()` - the runner looks for this exact name
2. **Idempotency**: Always check if the change already exists before applying
3. **Print Output**: Use `print()` for status messages (shows in container logs)
4. **Error Handling**: Let exceptions propagate - the runner handles them

### Common Migration Patterns

#### Adding a Column

```python
def upgrade():
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(events)"))
        columns = {row[1]: row for row in result}

        if 'new_column' not in columns:
            conn.execute(text("""
                ALTER TABLE events ADD COLUMN new_column VARCHAR(100)
            """))
            print("✓ Added new_column to events")
        else:
            print("✓ events.new_column already exists")
```

#### Adding Multiple Columns

```python
def upgrade():
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(members)"))
        columns = {row[1]: row for row in result}

        new_columns = [
            ("phone", "VARCHAR(20)"),
            ("notification_email", "BOOLEAN DEFAULT 1"),
            ("notification_push", "BOOLEAN DEFAULT 1"),
        ]

        for col_name, col_type in new_columns:
            if col_name not in columns:
                conn.execute(text(f"ALTER TABLE members ADD COLUMN {col_name} {col_type}"))
                print(f"✓ Added {col_name} to members")
            else:
                print(f"✓ members.{col_name} already exists")
```

#### Creating a New Table

```python
def upgrade():
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Check if table exists
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='new_table'"
        ))
        if not result.fetchone():
            conn.execute(text("""
                CREATE TABLE new_table (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✓ Created new_table")
        else:
            print("✓ new_table already exists")
```

#### Adding an Index

```python
def upgrade():
    database_url = f"sqlite:///{DATABASE_PATH}"
    engine = create_engine(database_url)

    with engine.begin() as conn:
        # Check if index exists
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_events_date'"
        ))
        if not result.fetchone():
            conn.execute(text("""
                CREATE INDEX idx_events_date ON events(event_date)
            """))
            print("✓ Created index idx_events_date")
        else:
            print("✓ idx_events_date already exists")
```

## Migration Tracking

The `schema_migrations` table tracks applied migrations:

```sql
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

To view applied migrations:

```bash
docker exec familycircle-dev sqlite3 /data/familycircle.db \
  "SELECT migration_name, applied_at FROM schema_migrations ORDER BY id;"
```

## Troubleshooting

### Migration Failed

If a migration fails:
1. Check the container logs for the error
2. Fix the migration file
3. The failed migration won't be marked as applied
4. Restart the container to retry

### Force Re-run a Migration

To re-run a migration (use with caution):

```bash
# Remove the migration record
docker exec familycircle-dev sqlite3 /data/familycircle.db \
  "DELETE FROM schema_migrations WHERE migration_name = '001_add_dietary_and_budget_columns';"

# Restart container
docker compose restart familycircle
```

### Check Database Schema

```bash
# List all tables
docker exec familycircle-dev sqlite3 /data/familycircle.db ".tables"

# Show table schema
docker exec familycircle-dev sqlite3 /data/familycircle.db ".schema events"
```

## Migration History

| Migration | Date | Description |
|-----------|------|-------------|
| 001_add_dietary_and_budget_columns | 2024-11-29 | Secret Santa budget rules, Potluck dietary info |

---

*Last updated: 2024-11-29*
