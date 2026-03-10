"""Baby shower event detail model."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import Event


ALLOWED_GENDERS = ["boy", "girl", "unknown", "surprise"]


class BabyShowerDetail(Base, UUIDMixin, TimestampMixin):
    """Type-specific details for baby shower events."""

    __tablename__ = "baby_shower_details"

    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    parent1_name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent2_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    baby_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    registry_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_gender_reveal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="baby_shower_detail")

    @property
    def display_parents(self) -> str:
        """Get display string for parents."""
        if self.parent2_name:
            return f"{self.parent1_name} & {self.parent2_name}"
        return self.parent1_name

    def __repr__(self) -> str:
        """Return string representation."""
        reveal = " (Gender Reveal)" if self.is_gender_reveal else ""
        return f"<BabyShowerDetail {self.display_parents}{reveal}>"
