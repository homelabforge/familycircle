"""Event-related schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.baby_shower import BabyShowerDetailCreate, BabyShowerDetailResponse
from app.schemas.birthday import BirthdayDetailCreate, BirthdayDetailResponse
from app.schemas.holiday import HolidayDetailCreate, HolidayDetailResponse
from app.schemas.wedding import WeddingDetailCreate, WeddingDetailResponse


class EventCreate(BaseModel):
    """Create event request."""

    title: str
    description: str | None = None
    event_date: datetime
    location_name: str | None = None
    location_address: str | None = None
    has_gift_exchange: bool = False
    has_potluck: bool = False
    has_rsvp: bool = True
    # Potluck configuration
    potluck_mode: str | None = None  # 'organized' or 'open'
    potluck_host_providing: str | None = None
    # Gift Exchange rules
    gift_exchange_budget_min: int | None = None
    gift_exchange_budget_max: int | None = None
    gift_exchange_notes: str | None = None
    # Event type (parent_event_id only set via POST /events/{id}/sub-events)
    event_type: str = "general"
    # Recurrence
    recurrence_type: str | None = None  # yearly, monthly, weekly
    recurrence_end_date: datetime | None = None
    recurrence_max_occurrences: int | None = None
    # Type-specific details
    holiday_detail: HolidayDetailCreate | None = None
    birthday_detail: BirthdayDetailCreate | None = None
    baby_shower_detail: BabyShowerDetailCreate | None = None
    wedding_detail: WeddingDetailCreate | None = None


class EventUpdate(BaseModel):
    """Update event request."""

    title: str | None = None
    description: str | None = None
    event_date: datetime | None = None
    location_name: str | None = None
    location_address: str | None = None
    has_gift_exchange: bool | None = None
    has_potluck: bool | None = None
    has_rsvp: bool | None = None
    # Potluck configuration
    potluck_mode: str | None = None
    potluck_host_providing: str | None = None
    # Gift Exchange rules
    gift_exchange_budget_min: int | None = None
    gift_exchange_budget_max: int | None = None
    gift_exchange_notes: str | None = None
    # Type-specific details (upsert on update)
    holiday_detail: HolidayDetailCreate | None = None
    birthday_detail: BirthdayDetailCreate | None = None
    baby_shower_detail: BabyShowerDetailCreate | None = None
    wedding_detail: WeddingDetailCreate | None = None


class EventResponse(BaseModel):
    """Event response."""

    id: str
    title: str
    description: str | None
    event_date: datetime
    location_name: str | None
    location_address: str | None
    has_gift_exchange: bool
    has_potluck: bool
    has_rsvp: bool
    # Potluck configuration
    potluck_mode: str | None = None
    potluck_host_providing: str | None = None
    gift_exchange_assigned: bool
    # Gift Exchange rules
    gift_exchange_budget_min: int | None = None
    gift_exchange_budget_max: int | None = None
    gift_exchange_notes: str | None = None
    # Event type
    event_type: str = "general"
    parent_event_id: str | None = None
    holiday_detail: HolidayDetailResponse | None = None
    birthday_detail: BirthdayDetailResponse | None = None
    baby_shower_detail: BabyShowerDetailResponse | None = None
    wedding_detail: WeddingDetailResponse | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)
