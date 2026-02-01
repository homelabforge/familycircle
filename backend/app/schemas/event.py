"""Event-related schemas."""

from datetime import datetime

from pydantic import BaseModel


class EventCreate(BaseModel):
    """Create event request."""

    title: str
    description: str | None = None
    event_date: datetime
    location_name: str | None = None
    location_address: str | None = None
    has_secret_santa: bool = False
    has_potluck: bool = False
    has_rsvp: bool = True
    # Potluck configuration
    potluck_mode: str | None = None  # 'organized' or 'open'
    potluck_host_providing: str | None = None
    # Secret Santa rules
    secret_santa_budget_min: int | None = None
    secret_santa_budget_max: int | None = None
    secret_santa_notes: str | None = None


class EventUpdate(BaseModel):
    """Update event request."""

    title: str | None = None
    description: str | None = None
    event_date: datetime | None = None
    location_name: str | None = None
    location_address: str | None = None
    has_secret_santa: bool | None = None
    has_potluck: bool | None = None
    has_rsvp: bool | None = None
    # Potluck configuration
    potluck_mode: str | None = None
    potluck_host_providing: str | None = None
    # Secret Santa rules
    secret_santa_budget_min: int | None = None
    secret_santa_budget_max: int | None = None
    secret_santa_notes: str | None = None


class EventResponse(BaseModel):
    """Event response."""

    id: str
    title: str
    description: str | None
    event_date: datetime
    location_name: str | None
    location_address: str | None
    has_secret_santa: bool
    has_potluck: bool
    has_rsvp: bool
    # Potluck configuration
    potluck_mode: str | None = None
    potluck_host_providing: str | None = None
    secret_santa_assigned: bool
    # Secret Santa rules
    secret_santa_budget_min: int | None = None
    secret_santa_budget_max: int | None = None
    secret_santa_notes: str | None = None
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
    member_name: str | None = None

    class Config:
        from_attributes = True
