"""Event comment model for chronological discussion threads."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.comment_mention import CommentMention
    from app.models.comment_reaction import CommentReaction
    from app.models.event import Event
    from app.models.user import User


class EventComment(Base, UUIDMixin, TimestampMixin):
    """A comment on an event, visible to all family members."""

    __tablename__ = "event_comments"

    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pinned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    event: Mapped[Event] = relationship(back_populates="comments")
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    reactions: Mapped[list[CommentReaction]] = relationship(
        back_populates="comment",
        lazy="selectin",
        cascade="all, delete-orphan",
        foreign_keys="CommentReaction.comment_id",
    )
    mentions: Mapped[list[CommentMention]] = relationship(
        back_populates="comment",
        lazy="selectin",
        cascade="all, delete-orphan",
        foreign_keys="CommentMention.comment_id",
    )

    def __repr__(self) -> str:
        return f"<EventComment {self.id} on {self.event_id}>"
