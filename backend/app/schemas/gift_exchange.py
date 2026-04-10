"""Gift Exchange schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GiftExchangeStatus(BaseModel):
    """Gift Exchange status for an event."""

    event_id: str
    is_assigned: bool
    assigned_at: datetime | None
    participant_count: int


class AssignmentResponse(BaseModel):
    """Your Gift Exchange assignment."""

    receiver_id: str
    receiver_name: str
    receiver_wishlist: list[WishlistItemResponse]


class ExclusionCreate(BaseModel):
    """Create exclusion rule."""

    member1_id: str
    member2_id: str


class ExclusionResponse(BaseModel):
    """Exclusion rule response."""

    id: str
    member1_id: str
    member1_name: str
    member2_id: str
    member2_name: str

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    """Send anonymous message."""

    message: str


class MessageResponse(BaseModel):
    """Message response."""

    id: str
    message: str
    is_from_me: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Import for forward reference
from app.schemas.wishlist import WishlistItemResponse  # noqa: E402

AssignmentResponse.model_rebuild()
