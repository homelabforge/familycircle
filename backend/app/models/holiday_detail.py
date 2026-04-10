"""Holiday event detail model."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import Event

PREDEFINED_HOLIDAYS: list[str] = [
    "Christmas",
    "Thanksgiving",
    "Easter",
    "Hanukkah",
    "New Year's Eve",
    "New Year's Day",
    "Valentine's Day",
    "Halloween",
    "Independence Day",
    "Mother's Day",
    "Father's Day",
    "Memorial Day",
    "Labor Day",
    "Passover",
    "Diwali",
    "Eid al-Fitr",
    "Eid al-Adha",
    "Kwanzaa",
    "Chinese New Year",
    "Juneteenth",
    "St. Patrick's Day",
    "Cinco de Mayo",
]


class HolidayDetail(Base, UUIDMixin, TimestampMixin):
    """Type-specific details for holiday events."""

    __tablename__ = "holiday_details"

    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    holiday_name: Mapped[str] = mapped_column(String(100), nullable=False)
    custom_holiday_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    event: Mapped[Event] = relationship(back_populates="holiday_detail")

    @property
    def display_name(self) -> str:
        """Get the display name for this holiday."""
        if self.holiday_name == "custom" and self.custom_holiday_name:
            return self.custom_holiday_name
        return self.holiday_name

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<HolidayDetail {self.display_name} ({self.year})>"
