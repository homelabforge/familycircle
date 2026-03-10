"""Security regression tests for event access control.

Validates:
- Strict tenant boundary: events only accessible in active family context
- Secret birthday concealment: birthday person cannot see their surprise event
- Super admin bypass: super admins can access all events
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.event_helpers import resolve_event_or_404

# ─── Tenant boundary: resolve_event_or_404 ────────────────────────────────


class TestTenantBoundary:
    """User in two families cannot access events outside active family context."""

    async def test_access_event_in_current_family(
        self, db: AsyncSession, two_family_scenario: dict
    ):
        """User can access events in their current family context."""
        s = two_family_scenario
        # User context is Family B, event_b is in Family B → should succeed
        event = await resolve_event_or_404(db, s["event_b"].id, s["user"])
        assert event.id == s["event_b"].id

    async def test_cross_family_event_returns_404(
        self, db: AsyncSession, two_family_scenario: dict
    ):
        """User cannot access events from a different family than their active context."""
        s = two_family_scenario
        # User context is Family B, event_a is in Family A → should 404
        with pytest.raises(HTTPException) as exc_info:
            await resolve_event_or_404(db, s["event_a"].id, s["user"])
        assert exc_info.value.status_code == 404

    async def test_nonexistent_event_returns_404(self, db: AsyncSession, two_family_scenario: dict):
        """Nonexistent event ID returns 404."""
        s = two_family_scenario
        with pytest.raises(HTTPException) as exc_info:
            await resolve_event_or_404(db, "nonexistent-id", s["user"])
        assert exc_info.value.status_code == 404


# ─── Secret birthday concealment ──────────────────────────────────────────


class TestSecretBirthdayConcealment:
    """Birthday person cannot see their secret birthday event."""

    async def test_birthday_person_gets_404(self, db: AsyncSession, secret_birthday_scenario: dict):
        """Birthday person cannot see their own secret birthday event."""
        s = secret_birthday_scenario
        with pytest.raises(HTTPException) as exc_info:
            await resolve_event_or_404(db, s["secret_event"].id, s["birthday_person"])
        assert exc_info.value.status_code == 404

    async def test_organizer_can_see_secret_birthday(
        self, db: AsyncSession, secret_birthday_scenario: dict
    ):
        """Organizer (non-birthday person) can see the secret birthday event."""
        s = secret_birthday_scenario
        event = await resolve_event_or_404(db, s["secret_event"].id, s["organizer"])
        assert event.id == s["secret_event"].id

    async def test_super_admin_can_see_secret_birthday(
        self, db: AsyncSession, secret_birthday_scenario: dict
    ):
        """Super admin bypasses secret birthday filter."""
        s = secret_birthday_scenario
        event = await resolve_event_or_404(db, s["secret_event"].id, s["super_admin"])
        assert event.id == s["secret_event"].id


# ─── Super admin bypass ──────────────────────────────────────────────────


class TestSuperAdminBypass:
    """Super admin can access events across family boundaries."""

    async def test_super_admin_cross_family_access(
        self, db: AsyncSession, two_family_scenario: dict
    ):
        """Super admin can access events outside their current family context."""
        s = two_family_scenario
        # Make user a super admin with context in Family B
        s["user"].is_super_admin = True
        # Should access event_a (Family A) even though context is Family B
        event = await resolve_event_or_404(db, s["event_a"].id, s["user"])
        assert event.id == s["event_a"].id


# ─── SQLAlchemy options passthrough ───────────────────────────────────────


class TestOptionsPassthrough:
    """Verify that loader options are applied to the query."""

    async def test_options_parameter_works(self, db: AsyncSession, two_family_scenario: dict):
        """Options parameter does not break the query."""
        from sqlalchemy.orm import selectinload

        from app.models.event import Event

        s = two_family_scenario
        event = await resolve_event_or_404(
            db, s["event_b"].id, s["user"], options=[selectinload(Event.rsvps)]
        )
        assert event.id == s["event_b"].id
        # rsvps should be loaded (empty list, not lazy-load proxy)
        assert event.rsvps == []
