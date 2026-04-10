"""Profile visibility settings - per-family control over what info is shared."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.family import Family
    from app.models.user import User


class ProfileVisibility(Base, UUIDMixin, TimestampMixin):
    """Controls what profile information is visible to a specific family."""

    __tablename__ = "profile_visibility"
    __table_args__ = (UniqueConstraint("user_id", "family_id", name="uq_user_family_visibility"),)

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("families.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Visibility settings (default to showing everything)
    show_email: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_phone: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_address: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    family: Mapped[Family] = relationship(back_populates="profile_visibility_settings")

    def __repr__(self) -> str:
        return f"<ProfileVisibility user={self.user_id} family={self.family_id}>"
