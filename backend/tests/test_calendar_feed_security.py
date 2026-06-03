"""Security regression tests for the family calendar feed (F8).

The .ics feed is authed only by a bearer token in the URL. On member removal the
token must rotate (so the removed member's subscription stops resolving), and the
feed response must be non-cacheable so a CDN cannot keep serving the old token.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.calendar import family_calendar_feed
from app.api.family import remove_member
from app.models.event import Event, EventType
from app.models.family_membership import FamilyRole
from app.services import auth as auth_service


def _uuid() -> str:
    return str(uuid.uuid4())


@pytest.fixture
async def feed_scenario(db: AsyncSession):
    """Family A (with a feed token) + an admin and a two-family member to remove."""
    family_a = await auth_service.create_family(db, "A")
    family_a.calendar_feed_token = auth_service.generate_calendar_feed_token()
    family_b = await auth_service.create_family(db, "B")

    admin = await auth_service.create_user(db, "admin@test.com", "pw123456")
    await auth_service.add_user_to_family(db, admin, family_a, "Admin", FamilyRole.ADMIN)
    admin.current_family_id = family_a.id

    removed = await auth_service.create_user(db, "removed@test.com", "pw123456")
    await auth_service.add_user_to_family(db, removed, family_a, "Removed A")
    await auth_service.add_user_to_family(db, removed, family_b, "Removed B")
    removed.current_family_id = family_a.id

    db.add(
        Event(
            id=_uuid(),
            family_id=family_a.id,
            created_by_id=admin.id,
            event_type=EventType.GENERAL.value,
            title="A Event",
            event_date=datetime.now(UTC) + timedelta(days=1),
        )
    )
    await db.commit()

    return {"family_a": family_a, "admin": admin, "removed": removed}


class TestCalendarFeedSecurity:
    async def test_feed_response_is_not_cacheable(self, db: AsyncSession, feed_scenario: dict):
        """The feed carries a non-cacheable Cache-Control header."""
        s = feed_scenario
        resp = await family_calendar_feed(feed_token=s["family_a"].calendar_feed_token, db=db)
        assert resp.headers["cache-control"] == "private, no-store"

    async def test_old_token_404s_after_removal(self, db: AsyncSession, feed_scenario: dict):
        """The removed member's old feed URL stops resolving at the origin."""
        s = feed_scenario
        old_token = s["family_a"].calendar_feed_token
        await remove_member(user_id=s["removed"].id, admin=s["admin"], db=db)

        with pytest.raises(HTTPException) as exc:
            await family_calendar_feed(feed_token=old_token, db=db)
        assert exc.value.status_code == 404

    async def test_new_token_serves_after_removal(self, db: AsyncSession, feed_scenario: dict):
        """The rotated token still serves the family's feed."""
        s = feed_scenario
        old_token = s["family_a"].calendar_feed_token
        await remove_member(user_id=s["removed"].id, admin=s["admin"], db=db)
        await db.refresh(s["family_a"])

        new_token = s["family_a"].calendar_feed_token
        assert new_token != old_token
        resp = await family_calendar_feed(feed_token=new_token, db=db)
        assert resp.status_code == 200
