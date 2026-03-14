"""Tests for the permission service."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventType
from app.models.family import Family
from app.models.family_membership import FamilyMembership, FamilyRole
from app.models.user import User
from app.models.wedding_detail import WeddingDetail, WeddingPartyMember
from app.models.wedding_party_permission import WeddingPartyPermission
from app.services.permissions import PermissionService


def _uuid() -> str:
    return str(uuid.uuid4())


@pytest.fixture
async def permission_scenario(db: AsyncSession):
    """Family with admin, member, super_admin, and an event created by member."""
    family = Family(id=_uuid(), name="Perm Family", family_code="PERM01")
    other_family = Family(id=_uuid(), name="Other Family", family_code="OTHER1")

    admin = User(
        id=_uuid(), email="admin@test.com", is_super_admin=False, current_family_id=family.id
    )
    member = User(
        id=_uuid(), email="member@test.com", is_super_admin=False, current_family_id=family.id
    )
    super_admin = User(
        id=_uuid(), email="super@test.com", is_super_admin=True, current_family_id=family.id
    )
    outsider = User(
        id=_uuid(),
        email="outsider@test.com",
        is_super_admin=False,
        current_family_id=other_family.id,
    )

    db.add_all([family, other_family, admin, member, super_admin, outsider])

    db.add(
        FamilyMembership(
            id=_uuid(),
            user_id=admin.id,
            family_id=family.id,
            role=FamilyRole.ADMIN,
            display_name="Admin",
        )
    )
    db.add(
        FamilyMembership(
            id=_uuid(),
            user_id=member.id,
            family_id=family.id,
            role=FamilyRole.MEMBER,
            display_name="Member",
        )
    )
    db.add(
        FamilyMembership(
            id=_uuid(),
            user_id=super_admin.id,
            family_id=family.id,
            role=FamilyRole.MEMBER,
            display_name="Super",
        )
    )
    db.add(
        FamilyMembership(
            id=_uuid(),
            user_id=outsider.id,
            family_id=other_family.id,
            role=FamilyRole.ADMIN,
            display_name="Outsider",
        )
    )

    from datetime import UTC, datetime, timedelta

    event = Event(
        id=_uuid(),
        family_id=family.id,
        created_by_id=member.id,
        event_type=EventType.GENERAL.value,
        title="Member's Event",
        event_date=datetime.now(UTC) + timedelta(days=1),
    )
    db.add(event)
    await db.commit()

    return {
        "family": family,
        "other_family": other_family,
        "admin": admin,
        "member": member,
        "super_admin": super_admin,
        "outsider": outsider,
        "event": event,
    }


class TestIsSuperAdmin:
    async def test_true_for_super_admin(self, permission_scenario):
        assert PermissionService.is_super_admin(permission_scenario["super_admin"]) is True

    async def test_false_for_regular_user(self, permission_scenario):
        assert PermissionService.is_super_admin(permission_scenario["member"]) is False

    async def test_false_for_family_admin(self, permission_scenario):
        assert PermissionService.is_super_admin(permission_scenario["admin"]) is False


class TestIsFamilyAdmin:
    async def test_admin_role_returns_true(self, db, permission_scenario):
        s = permission_scenario
        assert await PermissionService.is_family_admin(db, s["admin"], s["family"].id) is True

    async def test_member_role_returns_false(self, db, permission_scenario):
        s = permission_scenario
        assert await PermissionService.is_family_admin(db, s["member"], s["family"].id) is False

    async def test_super_admin_bypass(self, db, permission_scenario):
        s = permission_scenario
        assert await PermissionService.is_family_admin(db, s["super_admin"], s["family"].id) is True

    async def test_admin_of_other_family_returns_false(self, db, permission_scenario):
        s = permission_scenario
        assert await PermissionService.is_family_admin(db, s["outsider"], s["family"].id) is False


class TestIsFamilyMember:
    async def test_member_returns_true(self, db, permission_scenario):
        s = permission_scenario
        assert await PermissionService.is_family_member(db, s["member"], s["family"].id) is True

    async def test_non_member_returns_false(self, db, permission_scenario):
        s = permission_scenario
        assert await PermissionService.is_family_member(db, s["outsider"], s["family"].id) is False

    async def test_super_admin_bypass(self, db, permission_scenario):
        s = permission_scenario
        # Super admin is treated as member of any family
        assert (
            await PermissionService.is_family_member(db, s["super_admin"], s["other_family"].id)
            is True
        )


class TestCanManageEvent:
    async def test_creator_can_manage(self, db, permission_scenario):
        s = permission_scenario
        assert await PermissionService.can_manage_event(db, s["member"], s["event"]) is True

    async def test_family_admin_can_manage(self, db, permission_scenario):
        s = permission_scenario
        assert await PermissionService.can_manage_event(db, s["admin"], s["event"]) is True

    async def test_super_admin_can_manage(self, db, permission_scenario):
        s = permission_scenario
        assert await PermissionService.can_manage_event(db, s["super_admin"], s["event"]) is True

    async def test_random_member_cannot_manage(self, db, permission_scenario):
        s = permission_scenario
        assert await PermissionService.can_manage_event(db, s["outsider"], s["event"]) is False


class TestCanResetUserPassword:
    async def test_super_admin_can_reset_anyone(self, db, permission_scenario):
        s = permission_scenario
        assert (
            await PermissionService.can_reset_user_password(
                db, s["super_admin"], s["member"], s["family"].id
            )
            is True
        )

    async def test_family_admin_can_reset_own_family_member(self, db, permission_scenario):
        s = permission_scenario
        assert (
            await PermissionService.can_reset_user_password(
                db, s["admin"], s["member"], s["family"].id
            )
            is True
        )

    async def test_family_admin_cannot_reset_other_family_member(self, db, permission_scenario):
        s = permission_scenario
        assert (
            await PermissionService.can_reset_user_password(
                db, s["admin"], s["outsider"], s["family"].id
            )
            is False
        )

    async def test_regular_member_cannot_reset(self, db, permission_scenario):
        s = permission_scenario
        assert (
            await PermissionService.can_reset_user_password(
                db, s["member"], s["admin"], s["family"].id
            )
            is False
        )


class TestWeddingPermissions:
    @pytest.fixture
    async def wedding_scenario(self, db: AsyncSession, permission_scenario):
        """Add a wedding event with a party member who has permissions."""
        s = permission_scenario
        from datetime import UTC, datetime, timedelta

        wedding_event = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["admin"].id,
            event_type=EventType.WEDDING.value,
            title="Wedding",
            event_date=datetime.now(UTC) + timedelta(days=30),
        )
        wedding_detail = WeddingDetail(
            id=_uuid(),
            event_id=wedding_event.id,
            partner1_name="Alice",
            partner2_name="Bob",
        )
        party_member = WeddingPartyMember(
            id=_uuid(),
            event_id=wedding_event.id,
            user_id=s["member"].id,
            name="Member",
            role="best_man",
        )
        permission_with = WeddingPartyPermission(
            id=_uuid(),
            member_id=party_member.id,
            can_manage_sub_events=True,
            can_view_rsvps=True,
            can_post_updates=False,
        )

        # Another party member WITHOUT permissions
        party_member_no_perms = WeddingPartyMember(
            id=_uuid(),
            event_id=wedding_event.id,
            user_id=s["outsider"].id,
            name="Outsider",
            role="groomsman",
        )
        permission_without = WeddingPartyPermission(
            id=_uuid(),
            member_id=party_member_no_perms.id,
            can_manage_sub_events=False,
            can_view_rsvps=False,
            can_post_updates=False,
        )

        db.add_all(
            [
                wedding_event,
                wedding_detail,
                party_member,
                permission_with,
                party_member_no_perms,
                permission_without,
            ]
        )
        await db.commit()

        return {**s, "wedding_event": wedding_event}

    async def test_party_member_with_permission_can_manage_sub_events(self, db, wedding_scenario):
        s = wedding_scenario
        assert (
            await PermissionService.can_manage_wedding_sub_events(
                db, s["member"], s["wedding_event"]
            )
            is True
        )

    async def test_party_member_without_permission_cannot_manage_sub_events(
        self, db, wedding_scenario
    ):
        s = wedding_scenario
        assert (
            await PermissionService.can_manage_wedding_sub_events(
                db, s["outsider"], s["wedding_event"]
            )
            is False
        )

    async def test_party_member_with_permission_can_view_rsvps(self, db, wedding_scenario):
        s = wedding_scenario
        assert (
            await PermissionService.can_view_wedding_rsvps(db, s["member"], s["wedding_event"])
            is True
        )

    async def test_party_member_without_permission_cannot_view_rsvps(self, db, wedding_scenario):
        s = wedding_scenario
        assert (
            await PermissionService.can_view_wedding_rsvps(db, s["outsider"], s["wedding_event"])
            is False
        )

    async def test_event_creator_always_can(self, db, wedding_scenario):
        s = wedding_scenario
        # Admin created the wedding event
        assert (
            await PermissionService.can_manage_wedding_sub_events(
                db, s["admin"], s["wedding_event"]
            )
            is True
        )
        assert (
            await PermissionService.can_view_wedding_rsvps(db, s["admin"], s["wedding_event"])
            is True
        )
