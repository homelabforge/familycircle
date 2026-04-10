"""Wishlist item model."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class WishlistItem(Base, UUIDMixin, TimestampMixin):
    """Gift wishlist item."""

    __tablename__ = "wishlist_items"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Item details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)  # Notes, size, color, etc.
    url: Mapped[str | None] = mapped_column(Text, nullable=True)  # URL to product
    price_range: Mapped[str | None] = mapped_column(String(10), nullable=True)  # $, $$, $$$
    priority: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )  # 1-5, 1 = most wanted

    # Relationships
    user: Mapped[User] = relationship(foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<WishlistItem {self.name} (for {self.user_id})>"
