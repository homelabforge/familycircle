"""Wedding event detail and party member models."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.user import User
    from app.models.wedding_party_permission import WeddingPartyPermission


WEDDING_PARTY_ROLES = [
    "best_man",
    "maid_of_honor",
    "bridesmaid",
    "groomsman",
    "flower_girl",
    "ring_bearer",
    "officiant",
    "usher",
    "other",
]


class WeddingDetail(Base, UUIDMixin, TimestampMixin):
    """Type-specific details for wedding events."""

    __tablename__ = "wedding_details"

    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    partner1_name: Mapped[str] = mapped_column(String(200), nullable=False)
    partner2_name: Mapped[str] = mapped_column(String(200), nullable=False)
    wedding_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    venue_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    registry_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    color_theme: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sub_event_template: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="wedding_detail")

    @property
    def display_couple(self) -> str:
        """Get display string for the couple."""
        return f"{self.partner1_name} & {self.partner2_name}"

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<WeddingDetail {self.display_couple}>"


class WeddingPartyMember(Base, UUIDMixin, TimestampMixin):
    """A member of the wedding party."""

    __tablename__ = "wedding_party_members"

    event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    side: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="wedding_party_members")
    user: Mapped[Optional["User"]] = relationship(foreign_keys=[user_id])
    permissions: Mapped[Optional["WeddingPartyPermission"]] = relationship(
        back_populates="member", lazy="selectin", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def display_role(self) -> str:
        """Get human-readable role name."""
        role_labels = {
            "best_man": "Best Man",
            "maid_of_honor": "Maid of Honor",
            "bridesmaid": "Bridesmaid",
            "groomsman": "Groomsman",
            "flower_girl": "Flower Girl",
            "ring_bearer": "Ring Bearer",
            "officiant": "Officiant",
            "usher": "Usher",
            "other": "Other",
        }
        return role_labels.get(self.role, self.role.replace("_", " ").title())

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<WeddingPartyMember {self.name} ({self.display_role})>"
