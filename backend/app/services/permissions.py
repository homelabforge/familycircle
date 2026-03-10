"""Permission service - role-based access control for multi-family system."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Event,
    FamilyMembership,
    FamilyRole,
    User,
)
from app.models.wedding_detail import WeddingPartyMember
from app.models.wedding_party_permission import WeddingPartyPermission


class PermissionService:
    """Service for checking user permissions."""

    @staticmethod
    def is_super_admin(user: User) -> bool:
        """Check if user is a super admin."""
        return user.is_super_admin

    @staticmethod
    async def is_family_admin(session: AsyncSession, user: User, family_id: str) -> bool:
        """Check if user is an admin of the specified family."""
        if user.is_super_admin:
            return True

        result = await session.execute(
            select(FamilyMembership).where(
                FamilyMembership.user_id == user.id,
                FamilyMembership.family_id == family_id,
                FamilyMembership.role == FamilyRole.ADMIN,
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def is_family_member(session: AsyncSession, user: User, family_id: str) -> bool:
        """Check if user is a member of the specified family."""
        if user.is_super_admin:
            return True

        result = await session.execute(
            select(FamilyMembership).where(
                FamilyMembership.user_id == user.id,
                FamilyMembership.family_id == family_id,
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def can_manage_family(session: AsyncSession, user: User, family_id: str) -> bool:
        """Check if user can manage family settings and members."""
        return await PermissionService.is_family_admin(session, user, family_id)

    @staticmethod
    async def can_view_family(session: AsyncSession, user: User, family_id: str) -> bool:
        """Check if user can view family data."""
        return await PermissionService.is_family_member(session, user, family_id)

    @staticmethod
    async def can_manage_event(session: AsyncSession, user: User, event: Event) -> bool:
        """
        Check if user can edit/delete an event.
        - Super admin can manage any event
        - Family admin can manage any event in their family
        - Event creator can manage their own event
        """
        if user.is_super_admin:
            return True

        # Check if user is family admin
        if await PermissionService.is_family_admin(session, user, event.family_id):
            return True

        # Check if user is the event creator
        if event.created_by_id == user.id:
            return True

        return False

    @staticmethod
    async def can_view_health_summary(session: AsyncSession, user: User, event: Event) -> bool:
        """
        Check if user can view health/allergy summary for an event.
        Only event creator and family admins can see this.
        """
        if user.is_super_admin:
            return True

        if await PermissionService.is_family_admin(session, user, event.family_id):
            return True

        if event.created_by_id == user.id:
            return True

        return False

    @staticmethod
    async def can_view_member_profile(
        session: AsyncSession, user: User, target_user_id: str, family_id: str
    ) -> bool:
        """
        Check if user can view another member's profile in a family.
        Must be a member of the same family.
        """
        if user.is_super_admin:
            return True

        # Check both users are in the same family
        user_in_family = await PermissionService.is_family_member(session, user, family_id)
        if not user_in_family:
            return False

        # Check target is also in the family
        result = await session.execute(
            select(FamilyMembership).where(
                FamilyMembership.user_id == target_user_id,
                FamilyMembership.family_id == family_id,
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def can_reset_user_password(
        session: AsyncSession, admin: User, target_user: User, family_id: str
    ) -> bool:
        """
        Check if admin can reset another user's password.
        - Super admin can reset anyone's password
        - Family admin can reset passwords for their family members
        """
        if admin.is_super_admin:
            return True

        # Check admin is family admin
        if not await PermissionService.is_family_admin(session, admin, family_id):
            return False

        # Check target is in the same family
        result = await session.execute(
            select(FamilyMembership).where(
                FamilyMembership.user_id == target_user.id,
                FamilyMembership.family_id == family_id,
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_user_role_in_family(
        session: AsyncSession, user: User, family_id: str
    ) -> str | None:
        """Get user's role in a specific family."""
        if user.is_super_admin:
            return "super_admin"

        result = await session.execute(
            select(FamilyMembership).where(
                FamilyMembership.user_id == user.id,
                FamilyMembership.family_id == family_id,
            )
        )
        membership = result.scalar_one_or_none()
        return membership.role.value if membership else None

    @staticmethod
    async def can_manage_wedding_sub_events(
        session: AsyncSession, user: User, event: Event
    ) -> bool:
        """Check if user can manage sub-events for a wedding.

        Allowed for: super admin, family admin, event creator,
        or wedding party members with can_manage_sub_events permission.
        """
        if await PermissionService.can_manage_event(session, user, event):
            return True

        # Check wedding party permissions
        result = await session.execute(
            select(WeddingPartyPermission)
            .join(WeddingPartyMember)
            .where(
                WeddingPartyMember.event_id == event.id,
                WeddingPartyMember.user_id == user.id,
                WeddingPartyPermission.can_manage_sub_events.is_(True),
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def can_view_wedding_rsvps(session: AsyncSession, user: User, event: Event) -> bool:
        """Check if user can view RSVP details for a wedding.

        Allowed for: super admin, family admin, event creator,
        or wedding party members with can_view_rsvps permission.
        """
        if await PermissionService.can_manage_event(session, user, event):
            return True

        result = await session.execute(
            select(WeddingPartyPermission)
            .join(WeddingPartyMember)
            .where(
                WeddingPartyMember.event_id == event.id,
                WeddingPartyMember.user_id == user.id,
                WeddingPartyPermission.can_view_rsvps.is_(True),
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def can_post_wedding_updates(session: AsyncSession, user: User, event: Event) -> bool:
        """Check if user can post updates for a wedding.

        Allowed for: super admin, family admin, event creator,
        or wedding party members with can_post_updates permission.
        """
        if await PermissionService.can_manage_event(session, user, event):
            return True

        result = await session.execute(
            select(WeddingPartyPermission)
            .join(WeddingPartyMember)
            .where(
                WeddingPartyMember.event_id == event.id,
                WeddingPartyMember.user_id == user.id,
                WeddingPartyPermission.can_post_updates.is_(True),
            )
        )
        return result.scalar_one_or_none() is not None


# Singleton instance for convenience
permissions = PermissionService()
