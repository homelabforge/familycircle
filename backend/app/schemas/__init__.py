"""Pydantic schemas package."""

from app.schemas.auth import (
    MemberResponse,
    MagicLinkRequest,
    MagicLinkVerify,
    OrganizerLogin,
    JoinFamilyRequest,
)
from app.schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    RSVPRequest,
    RSVPResponse,
)
from app.schemas.wishlist import (
    WishlistItemCreate,
    WishlistItemUpdate,
    WishlistItemResponse,
)
from app.schemas.potluck import (
    PotluckItemCreate,
    PotluckItemResponse,
)
from app.schemas.secret_santa import (
    SecretSantaStatus,
    AssignmentResponse,
    ExclusionCreate,
    MessageCreate,
    MessageResponse,
)

__all__ = [
    "MemberResponse",
    "MagicLinkRequest",
    "MagicLinkVerify",
    "OrganizerLogin",
    "JoinFamilyRequest",
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    "RSVPRequest",
    "RSVPResponse",
    "WishlistItemCreate",
    "WishlistItemUpdate",
    "WishlistItemResponse",
    "PotluckItemCreate",
    "PotluckItemResponse",
    "SecretSantaStatus",
    "AssignmentResponse",
    "ExclusionCreate",
    "MessageCreate",
    "MessageResponse",
]
