"""Comment mention model for tracking @mentions in event comments."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event_comment import EventComment
    from app.models.user import User


class CommentMention(Base, UUIDMixin, TimestampMixin):
    """Tracks an @mention of a user within a comment."""

    __tablename__ = "comment_mentions"

    comment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("event_comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mentioned_user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    comment: Mapped[EventComment] = relationship(foreign_keys=[comment_id])
    mentioned_user: Mapped[User] = relationship(foreign_keys=[mentioned_user_id])

    def __repr__(self) -> str:
        return f"<CommentMention {self.mentioned_user_id} in {self.comment_id}>"
