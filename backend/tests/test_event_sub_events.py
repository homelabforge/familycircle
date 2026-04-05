"""Regression tests for MissingGreenlet (event sub_events) and magic-link arg wiring."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.auth import forgot_password
from app.api.events import EVENT_DICT_OPTIONS, event_to_dict
from app.models.event import Event, EventType
from app.models.user import User
from app.schemas.auth import ForgotPasswordRequest


def _uuid() -> str:
    return str(uuid.uuid4())


def _tomorrow() -> datetime:
    return datetime.now(UTC) + timedelta(days=1)


def _make_request() -> Request:
    """Minimal Starlette Request with a valid base_url."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/auth/magic-link",
        "headers": [],
        "query_string": b"",
        "root_path": "",
        "scheme": "http",
        "server": ("testserver", 80),
    }
    return Request(scope)


# ─── Fix 1: event_to_dict with sub_events ─────────────────────────────────────


class TestEventToDictSubEvents:
    """event_to_dict must not raise MissingGreenlet when sub_events are present."""

    async def test_event_to_dict_no_sub_events(self, db: AsyncSession, two_family_scenario: dict):
        """Baseline: event with no sub-events works fine."""
        s = two_family_scenario
        result = await db.execute(
            select(Event).where(Event.id == s["event_b"].id).options(*EVENT_DICT_OPTIONS)
        )
        parent = result.scalar_one()

        data = event_to_dict(parent)
        assert data["sub_event_count"] == 0
        assert data["sub_events"] == []

    async def test_event_to_dict_with_sub_events_does_not_raise(
        self, db: AsyncSession, two_family_scenario: dict
    ):
        """event_to_dict with a sub-event present must not raise MissingGreenlet."""
        s = two_family_scenario
        sub = Event(
            id=_uuid(),
            family_id=s["family_b"].id,
            created_by_id=s["user"].id,
            event_type=EventType.GENERAL.value,
            title="Rehearsal Dinner",
            event_date=_tomorrow(),
            parent_event_id=str(s["event_b"].id),
        )
        db.add(sub)
        await db.commit()

        # Query with explicit eager load — this is the fix
        result = await db.execute(
            select(Event).where(Event.id == s["event_b"].id).options(*EVENT_DICT_OPTIONS)
        )
        parent = result.scalar_one()

        # Must not raise MissingGreenlet
        data = event_to_dict(parent)
        assert data["sub_event_count"] == 1
        assert len(data["sub_events"]) == 1
        assert data["sub_events"][0]["title"] == "Rehearsal Dinner"

    async def test_event_to_dict_cancelled_sub_events_excluded_from_count(
        self, db: AsyncSession, two_family_scenario: dict
    ):
        """Cancelled sub-events must not count toward sub_event_count."""
        s = two_family_scenario
        sub_active = Event(
            id=_uuid(),
            family_id=s["family_b"].id,
            created_by_id=s["user"].id,
            event_type=EventType.GENERAL.value,
            title="Active Sub",
            event_date=_tomorrow(),
            parent_event_id=str(s["event_b"].id),
        )
        sub_cancelled = Event(
            id=_uuid(),
            family_id=s["family_b"].id,
            created_by_id=s["user"].id,
            event_type=EventType.GENERAL.value,
            title="Cancelled Sub",
            event_date=_tomorrow(),
            parent_event_id=str(s["event_b"].id),
            cancelled_at=datetime.now(UTC),
        )
        db.add_all([sub_active, sub_cancelled])
        await db.commit()

        result = await db.execute(
            select(Event).where(Event.id == s["event_b"].id).options(*EVENT_DICT_OPTIONS)
        )
        parent = result.scalar_one()

        data = event_to_dict(parent)
        assert data["sub_event_count"] == 1  # Only the active one
        assert len(data["sub_events"]) == 2  # Both present in raw list


# ─── Fix 2: forgot_password / magic-link arg wiring ───────────────────────────


class TestMagicLinkArgWiring:
    """forgot_password must receive a real Request, not the db session."""

    async def test_forgot_password_non_existent_email_returns_safe_message(self, db: AsyncSession):
        """Non-existent email returns the safe 'if account exists' envelope."""
        req = _make_request()
        body = ForgotPasswordRequest(email="nobody@example.com")

        result = await forgot_password(request=req, body=body, db=db)
        assert "message" in result
        assert "nobody@example.com" in result["message"]

    async def test_forgot_password_existing_user_accesses_req_base_url(self, db: AsyncSession):
        """When user exists, token is generated and base_url is read from Request.

        Regression: the old send_magic_link passed db as req, causing
        AttributeError on db.base_url. This test verifies the function
        runs to completion when called with a real Request.
        """
        user = User(
            id=_uuid(),
            email="reset@example.com",
            is_super_admin=False,
        )
        db.add(user)
        await db.commit()

        req = _make_request()
        body = ForgotPasswordRequest(email="reset@example.com")

        # This would crash with AttributeError('AsyncSession has no attribute base_url')
        # if send_magic_link were still passing db as req
        result = await forgot_password(request=req, body=body, db=db)
        assert "message" in result
        # SMTP not configured, but DEBUG is not set → dev_token must NOT be returned
        assert "dev_token" not in result
