"""Birthday event detail model."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.user import User


class BirthdayDetail(Base, UUIDMixin, TimestampMixin):
    """Type-specific details for birthday events."""

    __tablename__ = "birthday_details"

    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    birthday_person_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    birthday_person_name: Mapped[str] = mapped_column(String(200), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    age_turning: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    theme: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="birthday_detail")
    birthday_person: Mapped[Optional["User"]] = relationship(foreign_keys=[birthday_person_id])

    def __repr__(self) -> str:
        """Return string representation."""
        secret = " (SECRET)" if self.is_secret else ""
        return f"<BirthdayDetail {self.birthday_person_name}{secret}>"
