"""Poll template Pydantic schemas."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pydantic import BaseModel, field_validator

if TYPE_CHECKING:
    from app.models.poll_template import PollTemplate


class PollTemplateCreate(BaseModel):
    """Create a custom poll template."""

    name: str
    description: str | None = None
    options: list[str]
    allow_multiple: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate template name."""
        v = v.strip()
        if not v:
            raise ValueError("Name is required")
        if len(v) > 200:
            raise ValueError("Name must be 200 characters or less")
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[str]) -> list[str]:
        """Validate at least 2 options."""
        cleaned = [o.strip() for o in v if o.strip()]
        if len(cleaned) < 2:
            raise ValueError("At least 2 options are required")
        if len(cleaned) > 10:
            raise ValueError("Maximum 10 options allowed")
        return cleaned


class PollTemplateResponse(BaseModel):
    """Poll template response."""

    id: str
    family_id: str | None
    name: str
    description: str | None
    options: list[str]
    allow_multiple: bool
    is_builtin: bool
    created_at: str | None

    @classmethod
    def from_model(cls, template: PollTemplate) -> PollTemplateResponse:
        """Build response from a PollTemplate model instance."""
        options = json.loads(template.options_json) if template.options_json else []
        return cls(
            id=str(template.id),
            family_id=str(template.family_id) if template.family_id else None,
            name=template.name,
            description=template.description,
            options=options,
            allow_multiple=template.allow_multiple,
            is_builtin=template.is_builtin,
            created_at=template.created_at.isoformat() if template.created_at else None,
        )
