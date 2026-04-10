"""Gift Exchange models."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class GiftExchangeAssignment(Base, UUIDMixin, TimestampMixin):
    """Gift Exchange assignment - who gives to whom."""

    __tablename__ = "secret_santa_assignments"

    # event_id is a string identifier for the Gift Exchange round
    # Links to the Event.id when Gift Exchange is part of an event
    event_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    giver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    receiver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    giver: Mapped[User] = relationship(foreign_keys=[giver_id])
    receiver: Mapped[User] = relationship(foreign_keys=[receiver_id])

    def __repr__(self) -> str:
        return f"<GiftExchangeAssignment {self.giver_id} -> {self.receiver_id}>"


class GiftExchangeExclusion(Base, UUIDMixin, TimestampMixin):
    """Exclusion rule - two people who should not be paired."""

    __tablename__ = "secret_santa_exclusions"

    event_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    giver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    receiver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    giver: Mapped[User] = relationship(foreign_keys=[giver_id])
    receiver: Mapped[User] = relationship(foreign_keys=[receiver_id])

    def __repr__(self) -> str:
        return f"<GiftExchangeExclusion {self.giver_id} <-> {self.receiver_id}>"


class GiftExchangeMessage(Base, UUIDMixin, TimestampMixin):
    """Anonymous message between Gift Exchange pairs."""

    __tablename__ = "secret_santa_messages"

    event_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sender_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    sender: Mapped[User] = relationship(foreign_keys=[sender_id])
    recipient: Mapped[User] = relationship(foreign_keys=[recipient_id])

    def __repr__(self) -> str:
        return f"<GiftExchangeMessage {self.sender_id} -> {self.recipient_id}>"
