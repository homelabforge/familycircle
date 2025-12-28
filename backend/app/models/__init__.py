"""Database models package."""

from app.models.base import Base
from app.models.user import User
from app.models.family import Family
from app.models.family_membership import FamilyMembership, FamilyRole
from app.models.user_profile import UserProfile
from app.models.profile_visibility import ProfileVisibility
from app.models.event import Event, EventRSVP, RSVPStatus
from app.models.secret_santa import SecretSantaAssignment, SecretSantaExclusion, SecretSantaMessage
from app.models.potluck import PotluckItem
from app.models.wishlist import WishlistItem
from app.models.settings import Setting

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
    "RSVPStatus",
    # Secret Santa
    "SecretSantaAssignment",
    "SecretSantaExclusion",
    "SecretSantaMessage",
    # Other
    "PotluckItem",
    "WishlistItem",
    "Setting",
]
