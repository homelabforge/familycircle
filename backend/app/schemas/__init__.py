"""Pydantic schemas package."""

from app.schemas.auth import (
    JoinFamilyRequest,
    MagicLinkRequest,
    MagicLinkVerify,
    MemberResponse,
    OrganizerLogin,
)
from app.schemas.baby_shower import (
    BabyShowerDetailCreate,
    BabyShowerDetailResponse,
)
from app.schemas.birthday import (
    BirthdayDetailCreate,
    BirthdayDetailResponse,
)
from app.schemas.event import (
    EventCreate,
    EventResponse,
    EventUpdate,
    RSVPRequest,
    RSVPResponse,
)
from app.schemas.event_comment import (
    EventCommentCreate,
    EventCommentResponse,
    EventCommentUpdate,
)
from app.schemas.gift_exchange import (
    AssignmentResponse,
    ExclusionCreate,
    GiftExchangeStatus,
    MessageCreate,
    MessageResponse,
)
from app.schemas.holiday import (
    HolidayDetailCreate,
    HolidayDetailResponse,
)
from app.schemas.poll import (
    PollCreate,
    PollOptionCreate,
    PollOptionResponse,
    PollResponse,
    PollVoteRequest,
)
from app.schemas.potluck import (
    PotluckItemCreate,
    PotluckItemResponse,
)
from app.schemas.wedding import (
    WeddingDetailCreate,
    WeddingDetailResponse,
    WeddingPartyMemberCreate,
    WeddingPartyMemberResponse,
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
    "BirthdayDetailCreate",
    "BirthdayDetailResponse",
    "BabyShowerDetailCreate",
    "BabyShowerDetailResponse",
    "HolidayDetailCreate",
    "HolidayDetailResponse",
    "WeddingDetailCreate",
    "WeddingDetailResponse",
    "WeddingPartyMemberCreate",
    "WeddingPartyMemberResponse",
    "WishlistItemCreate",
    "WishlistItemUpdate",
    "WishlistItemResponse",
    "PotluckItemCreate",
    "PotluckItemResponse",
    "GiftExchangeStatus",
    "AssignmentResponse",
    "ExclusionCreate",
    "MessageCreate",
    "MessageResponse",
    # Polls
    "PollCreate",
    "PollOptionCreate",
    "PollOptionResponse",
    "PollResponse",
    "PollVoteRequest",
    # Event Comments
    "EventCommentCreate",
    "EventCommentUpdate",
    "EventCommentResponse",
]
