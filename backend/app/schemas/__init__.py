"""Pydantic schemas package."""

from app.schemas.auth import (
    JoinFamilyRequest,
    MagicLinkRequest,
    MagicLinkVerify,
    MemberResponse,
    OrganizerLogin,
)
from app.schemas.event import (
    EventCreate,
    EventResponse,
    EventUpdate,
    RSVPRequest,
    RSVPResponse,
)
from app.schemas.potluck import (
    PotluckItemCreate,
    PotluckItemResponse,
)
from app.schemas.secret_santa import (
    AssignmentResponse,
    ExclusionCreate,
    MessageCreate,
    MessageResponse,
    SecretSantaStatus,
)
from app.schemas.wishlist import (
    WishlistItemCreate,
    WishlistItemResponse,
    WishlistItemUpdate,
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
