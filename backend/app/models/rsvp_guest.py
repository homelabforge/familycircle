"""RSVP guest model — additional guests brought by an RSVP."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import EventRSVP


class RSVPGuest(Base, UUIDMixin, TimestampMixin):
    """An additional guest attached to an RSVP."""

    __tablename__ = "rsvp_guests"

    rsvp_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("event_rsvps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    guest_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dietary_restrictions: Mapped[str | None] = mapped_column(String(500), nullable=True)
    allergies: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    rsvp: Mapped["EventRSVP"] = relationship(back_populates="guests")

    def __repr__(self) -> str:
        return f"<RSVPGuest {self.guest_name} for rsvp={self.rsvp_id}>"
