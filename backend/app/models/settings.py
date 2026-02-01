"""Application settings model."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class Setting(Base, TimestampMixin):
    """Key-value settings storage - can be global or per-family."""

    __tablename__ = "settings"
    __table_args__ = (UniqueConstraint("family_id", "key", name="uq_family_setting_key"),)

    # Settings can be global (family_id=NULL) or per-family
    family_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("families.id", ondelete="CASCADE"), nullable=True, index=True
    )
    key: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        family = f" (family={self.family_id})" if self.family_id else " (global)"
        return f"<Setting {self.key}={self.value[:50] if self.value else None}{family}>"
