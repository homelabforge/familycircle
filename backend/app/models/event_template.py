"""Event template model — reusable event configurations."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.family import Family
    from app.models.user import User


class EventTemplate(Base, UUIDMixin, TimestampMixin):
    """A reusable event template scoped to a family."""

    __tablename__ = "event_templates"

    family_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    template_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    family: Mapped["Family"] = relationship()
    created_by: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:
        return f"<EventTemplate {self.name} family={self.family_id}>"
