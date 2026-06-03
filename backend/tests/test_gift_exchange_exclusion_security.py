"""Security regression tests for gift-exchange exclusion deletion scoping (F6).

A manager authorized for event A must not be able to delete an exclusion that
belongs to event B by supplying B's exclusion id against A's path (IDOR).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.gift_exchange import remove_exclusion
from app.models.event import Event, EventType
from app.models.family_membership import FamilyRole
from app.models.gift_exchange import GiftExchangeExclusion
from app.services import auth as auth_service


def _uuid() -> str:
    return str(uuid.uuid4())


@pytest.fixture
async def exclusion_scenario(db: AsyncSession):
    """A member-created event A and an admin-created event B in one family.

    The member can manage A (as its creator) but NOT B. An exclusion belongs to B.
    """
    family = await auth_service.create_family(db, "Fam")
    creator = await auth_service.create_user(db, "creator@test.com", "pw123456")
    await auth_service.add_user_to_family(db, creator, family, "Creator", FamilyRole.MEMBER)
    creator.current_family_id = family.id
    other = await auth_service.create_user(db, "other@test.com", "pw123456")
    await auth_service.add_user_to_family(db, other, family, "Other", FamilyRole.ADMIN)

    tomorrow = datetime.now(UTC) + timedelta(days=1)
    event_a = Event(
        id=_uuid(),
        family_id=family.id,
        created_by_id=creator.id,
        event_type=EventType.GENERAL.value,
        title="Event A",
        event_date=tomorrow,
        has_gift_exchange=True,
    )
    event_b = Event(
        id=_uuid(),
        family_id=family.id,
        created_by_id=other.id,
        event_type=EventType.GENERAL.value,
        title="Event B",
        event_date=tomorrow,
        has_gift_exchange=True,
    )
    db.add_all([event_a, event_b])
    await db.flush()

    excl_b = GiftExchangeExclusion(
        id=_uuid(), event_id=event_b.id, giver_id=creator.id, receiver_id=other.id
    )
    db.add(excl_b)
    await db.commit()

    return {
        "creator": creator,
        "other": other,
        "event_a": event_a,
        "event_b": event_b,
        "excl_b": excl_b,
    }


class TestExclusionDeleteScoping:
    async def test_cannot_delete_other_events_exclusion(
        self, db: AsyncSession, exclusion_scenario: dict
    ):
        """Deleting event B's exclusion via event A's path 404s and leaves it intact."""
        s = exclusion_scenario
        with pytest.raises(HTTPException) as exc:
            await remove_exclusion(
                event_id=s["event_a"].id,
                exclusion_id=s["excl_b"].id,
                user=s["creator"],
                db=db,
            )
        assert exc.value.status_code == 404

        surviving = await db.execute(
            select(GiftExchangeExclusion).where(GiftExchangeExclusion.id == s["excl_b"].id)
        )
        assert surviving.scalar_one_or_none() is not None

    async def test_can_delete_own_events_exclusion(
        self, db: AsyncSession, exclusion_scenario: dict
    ):
        """The legitimate path (exclusion on the authorized event) still works."""
        s = exclusion_scenario
        excl_a = GiftExchangeExclusion(
            id=_uuid(),
            event_id=s["event_a"].id,
            giver_id=s["creator"].id,
            receiver_id=s["other"].id,
        )
        db.add(excl_a)
        await db.commit()

        result = await remove_exclusion(
            event_id=s["event_a"].id,
            exclusion_id=excl_a.id,
            user=s["creator"],
            db=db,
        )
        assert "removed" in result["message"].lower()

        gone = await db.execute(
            select(GiftExchangeExclusion).where(GiftExchangeExclusion.id == excl_a.id)
        )
        assert gone.scalar_one_or_none() is None
