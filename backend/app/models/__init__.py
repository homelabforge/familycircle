"""Database models package."""

from app.models.baby_shower_detail import ALLOWED_GENDERS, BabyShowerDetail
from app.models.baby_shower_update import BABY_SHOWER_UPDATE_TYPES, BabyShowerUpdate
from app.models.base import Base
from app.models.birthday_detail import BirthdayDetail
from app.models.comment_mention import CommentMention
from app.models.comment_reaction import ALLOWED_EMOJIS, CommentReaction
from app.models.event import Event, EventRSVP, EventType, RSVPStatus
from app.models.event_comment import EventComment
from app.models.event_photo import EventPhoto
from app.models.event_recurrence import RECURRENCE_TYPES, EventRecurrence
from app.models.event_template import EventTemplate
from app.models.family import Family
from app.models.family_membership import FamilyMembership, FamilyRole
from app.models.gift_exchange import (
    GiftExchangeAssignment,
    GiftExchangeExclusion,
    GiftExchangeMessage,
)
from app.models.holiday_detail import PREDEFINED_HOLIDAYS, HolidayDetail
from app.models.poll import Poll, PollOption, PollVote
from app.models.poll_template import PollTemplate
from app.models.potluck import PotluckItem
from app.models.profile_visibility import ProfileVisibility
from app.models.registry_item import RegistryItem
from app.models.rsvp_guest import RSVPGuest
from app.models.settings import Setting
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.wedding_detail import WEDDING_PARTY_ROLES, WeddingDetail, WeddingPartyMember
from app.models.wedding_party_permission import WeddingPartyPermission
from app.models.wishlist import WishlistItem

__all__ = [
    "Base",
    # User & Family
    "User",
    "Family",
    "FamilyMembership",
    "FamilyRole",
    "UserProfile",
    "ProfileVisibility",
    # Events
    "Event",
    "EventRSVP",
    "EventType",
    "RSVPStatus",
    # Event type details
    "BabyShowerDetail",
    "ALLOWED_GENDERS",
    "BabyShowerUpdate",
    "BABY_SHOWER_UPDATE_TYPES",
    "BirthdayDetail",
    "HolidayDetail",
    "PREDEFINED_HOLIDAYS",
    "WeddingDetail",
    "WeddingPartyMember",
    "WeddingPartyPermission",
    "WEDDING_PARTY_ROLES",
    # Polls
    "Poll",
    "PollOption",
    "PollVote",
    "PollTemplate",
    # Comments
    "EventComment",
    "CommentReaction",
    "CommentMention",
    "ALLOWED_EMOJIS",
    # Photos
    "EventPhoto",
    # Gift Exchange
    "GiftExchangeAssignment",
    "GiftExchangeExclusion",
    "GiftExchangeMessage",
    # Registry
    "RegistryItem",
    # RSVP Guests
    "RSVPGuest",
    # Recurrence
    "EventRecurrence",
    "RECURRENCE_TYPES",
    # Templates
    "EventTemplate",
    # Other
    "PotluckItem",
    "WishlistItem",
    "Setting",
]
