"""Integration tests for consolidated routers — comment reactions and RSVP.

Tests verify the endpoints work correctly after being moved between files:
- toggle_reaction (merged from comment_reactions.py into event_comments.py)
- RSVP + guest endpoints (consolidated from events.py + rsvp_guests.py into rsvp.py)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment_reaction import CommentReaction
from app.models.event import Event, EventRSVP, EventType, RSVPStatus
from app.models.event_comment import EventComment
from app.models.family import Family
from app.models.family_membership import FamilyMembership, FamilyRole
from app.models.rsvp_guest import RSVPGuest
from app.models.user import User


def _uuid() -> str:
    return str(uuid.uuid4())


@pytest.fixture
async def router_scenario(db: AsyncSession):
    """Family + user + event + comment for testing consolidated routers."""
    family = Family(id=_uuid(), name="Router Family", family_code="RTR001")
    user = User(
        id=_uuid(),
        email="router@test.com",
        is_super_admin=False,
        current_family_id=family.id,
    )
    db.add_all([family, user])
    db.add(
        FamilyMembership(
            id=_uuid(),
            user_id=user.id,
            family_id=family.id,
            role=FamilyRole.MEMBER,
            display_name="Router User",
        )
    )

    tomorrow = datetime.now(UTC) + timedelta(days=1)
    event = Event(
        id=_uuid(),
        family_id=family.id,
        created_by_id=user.id,
        event_type=EventType.GENERAL.value,
        title="Router Test Event",
        event_date=tomorrow,
        has_rsvp=True,
    )
    db.add(event)

    comment = EventComment(
        id=_uuid(),
        event_id=event.id,
        user_id=user.id,
        content="Test comment",
    )
    db.add(comment)
    await db.commit()

    return {"family": family, "user": user, "event": event, "comment": comment}


class TestToggleReactionMerged:
    """Verify toggle_reaction works after merge into event_comments.py."""

    async def test_add_reaction(self, db: AsyncSession, router_scenario):
        s = router_scenario
        from app.api.event_comments import toggle_reaction
        from app.schemas.comment_reaction import CommentReactionToggle

        result = await toggle_reaction(
            event_id=s["event"].id,
            comment_id=s["comment"].id,
            data=CommentReactionToggle(emoji="👍"),
            user=s["user"],
            db=db,
        )

        assert result["action"] == "added"
        assert any(r["emoji"] == "👍" for r in result["reactions"])

    async def test_remove_reaction(self, db: AsyncSession, router_scenario):
        s = router_scenario

        # Pre-add a reaction
        db.add(
            CommentReaction(
                id=_uuid(),
                comment_id=s["comment"].id,
                user_id=s["user"].id,
                emoji="❤️",
            )
        )
        await db.flush()

        from app.api.event_comments import toggle_reaction
        from app.schemas.comment_reaction import CommentReactionToggle

        result = await toggle_reaction(
            event_id=s["event"].id,
            comment_id=s["comment"].id,
            data=CommentReactionToggle(emoji="❤️"),
            user=s["user"],
            db=db,
        )

        assert result["action"] == "removed"

    async def test_reaction_on_nonexistent_comment_returns_404(
        self, db: AsyncSession, router_scenario
    ):
        s = router_scenario
        from fastapi import HTTPException

        from app.api.event_comments import toggle_reaction
        from app.schemas.comment_reaction import CommentReactionToggle

        with pytest.raises(HTTPException) as exc_info:
            await toggle_reaction(
                event_id=s["event"].id,
                comment_id=_uuid(),  # nonexistent
                data=CommentReactionToggle(emoji="👍"),
                user=s["user"],
                db=db,
            )
        assert exc_info.value.status_code == 404


class TestRsvpConsolidated:
    """Verify RSVP endpoints work after consolidation into rsvp.py."""

    async def test_rsvp_to_event(self, db: AsyncSession, router_scenario):
        s = router_scenario
        from app.api.rsvp import RSVPRequest, rsvp_to_event

        background_tasks = AsyncMock()
        result = await rsvp_to_event(
            event_id=s["event"].id,
            request=RSVPRequest(status="yes"),
            background_tasks=background_tasks,
            user=s["user"],
            db=db,
        )

        assert "RSVP updated" in result["message"]

        # Verify DB row
        rsvp_result = await db.execute(
            select(EventRSVP).where(
                EventRSVP.event_id == s["event"].id,
                EventRSVP.user_id == s["user"].id,
            )
        )
        rsvp = rsvp_result.scalar_one()
        assert rsvp.status == RSVPStatus.YES

    async def test_rsvp_update_status(self, db: AsyncSession, router_scenario):
        s = router_scenario

        # Pre-RSVP as yes
        db.add(
            EventRSVP(
                id=_uuid(),
                event_id=s["event"].id,
                user_id=s["user"].id,
                status=RSVPStatus.YES,
            )
        )
        await db.commit()

        from app.api.rsvp import RSVPRequest, rsvp_to_event

        background_tasks = AsyncMock()
        result = await rsvp_to_event(
            event_id=s["event"].id,
            request=RSVPRequest(status="maybe"),
            background_tasks=background_tasks,
            user=s["user"],
            db=db,
        )

        assert "maybe" in result["message"]

    async def test_remove_rsvp(self, db: AsyncSession, router_scenario):
        s = router_scenario

        db.add(
            EventRSVP(
                id=_uuid(),
                event_id=s["event"].id,
                user_id=s["user"].id,
                status=RSVPStatus.YES,
            )
        )
        await db.commit()

        from app.api.rsvp import remove_rsvp

        result = await remove_rsvp(
            event_id=s["event"].id,
            user=s["user"],
            db=db,
        )

        assert result["message"] == "RSVP removed"

        # Verify gone
        rsvp_result = await db.execute(
            select(EventRSVP).where(
                EventRSVP.event_id == s["event"].id,
                EventRSVP.user_id == s["user"].id,
            )
        )
        assert rsvp_result.scalar_one_or_none() is None

    async def test_invalid_rsvp_status_returns_400(self, db: AsyncSession, router_scenario):
        s = router_scenario
        from fastapi import HTTPException

        from app.api.rsvp import RSVPRequest, rsvp_to_event

        background_tasks = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await rsvp_to_event(
                event_id=s["event"].id,
                request=RSVPRequest(status="invalid"),
                background_tasks=background_tasks,
                user=s["user"],
                db=db,
            )
        assert exc_info.value.status_code == 400


class TestRsvpGuestsConsolidated:
    """Verify RSVP guest endpoints work after consolidation into rsvp.py."""

    @pytest.fixture
    async def rsvp_with_guest(self, db: AsyncSession, router_scenario):
        s = router_scenario
        rsvp = EventRSVP(
            id=_uuid(),
            event_id=s["event"].id,
            user_id=s["user"].id,
            status=RSVPStatus.YES,
        )
        db.add(rsvp)
        await db.flush()

        guest = RSVPGuest(
            id=_uuid(),
            rsvp_id=rsvp.id,
            guest_name="Plus One",
            dietary_restrictions="Vegetarian",
        )
        db.add(guest)
        await db.commit()

        return {**s, "rsvp": rsvp, "guest": guest}

    async def test_list_guests(self, db: AsyncSession, rsvp_with_guest):
        s = rsvp_with_guest
        from app.api.rsvp import list_my_guests

        result = await list_my_guests(
            event_id=s["event"].id,
            user=s["user"],
            db=db,
        )

        assert len(result["guests"]) == 1
        assert result["guests"][0]["guest_name"] == "Plus One"

    async def test_add_guest(self, db: AsyncSession, rsvp_with_guest):
        s = rsvp_with_guest
        from app.api.rsvp import add_guest
        from app.schemas.rsvp_guest import RSVPGuestCreate

        result = await add_guest(
            event_id=s["event"].id,
            data=RSVPGuestCreate(guest_name="Plus Two"),
            user=s["user"],
            db=db,
        )

        assert result["guest_name"] == "Plus Two"

    async def test_add_guest_without_rsvp_returns_400(self, db: AsyncSession, router_scenario):
        s = router_scenario
        from fastapi import HTTPException

        from app.api.rsvp import add_guest
        from app.schemas.rsvp_guest import RSVPGuestCreate

        with pytest.raises(HTTPException) as exc_info:
            await add_guest(
                event_id=s["event"].id,
                data=RSVPGuestCreate(guest_name="No RSVP Guest"),
                user=s["user"],
                db=db,
            )
        assert exc_info.value.status_code == 400

    async def test_delete_guest(self, db: AsyncSession, rsvp_with_guest):
        s = rsvp_with_guest
        from app.api.rsvp import delete_guest

        await delete_guest(
            event_id=s["event"].id,
            guest_id=s["guest"].id,
            user=s["user"],
            db=db,
        )

        result = await db.execute(select(RSVPGuest).where(RSVPGuest.id == s["guest"].id))
        assert result.scalar_one_or_none() is None
