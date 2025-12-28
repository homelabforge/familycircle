"""Event and RSVP models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.family import Family
    from app.models.user import User
    from app.models.potluck import PotluckItem


class RSVPStatus(str, enum.Enum):
    """RSVP status options."""

    YES = "yes"
    NO = "no"
    MAYBE = "maybe"


class Event(Base, UUIDMixin, TimestampMixin):
    """Family event (dinner, party, etc.)."""

    __tablename__ = "events"

    # Family this event belongs to
    family_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("families.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Who created this event
    created_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Basic info
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Date/time
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Location
    location_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    location_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Features enabled for this event
    has_secret_santa: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_potluck: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_rsvp: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Secret Santa status
    secret_santa_assigned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    secret_santa_assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Secret Santa rules
    secret_santa_budget_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    secret_santa_budget_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    secret_santa_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    family: Mapped["Family"] = relationship(back_populates="events")
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id])
    rsvps: Mapped[list["EventRSVP"]] = relationship(
        back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )
    potluck_items: Mapped[list["PotluckItem"]] = relationship(
        back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )

    @property
    def is_cancelled(self) -> bool:
        """Check if event is cancelled."""
        return self.cancelled_at is not None

    def __repr__(self) -> str:
        return f"<Event {self.title} ({self.event_date})>"


class EventRSVP(Base, UUIDMixin, TimestampMixin):
    """RSVP for an event."""

    __tablename__ = "event_rsvps"

    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[RSVPStatus] = mapped_column(
        SQLEnum(RSVPStatus), nullable=False
    )

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="rsvps")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<EventRSVP {self.user_id} -> {self.event_id}: {self.status}>"
