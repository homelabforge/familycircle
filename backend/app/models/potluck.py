"""Potluck contribution model."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.user import User


class PotluckItem(Base, UUIDMixin, TimestampMixin):
    """Potluck item to bring."""

    __tablename__ = "potluck_items"

    event_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Item details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # appetizer, main, side, dessert, drink, other
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    serves: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Dietary information
    dietary_info: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # e.g., "vegetarian, gluten-free, contains nuts"
    allergens: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )  # e.g., "nuts, dairy, gluten"

    # Who claimed it (now references users table)
    claimed_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    event: Mapped[Event] = relationship(back_populates="potluck_items")
    claimed_by: Mapped[User | None] = relationship(foreign_keys=[claimed_by_id])

    def __repr__(self) -> str:
        claimed = f" (claimed by {self.claimed_by_id})" if self.claimed_by_id else ""
        return f"<PotluckItem {self.name}{claimed}>"
