"""Secret Santa models."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class SecretSantaAssignment(Base, UUIDMixin, TimestampMixin):
    """Secret Santa assignment - who gives to whom."""

    __tablename__ = "secret_santa_assignments"

    # event_id is a string identifier for the Secret Santa round
    # Links to the Event.id when Secret Santa is part of an event
    event_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    giver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    receiver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    giver: Mapped["User"] = relationship(foreign_keys=[giver_id])
    receiver: Mapped["User"] = relationship(foreign_keys=[receiver_id])

    def __repr__(self) -> str:
        return f"<SecretSantaAssignment {self.giver_id} -> {self.receiver_id}>"


class SecretSantaExclusion(Base, UUIDMixin, TimestampMixin):
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
    giver: Mapped["User"] = relationship(foreign_keys=[giver_id])
    receiver: Mapped["User"] = relationship(foreign_keys=[receiver_id])

    def __repr__(self) -> str:
        return f"<SecretSantaExclusion {self.giver_id} <-> {self.receiver_id}>"


class SecretSantaMessage(Base, UUIDMixin, TimestampMixin):
    """Anonymous message between Secret Santa pairs."""

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
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])
    recipient: Mapped["User"] = relationship(foreign_keys=[recipient_id])

    def __repr__(self) -> str:
        return f"<SecretSantaMessage {self.sender_id} -> {self.recipient_id}>"
