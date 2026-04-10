"""Comment reaction model for emoji reactions on event comments."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event_comment import EventComment
    from app.models.user import User

# Fixed emoji set for reactions
ALLOWED_EMOJIS = {"👍", "❤️", "😂", "😮", "😢", "🎉"}


class CommentReaction(Base, UUIDMixin, TimestampMixin):
    """An emoji reaction on a comment."""

    __tablename__ = "comment_reactions"
    __table_args__ = (
        UniqueConstraint("comment_id", "user_id", "emoji", name="uq_comment_reaction"),
    )

    comment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("event_comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    emoji: Mapped[str] = mapped_column(String(10), nullable=False)

    # Relationships
    comment: Mapped[EventComment] = relationship(foreign_keys=[comment_id])
    user: Mapped[User] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<CommentReaction {self.emoji} by {self.user_id} on {self.comment_id}>"
