"""Token model — separates session and magic link tokens from the User model.

Multi-session semantics:
- Login: Creates a new Token row (does NOT invalidate existing sessions)
- Logout: Deletes only the current session's Token row
- Password reset: Invalidates ALL tokens for the user, creates one new session
- Magic link: One active magic_link token per user (new request overwrites old)
- Expiry cleanup: APScheduler job deletes expired tokens daily
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class TokenType(enum.StrEnum):
    """Token type identifiers."""

    SESSION = "session"
    MAGIC_LINK = "magic_link"


class Token(Base, UUIDMixin, TimestampMixin):
    """Authentication token — supports multiple concurrent sessions per user."""

    __tablename__ = "tokens"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    token_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Named token_metadata (not metadata) to avoid shadowing SQLAlchemy's Base.metadata
    token_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<Token {self.token_type} for user={self.user_id}>"
