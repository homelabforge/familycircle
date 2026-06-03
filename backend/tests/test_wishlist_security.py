"""Security regression tests for wishlist visibility scoping (F7).

A gift-exchange assignment only unlocks the target's wishlist when it belongs to
a LIVE, same-family, non-cancelled gift-exchange event. Stale/deleted, cancelled,
cross-family, and non-gift-exchange assignments must NOT grant access.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.wishlist import get_user_wishlist
from app.models.event import Event, EventType
from app.models.family_membership import FamilyRole
from app.models.gift_exchange import GiftExchangeAssignment
from app.models.wishlist import WishlistItem
from app.services import auth as auth_service


def _uuid() -> str:
    return str(uuid.uuid4())


def _make_event(
    family_id: str, created_by: str, *, has_gift_exchange: bool = True, cancelled: bool = False
) -> Event:
    return Event(
        id=_uuid(),
        family_id=family_id,
        created_by_id=created_by,
        event_type=EventType.GENERAL.value,
        title="Gift Exchange",
        event_date=datetime.now(UTC) + timedelta(days=1),
        has_gift_exchange=has_gift_exchange,
        cancelled_at=datetime.now(UTC) if cancelled else None,
    )


@pytest.fixture
async def wishlist_scenario(db: AsyncSession):
    """A giver (viewer) and a target in the same family; target has a wishlist item."""
    family = await auth_service.create_family(db, "Fam")
    other_family = await auth_service.create_family(db, "Other")
    giver = await auth_service.create_user(db, "giver@test.com", "pw123456")
    await auth_service.add_user_to_family(db, giver, family, "Giver", FamilyRole.MEMBER)
    giver.current_family_id = family.id
    target = await auth_service.create_user(db, "target@test.com", "pw123456")
    await auth_service.add_user_to_family(db, target, family, "Target", FamilyRole.MEMBER)

    db.add(WishlistItem(id=_uuid(), user_id=target.id, name="Secret gift", priority=1))
    await db.commit()

    return {"family": family, "other_family": other_family, "giver": giver, "target": target}


async def _add_assignment(db: AsyncSession, event_id: str, giver_id: str, receiver_id: str) -> None:
    db.add(
        GiftExchangeAssignment(
            id=_uuid(), event_id=event_id, giver_id=giver_id, receiver_id=receiver_id
        )
    )
    await db.commit()


class TestWishlistAssignmentScoping:
    async def test_active_assignment_unlocks(self, db: AsyncSession, wishlist_scenario: dict):
        """A live same-family gift-exchange assignment unlocks the wishlist."""
        s = wishlist_scenario
        event = _make_event(s["family"].id, s["giver"].id)
        db.add(event)
        await db.flush()
        await _add_assignment(db, event.id, s["giver"].id, s["target"].id)

        result = await get_user_wishlist(user_id=s["target"].id, user=s["giver"], db=db)
        assert any(item["name"] == "Secret gift" for item in result["items"])

    async def test_deleted_event_does_not_unlock(self, db: AsyncSession, wishlist_scenario: dict):
        """An assignment whose event no longer exists must not unlock."""
        s = wishlist_scenario
        await _add_assignment(db, _uuid(), s["giver"].id, s["target"].id)  # event_id → nowhere

        with pytest.raises(HTTPException) as exc:
            await get_user_wishlist(user_id=s["target"].id, user=s["giver"], db=db)
        assert exc.value.status_code == 403

    async def test_cancelled_event_does_not_unlock(self, db: AsyncSession, wishlist_scenario: dict):
        """A cancelled event's assignment must not unlock."""
        s = wishlist_scenario
        event = _make_event(s["family"].id, s["giver"].id, cancelled=True)
        db.add(event)
        await db.flush()
        await _add_assignment(db, event.id, s["giver"].id, s["target"].id)

        with pytest.raises(HTTPException) as exc:
            await get_user_wishlist(user_id=s["target"].id, user=s["giver"], db=db)
        assert exc.value.status_code == 403

    async def test_non_gift_exchange_event_does_not_unlock(
        self, db: AsyncSession, wishlist_scenario: dict
    ):
        """An assignment on a non-gift-exchange event must not unlock."""
        s = wishlist_scenario
        event = _make_event(s["family"].id, s["giver"].id, has_gift_exchange=False)
        db.add(event)
        await db.flush()
        await _add_assignment(db, event.id, s["giver"].id, s["target"].id)

        with pytest.raises(HTTPException) as exc:
            await get_user_wishlist(user_id=s["target"].id, user=s["giver"], db=db)
        assert exc.value.status_code == 403

    async def test_cross_family_event_does_not_unlock(
        self, db: AsyncSession, wishlist_scenario: dict
    ):
        """An assignment whose event is in another family must not unlock."""
        s = wishlist_scenario
        event = _make_event(s["other_family"].id, s["giver"].id)
        db.add(event)
        await db.flush()
        await _add_assignment(db, event.id, s["giver"].id, s["target"].id)

        with pytest.raises(HTTPException) as exc:
            await get_user_wishlist(user_id=s["target"].id, user=s["giver"], db=db)
        assert exc.value.status_code == 403
