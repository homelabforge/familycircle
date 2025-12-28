"""User profile model - extended personal information."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class UserProfile(Base, UUIDMixin, TimestampMixin):
    """Extended profile information for a user."""

    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Health/medical information
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dietary_restrictions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    medical_needs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mobility_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Privacy settings - whether to share health info anonymously with event organizers
    share_health_info: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile for {self.user_id}>"
