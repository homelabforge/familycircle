"""RSVP API — event attendance and guest management.

Consolidated from events.py RSVP endpoints + rsvp_guests.py.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import require_family_context
from app.api.event_helpers import resolve_event_or_404
from app.db import get_db_session
from app.models import Event, EventRSVP, Family, FamilyMembership, User
from app.models.event import RSVPStatus
from app.models.rsvp_guest import RSVPGuest
from app.schemas.rsvp_guest import RSVPGuestCreate, RSVPGuestUpdate
from app.services.notifications.fire import send_notification_background

logger = logging.getLogger(__name__)

router = APIRouter()


class RSVPRequest(BaseModel):
    """RSVP request."""

    status: str  # yes, no, maybe


async def _get_member_display_name(db: AsyncSession, user_id: str, family_id: str) -> str:
    """Get user's display name in a family."""
    result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == family_id,
        )
    )
    membership = result.scalar_one_or_none()
    return membership.display_name if membership else "Unknown"


async def _check_event_conflicts(db: AsyncSession, user_id: str, target_event: Event) -> list[dict]:
    """Check for events on the same day that user has RSVPed yes to."""
    event_date = target_event.event_date.date()

    result = await db.execute(
        select(Event, EventRSVP)
        .join(EventRSVP, EventRSVP.event_id == Event.id)
        .where(
            EventRSVP.user_id == user_id,
            EventRSVP.status == RSVPStatus.YES,
            Event.id != target_event.id,
            Event.cancelled_at.is_(None),
        )
    )

    conflicts = []
    for event, _rsvp in result.all():
        if event.event_date.date() == event_date:
            family_result = await db.execute(select(Family).where(Family.id == event.family_id))
            family = family_result.scalar_one_or_none()

            conflicts.append(
                {
                    "title": event.title,
                    "family_name": family.name if family else "Unknown",
                    "date": event.event_date.isoformat(),
                }
            )

    return conflicts


# --- RSVP Endpoints (from events.py) ---


@router.post("/{event_id}/rsvp")
async def rsvp_to_event(
    event_id: str,
    request: RSVPRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """RSVP to an event (yes/no/maybe)."""
    try:
        status = RSVPStatus(request.status.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid RSVP status. Use yes, no, or maybe.")

    event = await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    if event.is_cancelled:
        raise HTTPException(status_code=400, detail="Cannot RSVP to a cancelled event")

    # Check for event conflicts (same day, across all families)
    conflict_warning = None
    if status == RSVPStatus.YES:
        conflicts = await _check_event_conflicts(db, user.id, event)
        if conflicts:
            conflict_warning = [
                {
                    "event_title": c["title"],
                    "family_name": c["family_name"],
                    "event_date": c["date"],
                }
                for c in conflicts
            ]

    # Check for existing RSVP
    rsvp_result = await db.execute(
        select(EventRSVP).where(
            EventRSVP.event_id == event_id,
            EventRSVP.user_id == user.id,
        )
    )
    existing_rsvp = rsvp_result.scalar_one_or_none()

    if existing_rsvp:
        existing_rsvp.status = status
    else:
        rsvp = EventRSVP(
            event_id=event_id,
            user_id=str(user.id),
            status=status,
        )
        db.add(rsvp)

    await db.commit()

    # Fire notification in background
    member_name = await _get_member_display_name(db, user.id, user.active_family_id or "")
    background_tasks.add_task(
        send_notification_background,
        "notify_rsvp_received",
        event_title=event.title,
        member_name=member_name,
        status=status.value,
    )

    response: dict = {"message": f"RSVP updated to {status.value}"}
    if status == RSVPStatus.YES and conflict_warning:
        response["conflicts"] = conflict_warning

    return response


@router.delete("/{event_id}/rsvp")
async def remove_rsvp(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Remove RSVP from an event."""
    await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(EventRSVP).where(
            EventRSVP.event_id == event_id,
            EventRSVP.user_id == user.id,
        )
    )
    rsvp = result.scalar_one_or_none()

    if rsvp:
        await db.delete(rsvp)
        await db.commit()

    return {"message": "RSVP removed"}


# --- RSVP Guest Endpoints (from rsvp_guests.py) ---


def _guest_to_dict(guest: RSVPGuest) -> dict:
    """Convert an RSVP guest to a response dict."""
    return {
        "id": str(guest.id),
        "rsvp_id": str(guest.rsvp_id),
        "guest_name": guest.guest_name,
        "dietary_restrictions": guest.dietary_restrictions,
        "allergies": guest.allergies,
        "created_at": guest.created_at.isoformat() if guest.created_at else None,
    }


@router.get("/{event_id}/rsvp/guests")
async def list_my_guests(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List the current user's additional guests for an event."""
    await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(EventRSVP)
        .where(
            EventRSVP.event_id == event_id,
            EventRSVP.user_id == user.id,
        )
        .options(selectinload(EventRSVP.guests))
    )
    rsvp = result.scalar_one_or_none()
    if not rsvp:
        return {"guests": []}

    return {"guests": [_guest_to_dict(g) for g in rsvp.guests]}


@router.post("/{event_id}/rsvp/guests", status_code=201)
async def add_guest(
    event_id: str,
    data: RSVPGuestCreate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Add an additional guest to the user's RSVP."""
    await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(EventRSVP).where(
            EventRSVP.event_id == event_id,
            EventRSVP.user_id == user.id,
        )
    )
    rsvp = result.scalar_one_or_none()
    if not rsvp:
        raise HTTPException(
            status_code=400,
            detail="You must RSVP before adding guests",
        )

    guest = RSVPGuest(
        rsvp_id=rsvp.id,
        guest_name=data.guest_name,
        dietary_restrictions=data.dietary_restrictions,
        allergies=data.allergies,
    )
    db.add(guest)
    await db.flush()

    return _guest_to_dict(guest)


@router.put("/{event_id}/rsvp/guests/{guest_id}")
async def update_guest(
    event_id: str,
    guest_id: str,
    data: RSVPGuestUpdate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Update an additional guest's info."""
    await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(RSVPGuest)
        .join(EventRSVP)
        .where(
            RSVPGuest.id == guest_id,
            EventRSVP.event_id == event_id,
            EventRSVP.user_id == user.id,
        )
    )
    guest = result.scalar_one_or_none()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(guest, key, value)
    await db.flush()

    return _guest_to_dict(guest)


@router.delete("/{event_id}/rsvp/guests/{guest_id}", status_code=204)
async def delete_guest(
    event_id: str,
    guest_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Remove an additional guest from the user's RSVP."""
    await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(RSVPGuest)
        .join(EventRSVP)
        .where(
            RSVPGuest.id == guest_id,
            EventRSVP.event_id == event_id,
            EventRSVP.user_id == user.id,
        )
    )
    guest = result.scalar_one_or_none()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    await db.delete(guest)
