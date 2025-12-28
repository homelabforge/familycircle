"""Potluck schemas."""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class PotluckItemCreate(BaseModel):
    """Create potluck item."""

    name: str
    dietary_info: Optional[str] = None
    notes: Optional[str] = None


class PotluckItemResponse(BaseModel):
    """Potluck item response."""

    id: str
    event_id: str
    name: str
    dietary_info: Optional[str]
    notes: Optional[str]
    claimed_by_id: Optional[str]
    claimed_by_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
