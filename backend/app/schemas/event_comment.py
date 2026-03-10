"""Event comment Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, field_validator


class EventCommentCreate(BaseModel):
    """Create an event comment."""

    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate comment content."""
        v = v.strip()
        if not v:
            raise ValueError("Comment cannot be empty")
        if len(v) > 5000:
            raise ValueError("Comment must be 5000 characters or less")
        return v


class EventCommentUpdate(BaseModel):
    """Update an event comment."""

    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate comment content."""
        v = v.strip()
        if not v:
            raise ValueError("Comment cannot be empty")
        if len(v) > 5000:
            raise ValueError("Comment must be 5000 characters or less")
        return v


class EventCommentResponse(BaseModel):
    """Event comment response."""

    id: str
    event_id: str
    user_id: str
    user_name: str = ""
    content: str
    edited_at: datetime | None = None
    is_own: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
