"""Event photo Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class EventPhotoCreate(BaseModel):
    """Caption for a photo upload (optional)."""

    caption: str | None = None

    @field_validator("caption")
    @classmethod
    def validate_caption(cls, v: str | None) -> str | None:
        """Validate caption length."""
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError("Caption must be 500 characters or less")
            if not v:
                return None
        return v


class EventPhotoResponse(BaseModel):
    """Event photo response."""

    id: str
    event_id: str
    uploaded_by_id: str | None = None
    uploaded_by_name: str = ""
    filename: str
    url: str
    file_size: int
    mime_type: str
    caption: str | None = None
    display_order: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventPhotoReorder(BaseModel):
    """Reorder photos."""

    photo_ids: list[str]

    @field_validator("photo_ids")
    @classmethod
    def validate_photo_ids(cls, v: list[str]) -> list[str]:
        """Validate photo IDs list."""
        if not v:
            raise ValueError("Photo IDs list cannot be empty")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate photo IDs")
        return v
