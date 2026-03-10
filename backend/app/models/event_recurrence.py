"""Event recurrence model — recurring event configuration."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import Event

RECURRENCE_TYPES = ["yearly", "monthly", "weekly"]


class EventRecurrence(Base, UUIDMixin, TimestampMixin):
    """Recurrence configuration for an event."""

    __tablename__ = "event_recurrences"

    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    recurrence_type: Mapped[str] = mapped_column(String(20), nullable=False)
    next_occurrence: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    max_occurrences: Mapped[int | None] = mapped_column(Integer, nullable=True)
    occurrences_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="recurrence")

    def __repr__(self) -> str:
        return f"<EventRecurrence {self.recurrence_type} for event={self.event_id}>"
