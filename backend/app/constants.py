"""Application-wide constants — replaces hardcoded magic numbers (M3 fix)."""

# Session & auth
SESSION_TOKEN_EXPIRY_DAYS = 30
"""How long a session token stays valid."""

SESSION_COOKIE_MAX_AGE_SECONDS = SESSION_TOKEN_EXPIRY_DAYS * 24 * 3600
"""Cookie max-age, matches token expiry."""

# File uploads
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
"""Maximum file upload size (10 MB)."""

# Event recurrence
RECURRENCE_LOOKAHEAD_DAYS = 30
"""How far ahead to generate recurring event occurrences."""

# Defaults for database-stored settings (used when setting doesn't exist yet)
DEFAULT_CANCELLED_EVENT_RETENTION_DAYS = 7
"""Days to keep cancelled events visible before filtering them out."""

DEFAULT_EVENT_REMINDER_DAYS = 3
"""Days before an event to send reminders."""

DEFAULT_MAGIC_LINK_EXPIRY_DAYS = 90
"""Days before a magic link token expires."""
