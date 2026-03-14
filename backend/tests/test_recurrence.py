"""Tests for recurrence cloning — _copy_type_details."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.baby_shower_detail import BabyShowerDetail
from app.models.birthday_detail import BirthdayDetail
from app.models.event import Event, EventType
from app.models.family import Family
from app.models.family_membership import FamilyMembership, FamilyRole
from app.models.holiday_detail import HolidayDetail
from app.models.user import User
from app.models.wedding_detail import WeddingDetail
from app.services.recurrence import _copy_type_details


def _uuid() -> str:
    return str(uuid.uuid4())


@pytest.fixture
async def recurrence_base(db: AsyncSession):
    """Create family + user + target event for cloning into."""
    family = Family(id=_uuid(), name="Recurrence Family", family_code="REC001")
    user = User(id=_uuid(), email="rec@test.com", is_super_admin=False, current_family_id=family.id)
    db.add_all([family, user])
    db.add(
        FamilyMembership(
            id=_uuid(),
            user_id=user.id,
            family_id=family.id,
            role=FamilyRole.MEMBER,
            display_name="Rec",
        )
    )
    await db.commit()
    return {"family": family, "user": user}


class TestCopyTypeDetails:
    async def test_holiday_cloned_with_year_incremented(self, db: AsyncSession, recurrence_base):
        s = recurrence_base
        tomorrow = datetime.now(UTC) + timedelta(days=1)

        source = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.HOLIDAY.value,
            title="Christmas",
            event_date=tomorrow,
        )
        detail = HolidayDetail(
            id=_uuid(),
            event_id=source.id,
            holiday_name="Christmas",
            year=2025,
        )
        target = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.HOLIDAY.value,
            title="Christmas",
            event_date=tomorrow + timedelta(days=365),
        )
        db.add_all([source, detail, target])
        await db.flush()

        # Re-query with selectinload to avoid MissingGreenlet
        result = await db.execute(
            select(Event)
            .where(Event.id == source.id)
            .options(
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
            )
        )
        source = result.scalar_one()

        await _copy_type_details(db, source, target)
        await db.flush()

        result = await db.execute(select(HolidayDetail).where(HolidayDetail.event_id == target.id))
        cloned = result.scalar_one()
        assert cloned.holiday_name == "Christmas"
        assert cloned.year == 2026  # year + 1

    async def test_birthday_cloned_with_age_incremented(self, db: AsyncSession, recurrence_base):
        s = recurrence_base
        tomorrow = datetime.now(UTC) + timedelta(days=1)

        source = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.BIRTHDAY.value,
            title="Birthday",
            event_date=tomorrow,
        )
        detail = BirthdayDetail(
            id=_uuid(),
            event_id=source.id,
            birthday_person_name="Alice",
            age_turning=30,
            is_secret=False,
        )
        target = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.BIRTHDAY.value,
            title="Birthday",
            event_date=tomorrow + timedelta(days=365),
        )
        db.add_all([source, detail, target])
        await db.flush()
        result = await db.execute(
            select(Event)
            .where(Event.id == source.id)
            .options(
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
            )
        )
        source = result.scalar_one()

        await _copy_type_details(db, source, target)
        await db.flush()

        result = await db.execute(
            select(BirthdayDetail).where(BirthdayDetail.event_id == target.id)
        )
        cloned = result.scalar_one()
        assert cloned.birthday_person_name == "Alice"
        assert cloned.age_turning == 31  # age + 1

    async def test_baby_shower_cloned_exactly(self, db: AsyncSession, recurrence_base):
        s = recurrence_base
        tomorrow = datetime.now(UTC) + timedelta(days=1)

        source = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.BABY_SHOWER.value,
            title="Shower",
            event_date=tomorrow,
        )
        detail = BabyShowerDetail(
            id=_uuid(),
            event_id=source.id,
            parent1_name="Jane",
            parent2_name="John",
            baby_name="Baby",
            gender="unknown",
            is_gender_reveal=True,
        )
        target = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.BABY_SHOWER.value,
            title="Shower",
            event_date=tomorrow + timedelta(days=30),
        )
        db.add_all([source, detail, target])
        await db.flush()
        result = await db.execute(
            select(Event)
            .where(Event.id == source.id)
            .options(
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
            )
        )
        source = result.scalar_one()

        await _copy_type_details(db, source, target)
        await db.flush()

        result = await db.execute(
            select(BabyShowerDetail).where(BabyShowerDetail.event_id == target.id)
        )
        cloned = result.scalar_one()
        assert cloned.parent1_name == "Jane"
        assert cloned.parent2_name == "John"
        assert cloned.baby_name == "Baby"
        assert cloned.gender == "unknown"
        assert cloned.is_gender_reveal is True

    async def test_wedding_cloned_exactly(self, db: AsyncSession, recurrence_base):
        s = recurrence_base
        tomorrow = datetime.now(UTC) + timedelta(days=1)

        source = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.WEDDING.value,
            title="Wedding",
            event_date=tomorrow,
        )
        detail = WeddingDetail(
            id=_uuid(),
            event_id=source.id,
            partner1_name="Alice",
            partner2_name="Bob",
            venue_name="Chapel",
            color_theme="Ivory",
        )
        target = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.WEDDING.value,
            title="Wedding",
            event_date=tomorrow + timedelta(days=365),
        )
        db.add_all([source, detail, target])
        await db.flush()
        result = await db.execute(
            select(Event)
            .where(Event.id == source.id)
            .options(
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
            )
        )
        source = result.scalar_one()

        await _copy_type_details(db, source, target)
        await db.flush()

        result = await db.execute(select(WeddingDetail).where(WeddingDetail.event_id == target.id))
        cloned = result.scalar_one()
        assert cloned.partner1_name == "Alice"
        assert cloned.partner2_name == "Bob"
        assert cloned.venue_name == "Chapel"
        assert cloned.color_theme == "Ivory"

    async def test_general_event_no_detail_created(self, db: AsyncSession, recurrence_base):
        s = recurrence_base
        tomorrow = datetime.now(UTC) + timedelta(days=1)

        source = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.GENERAL.value,
            title="General",
            event_date=tomorrow,
        )
        target = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.GENERAL.value,
            title="General",
            event_date=tomorrow + timedelta(days=7),
        )
        db.add_all([source, target])
        await db.flush()

        result = await db.execute(
            select(Event)
            .where(Event.id == source.id)
            .options(
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
            )
        )
        source = result.scalar_one()

        await _copy_type_details(db, source, target)
        await db.flush()

        # No detail rows should exist for target
        for model in [HolidayDetail, BirthdayDetail, BabyShowerDetail, WeddingDetail]:
            result = await db.execute(select(model).where(model.event_id == target.id))
            assert result.scalar_one_or_none() is None

    async def test_holiday_null_year_stays_null(self, db: AsyncSession, recurrence_base):
        """When year is None, cloned year should also be None (not None + 1)."""
        s = recurrence_base
        tomorrow = datetime.now(UTC) + timedelta(days=1)

        source = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.HOLIDAY.value,
            title="Holiday",
            event_date=tomorrow,
        )
        detail = HolidayDetail(
            id=_uuid(),
            event_id=source.id,
            holiday_name="Custom",
            year=None,
        )
        target = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.HOLIDAY.value,
            title="Holiday",
            event_date=tomorrow + timedelta(days=365),
        )
        db.add_all([source, detail, target])
        await db.flush()
        result = await db.execute(
            select(Event)
            .where(Event.id == source.id)
            .options(
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
            )
        )
        source = result.scalar_one()

        await _copy_type_details(db, source, target)
        await db.flush()

        result = await db.execute(select(HolidayDetail).where(HolidayDetail.event_id == target.id))
        cloned = result.scalar_one()
        assert cloned.year is None

    async def test_birthday_null_age_stays_null(self, db: AsyncSession, recurrence_base):
        """When age_turning is None, cloned should also be None."""
        s = recurrence_base
        tomorrow = datetime.now(UTC) + timedelta(days=1)

        source = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.BIRTHDAY.value,
            title="Birthday",
            event_date=tomorrow,
        )
        detail = BirthdayDetail(
            id=_uuid(),
            event_id=source.id,
            birthday_person_name="Bob",
            age_turning=None,
            is_secret=False,
        )
        target = Event(
            id=_uuid(),
            family_id=s["family"].id,
            created_by_id=s["user"].id,
            event_type=EventType.BIRTHDAY.value,
            title="Birthday",
            event_date=tomorrow + timedelta(days=365),
        )
        db.add_all([source, detail, target])
        await db.flush()
        result = await db.execute(
            select(Event)
            .where(Event.id == source.id)
            .options(
                selectinload(Event.holiday_detail),
                selectinload(Event.birthday_detail),
                selectinload(Event.baby_shower_detail),
                selectinload(Event.wedding_detail),
            )
        )
        source = result.scalar_one()

        await _copy_type_details(db, source, target)
        await db.flush()

        result = await db.execute(
            select(BirthdayDetail).where(BirthdayDetail.event_id == target.id)
        )
        cloned = result.scalar_one()
        assert cloned.age_turning is None
