"""Poll-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, field_validator


class PollOptionCreate(BaseModel):
    """Create a poll option."""

    text: str
    display_order: int = 0

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate option text."""
        v = v.strip()
        if not v:
            raise ValueError("Option text is required")
        if len(v) > 500:
            raise ValueError("Option text must be 500 characters or less")
        return v


class PollCreate(BaseModel):
    """Create a poll."""

    title: str
    description: str | None = None
    event_id: str | None = None
    allow_multiple: bool = False
    is_anonymous: bool = False
    close_date: datetime | None = None
    options: list[PollOptionCreate]

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate poll title."""
        v = v.strip()
        if not v:
            raise ValueError("Title is required")
        if len(v) > 300:
            raise ValueError("Title must be 300 characters or less")
        return v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[PollOptionCreate]) -> list[PollOptionCreate]:
        """Validate at least 2 options."""
        if len(v) < 2:
            raise ValueError("At least 2 options are required")
        return v


class PollOptionResponse(BaseModel):
    """Poll option in response."""

    id: str
    text: str
    display_order: int
    vote_count: int = 0
    voted_by: list[str] | None = None  # None when anonymous

    class Config:
        from_attributes = True


class PollResponse(BaseModel):
    """Poll response."""

    id: str
    family_id: str
    event_id: str | None
    created_by_id: str | None
    created_by_name: str | None = None
    title: str
    description: str | None
    allow_multiple: bool
    is_anonymous: bool
    close_date: datetime | None
    is_closed: bool
    total_votes: int = 0
    user_voted: bool = False
    user_votes: list[str] = []  # option IDs the current user voted for
    options: list[PollOptionResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class PollVoteRequest(BaseModel):
    """Vote on a poll."""

    option_ids: list[str]

    @field_validator("option_ids")
    @classmethod
    def validate_option_ids(cls, v: list[str]) -> list[str]:
        """Validate at least one option selected."""
        if not v:
            raise ValueError("At least one option must be selected")
        return v
