"""Regression test: hard-deleting an event purges its gift-exchange rows (F7 follow-up).

event_id on the gift-exchange tables is a bare string with no FK and runtime FK
enforcement is off, so the delete is done explicitly in the service.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventType
from app.models.gift_exchange import (
    GiftExchangeAssignment,
    GiftExchangeExclusion,
    GiftExchangeMessage,
)
from app.services import auth as auth_service
from app.services import gift_exchange as ge_service


def _uuid() -> str:
    return str(uuid.uuid4())


async def _count(db: AsyncSession, model, event_id: str) -> int:
    stmt = select(func.count()).select_from(model).where(model.event_id == event_id)
    return (await db.execute(stmt)).scalar() or 0


class TestEventDeleteGiftExchangeCleanup:
    async def test_purges_assignments_exclusions_messages(self, db: AsyncSession):
        family = await auth_service.create_family(db, "Fam")
        u1 = await auth_service.create_user(db, "u1@test.com", "pw123456")
        await auth_service.add_user_to_family(db, u1, family, "U1")
        u2 = await auth_service.create_user(db, "u2@test.com", "pw123456")
        await auth_service.add_user_to_family(db, u2, family, "U2")

        event = Event(
            id=_uuid(),
            family_id=family.id,
            created_by_id=u1.id,
            event_type=EventType.GENERAL.value,
            title="Gift Exchange",
            event_date=datetime.now(UTC) + timedelta(days=1),
            has_gift_exchange=True,
        )
        db.add(event)
        await db.flush()

        db.add(
            GiftExchangeAssignment(id=_uuid(), event_id=event.id, giver_id=u1.id, receiver_id=u2.id)
        )
        db.add(
            GiftExchangeExclusion(id=_uuid(), event_id=event.id, giver_id=u1.id, receiver_id=u2.id)
        )
        db.add(
            GiftExchangeMessage(
                id=_uuid(), event_id=event.id, sender_id=u1.id, recipient_id=u2.id, content="hi"
            )
        )
        await db.commit()

        await ge_service.delete_event_gift_exchange_data(db, event.id)
        await db.commit()

        assert await _count(db, GiftExchangeAssignment, event.id) == 0
        assert await _count(db, GiftExchangeExclusion, event.id) == 0
        assert await _count(db, GiftExchangeMessage, event.id) == 0

    async def test_leaves_other_events_data_intact(self, db: AsyncSession):
        family = await auth_service.create_family(db, "Fam")
        u1 = await auth_service.create_user(db, "u1@test.com", "pw123456")
        await auth_service.add_user_to_family(db, u1, family, "U1")
        u2 = await auth_service.create_user(db, "u2@test.com", "pw123456")
        await auth_service.add_user_to_family(db, u2, family, "U2")

        keep_event_id = _uuid()
        drop_event_id = _uuid()
        db.add(
            GiftExchangeAssignment(
                id=_uuid(), event_id=keep_event_id, giver_id=u1.id, receiver_id=u2.id
            )
        )
        db.add(
            GiftExchangeAssignment(
                id=_uuid(), event_id=drop_event_id, giver_id=u1.id, receiver_id=u2.id
            )
        )
        await db.commit()

        await ge_service.delete_event_gift_exchange_data(db, drop_event_id)
        await db.commit()

        assert await _count(db, GiftExchangeAssignment, drop_event_id) == 0
        assert await _count(db, GiftExchangeAssignment, keep_event_id) == 1

    async def test_delete_family_purges_gift_exchange(self, db: AsyncSession):
        """Family deletion also clears its events' gift-exchange rows (no FK cascade)."""
        family = await auth_service.create_family(db, "Fam")
        event = Event(
            id=_uuid(),
            family_id=family.id,
            created_by_id=_uuid(),
            event_type=EventType.GENERAL.value,
            title="Gift Exchange",
            event_date=datetime.now(UTC) + timedelta(days=1),
            has_gift_exchange=True,
        )
        db.add(event)
        await db.flush()
        db.add(
            GiftExchangeAssignment(
                id=_uuid(), event_id=event.id, giver_id=_uuid(), receiver_id=_uuid()
            )
        )
        await db.commit()

        # No single-membership users → delete_family proceeds (no orphan guard hit).
        _name, orphaned = await auth_service.delete_family(db, family.id)
        await db.commit()

        assert orphaned is None
        assert await _count(db, GiftExchangeAssignment, event.id) == 0
