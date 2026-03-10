"""Baby shower update schemas."""

from datetime import date

from pydantic import BaseModel, field_validator

from app.models.baby_shower_update import BABY_SHOWER_UPDATE_TYPES


class BabyShowerUpdateCreate(BaseModel):
    """Schema for creating a baby shower update."""

    update_type: str
    update_date: date | None = None
    title: str
    notes: str | None = None
    photo_id: str | None = None

    @field_validator("update_type")
    @classmethod
    def validate_update_type(cls, v: str) -> str:
        """Validate update type."""
        if v not in BABY_SHOWER_UPDATE_TYPES:
            msg = f"Invalid update type. Must be one of: {', '.join(BABY_SHOWER_UPDATE_TYPES)}"
            raise ValueError(msg)
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty."""
        v = v.strip()
        if not v:
            msg = "Title is required"
            raise ValueError(msg)
        return v
