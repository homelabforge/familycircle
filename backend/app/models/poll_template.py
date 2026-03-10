"""Poll template model for reusable poll configurations."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.family import Family
    from app.models.user import User


class PollTemplate(Base, UUIDMixin, TimestampMixin):
    """A reusable poll template. Built-in templates have family_id=NULL."""

    __tablename__ = "poll_templates"

    family_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    options_json: Mapped[str] = mapped_column(Text, nullable=False)
    allow_multiple: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    family: Mapped["Family | None"] = relationship(foreign_keys=[family_id])
    created_by: Mapped["User | None"] = relationship(foreign_keys=[created_by_id])

    def __repr__(self) -> str:
        return f"<PollTemplate {self.name}>"
