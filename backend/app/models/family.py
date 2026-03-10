"""Family model."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.family_membership import FamilyMembership
    from app.models.profile_visibility import ProfileVisibility


class Family(Base, UUIDMixin, TimestampMixin):
    """Family group - contains members and events."""

    __tablename__ = "families"

    # Basic info
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Unique code for joining this family
    family_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # Calendar feed token (for subscribable iCal feed URL)
    calendar_feed_token: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    memberships: Mapped[list["FamilyMembership"]] = relationship(
        back_populates="family", lazy="selectin", cascade="all, delete-orphan"
    )
    events: Mapped[list["Event"]] = relationship(
        back_populates="family", lazy="selectin", cascade="all, delete-orphan"
    )
    profile_visibility_settings: Mapped[list["ProfileVisibility"]] = relationship(
        back_populates="family", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Family {self.name} ({self.family_code})>"
