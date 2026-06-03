"""Regression test: gift-exchange participants endpoint does not leak emails (F11)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.gift_exchange import get_participants
from app.models.event import Event, EventType
from app.models.family_membership import FamilyRole
from app.services import auth as auth_service


def _uuid() -> str:
    return str(uuid.uuid4())


class TestParticipantsOmitEmail:
    async def test_participants_have_no_email_field(self, db: AsyncSession):
        family = await auth_service.create_family(db, "Fam")
        admin = await auth_service.create_user(db, "admin@test.com", "pw123456")
        await auth_service.add_user_to_family(db, admin, family, "Admin", FamilyRole.ADMIN)
        admin.current_family_id = family.id
        member = await auth_service.create_user(db, "member@test.com", "pw123456")
        await auth_service.add_user_to_family(db, member, family, "Member")

        event = Event(
            id=_uuid(),
            family_id=family.id,
            created_by_id=admin.id,
            event_type=EventType.GENERAL.value,
            title="Gift Exchange",
            event_date=datetime.now(UTC) + timedelta(days=1),
            has_gift_exchange=True,
        )
        db.add(event)
        await db.commit()

        result = await get_participants(event_id=event.id, user=admin, db=db)

        assert result["participants"]
        for participant in result["participants"]:
            assert "email" not in participant
            assert set(participant.keys()) == {"id", "display_name"}
