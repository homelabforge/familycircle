"""Potluck schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PotluckItemCreate(BaseModel):
    """Create potluck item."""

    name: str
    dietary_info: str | None = None
    notes: str | None = None


class PotluckItemResponse(BaseModel):
    """Potluck item response."""

    id: str
    event_id: str
    name: str
    dietary_info: str | None
    notes: str | None
    claimed_by_id: str | None
    claimed_by_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
