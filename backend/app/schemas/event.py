"""Event-related schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EventCreate(BaseModel):
    """Create event request."""

    title: str
    description: Optional[str] = None
    event_date: datetime
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    has_secret_santa: bool = False
    has_potluck: bool = False
    has_rsvp: bool = True
    # Secret Santa rules
    secret_santa_budget_min: Optional[int] = None
    secret_santa_budget_max: Optional[int] = None
    secret_santa_notes: Optional[str] = None


class EventUpdate(BaseModel):
    """Update event request."""

    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    has_secret_santa: Optional[bool] = None
    has_potluck: Optional[bool] = None
    has_rsvp: Optional[bool] = None
    # Secret Santa rules
    secret_santa_budget_min: Optional[int] = None
    secret_santa_budget_max: Optional[int] = None
    secret_santa_notes: Optional[str] = None


class EventResponse(BaseModel):
    """Event response."""

    id: str
    title: str
    description: Optional[str]
    event_date: datetime
    location_name: Optional[str]
    location_address: Optional[str]
    has_secret_santa: bool
    has_potluck: bool
    has_rsvp: bool
    secret_santa_assigned: bool
    # Secret Santa rules
    secret_santa_budget_min: Optional[int] = None
    secret_santa_budget_max: Optional[int] = None
    secret_santa_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RSVPRequest(BaseModel):
    """RSVP request."""

    status: str  # yes, no, maybe


class RSVPResponse(BaseModel):
    """RSVP response."""

    id: str
    event_id: str
    member_id: str
    status: str
    member_name: Optional[str] = None

    class Config:
        from_attributes = True
