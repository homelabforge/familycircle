"""Baby shower update timeline model."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.event_photo import EventPhoto
    from app.models.user import User


BABY_SHOWER_UPDATE_TYPES = [
    "baby_born",
    "name_announced",
    "gender_revealed",
    "milestone",
    "custom",
]


class BabyShowerUpdate(Base, UUIDMixin, TimestampMixin):
    """A timeline update for a baby shower event."""

    __tablename__ = "baby_shower_updates"

    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    update_type: Mapped[str] = mapped_column(String(30), nullable=False)
    update_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("event_photos.id", ondelete="SET NULL"),
        nullable=True,
    )
    posted_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    event: Mapped[Event] = relationship(back_populates="baby_shower_updates")
    photo: Mapped[EventPhoto | None] = relationship(foreign_keys=[photo_id])
    posted_by: Mapped[User | None] = relationship(foreign_keys=[posted_by_id])

    def __repr__(self) -> str:
        return f"<BabyShowerUpdate {self.update_type}: {self.title}>"
