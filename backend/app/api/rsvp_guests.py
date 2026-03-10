"""RSVP guests API — manage additional guests for RSVP responses."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_family_context
from app.api.event_helpers import resolve_event_or_404
from app.db import get_db_session
from app.models import EventRSVP, User
from app.models.rsvp_guest import RSVPGuest
from app.schemas.rsvp_guest import RSVPGuestCreate, RSVPGuestUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


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
    await resolve_event_or_404(db, event_id, user)

    result = await db.execute(
        select(EventRSVP).where(
            EventRSVP.event_id == event_id,
            EventRSVP.user_id == user.id,
        )
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
    await resolve_event_or_404(db, event_id, user)

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
    await resolve_event_or_404(db, event_id, user)

    # Find the guest, ensuring it belongs to this user's RSVP
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
    await resolve_event_or_404(db, event_id, user)

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
