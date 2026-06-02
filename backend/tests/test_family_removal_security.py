"""Security regression tests for family-removal access revocation (F2).

Two halves:
1. The load-bearing fix — require_family_context() must verify a LIVE
   FamilyMembership, so a stale current_family_id can never grant access.
2. The cleanup in remove_member() — switch the removed user's active family to
   one they still belong to and revoke their session tokens.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_family_context
from app.api.event_helpers import resolve_event_or_404
from app.api.family import remove_member
from app.models.event import Event, EventType
from app.models.family_membership import FamilyRole
from app.models.token import Token, TokenType
from app.services import auth as auth_service


def _uuid() -> str:
    return str(uuid.uuid4())


# ─── Load-bearing fix: require_family_context live-membership check ──────────


class TestRequireFamilyContextLiveMembership:
    """A non-null current_family_id is not enough — membership must be live."""

    async def test_stale_membership_is_rejected(self, db: AsyncSession):
        """current_family_id pointing at a non-member family → 400."""
        family = await auth_service.create_family(db, "Family")
        user = await auth_service.create_user(db, "stale@test.com", "pw123456")
        # Stale id: user is NOT a member of `family`
        user.current_family_id = family.id
        await db.commit()

        with pytest.raises(HTTPException) as exc:
            await require_family_context(user=user, db=db)
        assert exc.value.status_code == 400

    async def test_live_membership_is_allowed(self, db: AsyncSession):
        """A real membership for the active family passes."""
        family = await auth_service.create_family(db, "Family")
        user = await auth_service.create_user(db, "live@test.com", "pw123456")
        await auth_service.add_user_to_family(db, user, family, "Live")
        user.current_family_id = family.id
        await db.commit()

        result = await require_family_context(user=user, db=db)
        assert result is user

    async def test_no_family_context_is_rejected(self, db: AsyncSession):
        """current_family_id is None → 400 (unchanged behavior)."""
        user = await auth_service.create_user(db, "none@test.com", "pw123456")
        await db.commit()

        with pytest.raises(HTTPException) as exc:
            await require_family_context(user=user, db=db)
        assert exc.value.status_code == 400

    async def test_super_admin_bypasses_membership_check(self, db: AsyncSession):
        """Super admins short-circuit true even without a membership row."""
        family = await auth_service.create_family(db, "Family")
        user = await auth_service.create_user(db, "super@test.com", "pw123456", is_super_admin=True)
        user.current_family_id = family.id  # no membership, but super admin
        await db.commit()

        result = await require_family_context(user=user, db=db)
        assert result is user


# ─── Cleanup on removal: remove_member ──────────────────────────────────────


@pytest.fixture
async def removal_scenario(db: AsyncSession):
    """Admin of family A removes a member who also belongs to family B.

    The removed user's active context is family A and they hold a live session.
    Family A also has an event, to prove event access is revoked.
    """
    family_a = await auth_service.create_family(db, "Family A")
    family_b = await auth_service.create_family(db, "Family B")

    admin = await auth_service.create_user(db, "admin@test.com", "pw123456")
    await auth_service.add_user_to_family(db, admin, family_a, "Admin", FamilyRole.ADMIN)
    admin.current_family_id = family_a.id

    removed = await auth_service.create_user(db, "removed@test.com", "pw123456")
    await auth_service.add_user_to_family(db, removed, family_a, "Removed A")
    await auth_service.add_user_to_family(db, removed, family_b, "Removed B")
    removed.current_family_id = family_a.id

    # Live session for the removed user (must be revoked on removal)
    await auth_service.create_session(removed, db)

    event = Event(
        id=_uuid(),
        family_id=family_a.id,
        created_by_id=admin.id,
        event_type=EventType.GENERAL.value,
        title="Family A Dinner",
        event_date=datetime.now(UTC) + timedelta(days=1),
    )
    db.add(event)
    await db.commit()

    return {
        "admin": admin,
        "removed": removed,
        "family_a": family_a,
        "family_b": family_b,
        "event": event,
    }


class TestRemoveMemberCleanup:
    async def test_switches_current_family_to_remaining(
        self, db: AsyncSession, removal_scenario: dict
    ):
        """Active context moves to a family the user still belongs to (not NULL)."""
        s = removal_scenario
        await remove_member(user_id=s["removed"].id, admin=s["admin"], db=db)
        await db.refresh(s["removed"])
        assert s["removed"].current_family_id == s["family_b"].id

    async def test_revokes_session_tokens(self, db: AsyncSession, removal_scenario: dict):
        """The removed user's session tokens are deleted."""
        s = removal_scenario
        await remove_member(user_id=s["removed"].id, admin=s["admin"], db=db)
        remaining = (
            await db.execute(
                select(func.count())
                .select_from(Token)
                .where(
                    Token.user_id == s["removed"].id,
                    Token.token_type == TokenType.SESSION,
                )
            )
        ).scalar()
        assert remaining == 0

    async def test_event_access_revoked(self, db: AsyncSession, removal_scenario: dict):
        """After removal the user can no longer resolve family A's events."""
        s = removal_scenario
        await remove_member(user_id=s["removed"].id, admin=s["admin"], db=db)
        await db.refresh(s["removed"])
        with pytest.raises(HTTPException) as exc:
            await resolve_event_or_404(db, s["event"].id, s["removed"])
        assert exc.value.status_code == 404

    async def test_membership_actually_deleted(self, db: AsyncSession, removal_scenario: dict):
        """The family A membership row is gone (sanity check on the removal itself)."""
        s = removal_scenario
        await remove_member(user_id=s["removed"].id, admin=s["admin"], db=db)
        assert await auth_service.get_user_membership(db, s["removed"].id, s["family_a"].id) is None
