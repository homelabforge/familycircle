"""User model - replaces Member for authentication."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.family import FamilyMembership
    from app.models.user_profile import UserProfile


class User(Base, UUIDMixin, TimestampMixin):
    """User account - can belong to multiple families."""

    __tablename__ = "users"

    # Basic info
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Auth
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Platform role
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Magic link token (for password recovery)
    magic_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    magic_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Session token (after successful auth)
    session_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    session_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Current active family context (set after login/switch)
    current_family_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # User preferences
    theme: Mapped[str] = mapped_column(String(20), default="system", nullable=False)
    big_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    family_memberships: Mapped[list["FamilyMembership"]] = relationship(
        back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )
    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user", lazy="selectin", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def active_family_id(self) -> str:
        """Return current_family_id, narrowed to str.

        Safe to call in endpoints that use require_family_context dependency,
        which guarantees current_family_id is set.
        """
        if self.current_family_id is None:
            raise RuntimeError("active_family_id accessed without family context")
        return self.current_family_id

    def __repr__(self) -> str:
        return f"<User {self.email}>"
