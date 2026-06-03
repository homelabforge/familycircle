"""Security regression tests for privilege-escalating admin password resets (N1).

A family admin may reset only ordinary MEMBER passwords. They must NOT be able
to reset a super-admin's or a peer-admin's password (which would let them seize
those accounts). Super admins retain unrestricted reset.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import admin_reset_password
from app.models.family_membership import FamilyRole
from app.schemas.auth import AdminResetPasswordRequest
from app.services import auth as auth_service


@pytest.fixture
async def reset_scenario(db: AsyncSession):
    """One family containing a super admin, two family admins, and a member."""
    family = await auth_service.create_family(db, "Family")

    super_admin = await auth_service.create_user(
        db, "super@test.com", "pw123456", is_super_admin=True
    )
    await auth_service.add_user_to_family(db, super_admin, family, "Super", FamilyRole.ADMIN)
    super_admin.current_family_id = family.id

    family_admin = await auth_service.create_user(db, "fadmin@test.com", "pw123456")
    await auth_service.add_user_to_family(db, family_admin, family, "FamAdmin", FamilyRole.ADMIN)
    family_admin.current_family_id = family.id

    peer_admin = await auth_service.create_user(db, "peer@test.com", "pw123456")
    await auth_service.add_user_to_family(db, peer_admin, family, "PeerAdmin", FamilyRole.ADMIN)
    peer_admin.current_family_id = family.id

    member = await auth_service.create_user(db, "member@test.com", "pw123456")
    await auth_service.add_user_to_family(db, member, family, "Member", FamilyRole.MEMBER)
    member.current_family_id = family.id

    await db.commit()

    return {
        "family": family,
        "super_admin": super_admin,
        "family_admin": family_admin,
        "peer_admin": peer_admin,
        "member": member,
    }


class TestAdminResetPrivilegeGuard:
    async def test_family_admin_cannot_reset_super_admin(
        self, db: AsyncSession, reset_scenario: dict
    ):
        """(a) family-admin → super-admin = 403."""
        s = reset_scenario
        old_hash = s["super_admin"].password_hash
        with pytest.raises(HTTPException) as exc:
            await admin_reset_password(
                request=AdminResetPasswordRequest(
                    user_id=s["super_admin"].id, new_password="hijacked123"
                ),
                admin=s["family_admin"],
                db=db,
            )
        assert exc.value.status_code == 403
        # Password untouched
        await db.refresh(s["super_admin"])
        assert s["super_admin"].password_hash == old_hash

    async def test_family_admin_cannot_reset_peer_admin(
        self, db: AsyncSession, reset_scenario: dict
    ):
        """(b) family-admin → peer-admin = 403."""
        s = reset_scenario
        old_hash = s["peer_admin"].password_hash
        with pytest.raises(HTTPException) as exc:
            await admin_reset_password(
                request=AdminResetPasswordRequest(
                    user_id=s["peer_admin"].id, new_password="hijacked123"
                ),
                admin=s["family_admin"],
                db=db,
            )
        assert exc.value.status_code == 403
        await db.refresh(s["peer_admin"])
        assert s["peer_admin"].password_hash == old_hash

    async def test_family_admin_can_reset_member(self, db: AsyncSession, reset_scenario: dict):
        """(c) family-admin → member = 200, password actually changes."""
        s = reset_scenario
        old_hash = s["member"].password_hash
        result = await admin_reset_password(
            request=AdminResetPasswordRequest(user_id=s["member"].id, new_password="newpass123"),
            admin=s["family_admin"],
            db=db,
        )
        assert "successfully" in result["message"].lower()
        # Handler is flush-only (request-level commit happens in prod); assert the
        # in-memory re-hash took effect rather than refreshing back to committed state.
        assert s["member"].password_hash != old_hash

    async def test_super_admin_can_reset_admin(self, db: AsyncSession, reset_scenario: dict):
        """(d) super-admin → anyone (incl. a peer admin) = 200."""
        s = reset_scenario
        old_hash = s["peer_admin"].password_hash
        result = await admin_reset_password(
            request=AdminResetPasswordRequest(
                user_id=s["peer_admin"].id, new_password="newpass123"
            ),
            admin=s["super_admin"],
            db=db,
        )
        assert "successfully" in result["message"].lower()
        # Flush-only handler: assert the in-memory re-hash rather than refreshing.
        assert s["peer_admin"].password_hash != old_hash
