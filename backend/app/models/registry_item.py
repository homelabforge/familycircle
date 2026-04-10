"""Registry item model for event gift registries."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.user import User


class RegistryItem(Base, UUIDMixin, TimestampMixin):
    """An item in an event's gift registry."""

    __tablename__ = "registry_items"

    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_name: Mapped[str] = mapped_column(String(300), nullable=False)
    item_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    claimed_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    purchased_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    event: Mapped[Event] = relationship(back_populates="registry_items")
    claimed_by: Mapped[User | None] = relationship(foreign_keys=[claimed_by_id])

    @property
    def is_claimed(self) -> bool:
        """Check if item has been claimed."""
        return self.claimed_by_id is not None

    @property
    def is_purchased(self) -> bool:
        """Check if item has been purchased."""
        return self.purchased_at is not None

    def __repr__(self) -> str:
        return f"<RegistryItem {self.item_name}>"
