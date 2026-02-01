"""Family membership model - links users to families with roles."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.family import Family
    from app.models.user import User


class FamilyRole(str, enum.Enum):
    """Role within a family."""

    ADMIN = "admin"
    MEMBER = "member"


class FamilyMembership(Base, UUIDMixin, TimestampMixin):
    """Links a user to a family with a specific role."""

    __tablename__ = "family_memberships"
    __table_args__ = (UniqueConstraint("user_id", "family_id", name="uq_user_family"),)

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("families.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Role within this family
    role: Mapped[FamilyRole] = mapped_column(
        SQLEnum(FamilyRole), default=FamilyRole.MEMBER, nullable=False
    )

    # Display name in this family (can differ from family to family)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="family_memberships")
    family: Mapped["Family"] = relationship(back_populates="memberships")

    def __repr__(self) -> str:
        return f"<FamilyMembership {self.user_id} in {self.family_id} as {self.role}>"
