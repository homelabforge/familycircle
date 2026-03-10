"""Shared test fixtures for FamilyCircle backend tests."""

from __future__ import annotations

import os
import uuid

# Must be set before any app imports so config.py doesn't try to mkdir /data
os.environ.setdefault("DATABASE_PATH", "/tmp/test-familycircle.db")
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.birthday_detail import BirthdayDetail
from app.models.event import Event, EventType
from app.models.family import Family
from app.models.family_membership import FamilyMembership, FamilyRole
from app.models.user import User


def _uuid() -> str:
    return str(uuid.uuid4())


@pytest.fixture
async def db():
    """In-memory SQLite async session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def two_family_scenario(db: AsyncSession):
    """Create a scenario with two families and a user who belongs to both.

    Returns a dict with:
        user: User in both Family A and Family B, context set to Family B
        family_a / family_b: Family objects
        event_a: A general event in Family A
        event_b: A general event in Family B
    """
    family_a = Family(id=_uuid(), name="Family A", family_code="AAAAAA")
    family_b = Family(id=_uuid(), name="Family B", family_code="BBBBBB")

    user = User(
        id=_uuid(),
        email="multi@test.com",
        is_super_admin=False,
        current_family_id=family_b.id,  # Context set to Family B
    )

    mem_a = FamilyMembership(
        id=_uuid(),
        user_id=user.id,
        family_id=family_a.id,
        role=FamilyRole.MEMBER,
        display_name="User A",
    )
    mem_b = FamilyMembership(
        id=_uuid(),
        user_id=user.id,
        family_id=family_b.id,
        role=FamilyRole.MEMBER,
        display_name="User B",
    )

    tomorrow = datetime.now(UTC) + timedelta(days=1)
    event_a = Event(
        id=_uuid(),
        family_id=family_a.id,
        created_by_id=user.id,
        event_type=EventType.GENERAL.value,
        title="Family A Dinner",
        event_date=tomorrow,
    )
    event_b = Event(
        id=_uuid(),
        family_id=family_b.id,
        created_by_id=user.id,
        event_type=EventType.GENERAL.value,
        title="Family B Dinner",
        event_date=tomorrow,
    )

    db.add_all([family_a, family_b, user, mem_a, mem_b, event_a, event_b])
    await db.commit()

    return {
        "user": user,
        "family_a": family_a,
        "family_b": family_b,
        "event_a": event_a,
        "event_b": event_b,
    }


@pytest.fixture
async def secret_birthday_scenario(db: AsyncSession):
    """Create a scenario with a secret birthday event.

    Returns a dict with:
        birthday_person: The user whose birthday it is (should NOT see the event)
        organizer: The user who created the event (should see it)
        super_admin: A super admin user (should see it)
        family: The family
        secret_event: The secret birthday event
    """
    family = Family(id=_uuid(), name="Birthday Family", family_code="BDAY01")

    birthday_person = User(
        id=_uuid(),
        email="birthday@test.com",
        is_super_admin=False,
        current_family_id=family.id,
    )
    organizer = User(
        id=_uuid(),
        email="organizer@test.com",
        is_super_admin=False,
        current_family_id=family.id,
    )
    super_admin = User(
        id=_uuid(),
        email="admin@test.com",
        is_super_admin=True,
        current_family_id=family.id,
    )

    for u in [birthday_person, organizer, super_admin]:
        db.add(
            FamilyMembership(
                id=_uuid(),
                user_id=u.id,
                family_id=family.id,
                role=FamilyRole.ADMIN if u is organizer else FamilyRole.MEMBER,
                display_name=u.email.split("@")[0],
            )
        )

    tomorrow = datetime.now(UTC) + timedelta(days=7)
    secret_event = Event(
        id=_uuid(),
        family_id=family.id,
        created_by_id=organizer.id,
        event_type=EventType.BIRTHDAY.value,
        title="Surprise Party",
        event_date=tomorrow,
        has_potluck=True,
    )

    birthday_detail = BirthdayDetail(
        id=_uuid(),
        event_id=secret_event.id,
        birthday_person_id=birthday_person.id,
        birthday_person_name="Birthday Person",
        is_secret=True,
    )

    db.add_all([family, birthday_person, organizer, super_admin, secret_event, birthday_detail])
    await db.commit()

    # Refresh to load relationships
    await db.refresh(secret_event, ["birthday_detail"])

    return {
        "birthday_person": birthday_person,
        "organizer": organizer,
        "super_admin": super_admin,
        "family": family,
        "secret_event": secret_event,
    }
