"""Event and RSVP models."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.baby_shower_detail import BabyShowerDetail
    from app.models.baby_shower_update import BabyShowerUpdate
    from app.models.birthday_detail import BirthdayDetail
    from app.models.event_comment import EventComment
    from app.models.event_photo import EventPhoto
    from app.models.event_recurrence import EventRecurrence
    from app.models.family import Family
    from app.models.holiday_detail import HolidayDetail
    from app.models.poll import Poll
    from app.models.potluck import PotluckItem
    from app.models.registry_item import RegistryItem
    from app.models.rsvp_guest import RSVPGuest
    from app.models.user import User
    from app.models.wedding_detail import WeddingDetail, WeddingPartyMember


class RSVPStatus(enum.StrEnum):
    """RSVP status options."""

    YES = "yes"
    NO = "no"
    MAYBE = "maybe"


class EventType(enum.StrEnum):
    """Event type classification."""

    GENERAL = "general"
    HOLIDAY = "holiday"
    BIRTHDAY = "birthday"
    BABY_SHOWER = "baby_shower"
    WEDDING = "wedding"


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

    # Event type
    event_type: Mapped[str] = mapped_column(
        String(20), default=EventType.GENERAL.value, nullable=False
    )

    # Parent event (for wedding sub-events in Phase 2)
    parent_event_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Basic info
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Date/time
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Location
    location_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Features enabled for this event
    has_secret_santa: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_potluck: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_rsvp: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Potluck configuration
    potluck_mode: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # 'organized' or 'open'
    potluck_host_providing: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # What the host is providing

    # Gift Exchange status
    secret_santa_assigned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    secret_santa_assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Gift Exchange rules
    secret_santa_budget_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    secret_santa_budget_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    secret_santa_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Cancellation
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Recurrence
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    family: Mapped["Family"] = relationship(back_populates="events")
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id])
    rsvps: Mapped[list["EventRSVP"]] = relationship(
        back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )
    potluck_items: Mapped[list["PotluckItem"]] = relationship(
        back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )

    # Type-specific detail relationships (one-to-one)
    holiday_detail: Mapped[Optional["HolidayDetail"]] = relationship(
        back_populates="event", lazy="selectin", uselist=False, cascade="all, delete-orphan"
    )
    birthday_detail: Mapped[Optional["BirthdayDetail"]] = relationship(
        back_populates="event", lazy="selectin", uselist=False, cascade="all, delete-orphan"
    )
    baby_shower_detail: Mapped[Optional["BabyShowerDetail"]] = relationship(
        back_populates="event", lazy="selectin", uselist=False, cascade="all, delete-orphan"
    )
    wedding_detail: Mapped[Optional["WeddingDetail"]] = relationship(
        back_populates="event", lazy="selectin", uselist=False, cascade="all, delete-orphan"
    )
    wedding_party_members: Mapped[list["WeddingPartyMember"]] = relationship(
        back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )

    # Polls and comments
    polls: Mapped[list["Poll"]] = relationship(
        back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )
    comments: Mapped[list["EventComment"]] = relationship(
        back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )

    # Photos
    photos: Mapped[list["EventPhoto"]] = relationship(
        back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )

    # Baby shower updates
    baby_shower_updates: Mapped[list["BabyShowerUpdate"]] = relationship(
        back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )

    # Registry items
    registry_items: Mapped[list["RegistryItem"]] = relationship(
        back_populates="event", lazy="selectin", cascade="all, delete-orphan"
    )

    # Recurrence
    recurrence: Mapped[Optional["EventRecurrence"]] = relationship(
        back_populates="event", lazy="selectin", uselist=False, cascade="all, delete-orphan"
    )

    # Self-referential for sub-events
    parent_event: Mapped[Optional["Event"]] = relationship(
        remote_side="Event.id",
        foreign_keys=[parent_event_id],
        back_populates="sub_events",
    )
    sub_events: Mapped[list["Event"]] = relationship(
        back_populates="parent_event", lazy="selectin", cascade="all, delete-orphan"
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
    status: Mapped[RSVPStatus] = mapped_column(SQLEnum(RSVPStatus), nullable=False)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="rsvps")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    guests: Mapped[list["RSVPGuest"]] = relationship(
        back_populates="rsvp", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<EventRSVP {self.user_id} -> {self.event_id}: {self.status}>"
