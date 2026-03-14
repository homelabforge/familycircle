"""Tests for event_to_dict serialization function."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.events import event_to_dict
from app.models.event import Event, EventRSVP, EventType, RSVPStatus
from app.models.family import Family
from app.models.family_membership import FamilyMembership, FamilyRole
from app.models.holiday_detail import HolidayDetail
from app.models.rsvp_guest import RSVPGuest
from app.models.user import User


def _uuid() -> str:
    return str(uuid.uuid4())


@pytest.fixture
async def serialization_scenario(db: AsyncSession):
    """Create a family with users, events, RSVPs, and detail types for testing event_to_dict."""
    family = Family(id=_uuid(), name="Serialize Family", family_code="SER001")
    user = User(id=_uuid(), email="ser@test.com", is_super_admin=False, current_family_id=family.id)
    db.add_all([family, user])
    db.add(
        FamilyMembership(
            id=_uuid(),
            user_id=user.id,
            family_id=family.id,
            role=FamilyRole.MEMBER,
            display_name="Ser User",
        )
    )

    tomorrow = datetime.now(UTC) + timedelta(days=1)

    # General event with RSVPs
    general_event = Event(
        id=_uuid(),
        family_id=family.id,
        created_by_id=user.id,
        event_type=EventType.GENERAL.value,
        title="General Event",
        event_date=tomorrow,
        has_rsvp=True,
    )
    db.add(general_event)

    # Add RSVPs
    rsvp_yes = EventRSVP(
        id=_uuid(), event_id=general_event.id, user_id=user.id, status=RSVPStatus.YES
    )
    db.add(rsvp_yes)

    user2 = User(
        id=_uuid(), email="ser2@test.com", is_super_admin=False, current_family_id=family.id
    )
    db.add(user2)
    db.add(
        FamilyMembership(
            id=_uuid(),
            user_id=user2.id,
            family_id=family.id,
            role=FamilyRole.MEMBER,
            display_name="Ser User 2",
        )
    )
    rsvp_no = EventRSVP(
        id=_uuid(), event_id=general_event.id, user_id=user2.id, status=RSVPStatus.NO
    )
    db.add(rsvp_no)

    user3 = User(
        id=_uuid(), email="ser3@test.com", is_super_admin=False, current_family_id=family.id
    )
    db.add(user3)
    db.add(
        FamilyMembership(
            id=_uuid(),
            user_id=user3.id,
            family_id=family.id,
            role=FamilyRole.MEMBER,
            display_name="Ser User 3",
        )
    )
    rsvp_maybe = EventRSVP(
        id=_uuid(), event_id=general_event.id, user_id=user3.id, status=RSVPStatus.MAYBE
    )
    db.add(rsvp_maybe)

    # Add a guest to the YES RSVP
    guest = RSVPGuest(id=_uuid(), rsvp_id=rsvp_yes.id, guest_name="Plus One")
    db.add(guest)

    # Holiday event
    holiday_event = Event(
        id=_uuid(),
        family_id=family.id,
        created_by_id=user.id,
        event_type=EventType.HOLIDAY.value,
        title="Christmas Dinner",
        event_date=tomorrow,
    )
    holiday_detail = HolidayDetail(
        id=_uuid(),
        event_id=holiday_event.id,
        holiday_name="Christmas",
        year=2026,
    )
    db.add_all([holiday_event, holiday_detail])

    # Parent event with sub-events
    parent_event = Event(
        id=_uuid(),
        family_id=family.id,
        created_by_id=user.id,
        event_type=EventType.GENERAL.value,
        title="Parent Event",
        event_date=tomorrow,
    )
    sub_event_active = Event(
        id=_uuid(),
        family_id=family.id,
        created_by_id=user.id,
        event_type=EventType.GENERAL.value,
        title="Active Sub",
        event_date=tomorrow,
        parent_event_id=parent_event.id,
    )
    sub_event_cancelled = Event(
        id=_uuid(),
        family_id=family.id,
        created_by_id=user.id,
        event_type=EventType.GENERAL.value,
        title="Cancelled Sub",
        event_date=tomorrow,
        parent_event_id=parent_event.id,
        cancelled_at=datetime.now(UTC),
        cancellation_reason="Changed plans",
    )
    db.add_all([parent_event, sub_event_active, sub_event_cancelled])
    await db.commit()

    return {
        "family": family,
        "user": user,
        "general_event": general_event,
        "holiday_event": holiday_event,
        "parent_event": parent_event,
        "rsvp_yes": rsvp_yes,
    }


class TestEventToDict:
    async def test_general_event_has_expected_keys(self, db: AsyncSession, serialization_scenario):
        s = serialization_scenario
        from sqlalchemy import select

        result = await db.execute(
            select(Event)
            .where(Event.id == s["general_event"].id)
            .options(
                selectinload(Event.rsvps).selectinload(EventRSVP.guests),
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
                selectinload(Event.wedding_party_members),
                selectinload(Event.sub_events),
                selectinload(Event.recurrence),
            )
        )
        event = result.scalar_one()
        d = event_to_dict(event)

        assert d["id"] == s["general_event"].id
        assert d["title"] == "General Event"
        assert d["event_type"] == "general"
        assert "rsvp_counts" in d
        assert "headcount" in d
        assert "holiday_detail" in d
        assert "birthday_detail" in d
        assert "baby_shower_detail" in d
        assert "wedding_detail" in d
        assert "sub_events" in d
        assert "wedding_party" in d
        assert "can_manage" in d

    async def test_rsvp_counts_computed_correctly(self, db: AsyncSession, serialization_scenario):
        s = serialization_scenario
        from sqlalchemy import select

        result = await db.execute(
            select(Event)
            .where(Event.id == s["general_event"].id)
            .options(
                selectinload(Event.rsvps).selectinload(EventRSVP.guests),
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
                selectinload(Event.wedding_party_members),
                selectinload(Event.sub_events),
                selectinload(Event.recurrence),
            )
        )
        event = result.scalar_one()
        d = event_to_dict(event)

        assert d["rsvp_counts"]["yes"] == 1
        assert d["rsvp_counts"]["no"] == 1
        assert d["rsvp_counts"]["maybe"] == 1

    async def test_headcount_includes_guests(self, db: AsyncSession, serialization_scenario):
        s = serialization_scenario
        from sqlalchemy import select

        result = await db.execute(
            select(Event)
            .where(Event.id == s["general_event"].id)
            .options(
                selectinload(Event.rsvps).selectinload(EventRSVP.guests),
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
                selectinload(Event.wedding_party_members),
                selectinload(Event.sub_events),
                selectinload(Event.recurrence),
            )
        )
        event = result.scalar_one()
        d = event_to_dict(event)

        # 1 YES RSVP + 1 guest = headcount of 2
        assert d["headcount"] == 2

    async def test_holiday_event_includes_detail(self, db: AsyncSession, serialization_scenario):
        s = serialization_scenario
        from sqlalchemy import select

        result = await db.execute(
            select(Event)
            .where(Event.id == s["holiday_event"].id)
            .options(
                selectinload(Event.rsvps).selectinload(EventRSVP.guests),
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
                selectinload(Event.wedding_party_members),
                selectinload(Event.sub_events),
                selectinload(Event.recurrence),
            )
        )
        event = result.scalar_one()
        d = event_to_dict(event)

        assert d["holiday_detail"] is not None
        assert d["holiday_detail"]["holiday_name"] == "Christmas"
        assert d["holiday_detail"]["year"] == 2026
        # Other details should be None
        assert d["birthday_detail"] is None
        assert d["baby_shower_detail"] is None
        assert d["wedding_detail"] is None

    async def test_sub_events_listed_cancelled_excluded_from_count(
        self, db: AsyncSession, serialization_scenario
    ):
        s = serialization_scenario
        from sqlalchemy import select

        result = await db.execute(
            select(Event)
            .where(Event.id == s["parent_event"].id)
            .options(
                selectinload(Event.rsvps).selectinload(EventRSVP.guests),
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
                selectinload(Event.wedding_party_members),
                selectinload(Event.sub_events),
                selectinload(Event.recurrence),
            )
        )
        event = result.scalar_one()
        d = event_to_dict(event)

        # 2 total sub-events, but only 1 active
        assert d["sub_event_count"] == 1
        assert len(d["sub_events"]) == 2  # all listed, including cancelled

    async def test_general_event_type_details_all_none(
        self, db: AsyncSession, serialization_scenario
    ):
        s = serialization_scenario
        from sqlalchemy import select

        result = await db.execute(
            select(Event)
            .where(Event.id == s["general_event"].id)
            .options(
                selectinload(Event.rsvps).selectinload(EventRSVP.guests),
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
                selectinload(Event.wedding_party_members),
                selectinload(Event.sub_events),
                selectinload(Event.recurrence),
            )
        )
        event = result.scalar_one()
        d = event_to_dict(event)

        assert d["holiday_detail"] is None
        assert d["birthday_detail"] is None
        assert d["baby_shower_detail"] is None
        assert d["wedding_detail"] is None
