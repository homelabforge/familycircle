"""Poll models for family and event-scoped polls."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.family import Family
    from app.models.user import User


class Poll(Base, UUIDMixin, TimestampMixin):
    """A poll that belongs to a family, optionally attached to an event."""

    __tablename__ = "polls"

    family_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    allow_multiple: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    family: Mapped[Family] = relationship(foreign_keys=[family_id])
    event: Mapped[Event | None] = relationship(back_populates="polls", foreign_keys=[event_id])
    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
    options: Mapped[list[PollOption]] = relationship(
        back_populates="poll", lazy="selectin", cascade="all, delete-orphan"
    )
    votes: Mapped[list[PollVote]] = relationship(
        back_populates="poll",
        lazy="selectin",
        cascade="all, delete-orphan",
        foreign_keys="PollVote.poll_id",
    )

    @property
    def is_closed(self) -> bool:
        """Check if poll is closed (manually or by close_date)."""
        if self.closed_at is not None:
            return True
        if self.close_date is not None and self.close_date <= datetime.now(UTC):
            return True
        return False

    def __repr__(self) -> str:
        return f"<Poll {self.title}>"


class PollOption(Base, UUIDMixin, TimestampMixin):
    """An option within a poll."""

    __tablename__ = "poll_options"

    poll_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("polls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    poll: Mapped[Poll] = relationship(back_populates="options")
    votes: Mapped[list[PollVote]] = relationship(
        back_populates="option", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PollOption {self.text}>"


class PollVote(Base, UUIDMixin, TimestampMixin):
    """A user's vote on a poll option."""

    __tablename__ = "poll_votes"
    __table_args__ = (UniqueConstraint("option_id", "user_id", name="uq_poll_votes_option_user"),)

    poll_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("polls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("poll_options.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    poll: Mapped[Poll] = relationship(back_populates="votes", foreign_keys=[poll_id])
    option: Mapped[PollOption] = relationship(back_populates="votes")
    user: Mapped[User] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<PollVote {self.user_id} -> {self.option_id}>"
