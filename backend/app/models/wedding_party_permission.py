"""Wedding party member permissions model."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.wedding_detail import WeddingPartyMember


class WeddingPartyPermission(Base, UUIDMixin, TimestampMixin):
    """Permission flags for a wedding party member."""

    __tablename__ = "wedding_party_permissions"

    member_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("wedding_party_members.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    can_manage_sub_events: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_view_rsvps: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_post_updates: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    member: Mapped[WeddingPartyMember] = relationship(back_populates="permissions", uselist=False)

    def __repr__(self) -> str:
        return f"<WeddingPartyPermission member={self.member_id}>"
