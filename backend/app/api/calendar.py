"""Calendar API endpoints — iCal export and family feed."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import require_family_context
from app.api.event_helpers import resolve_event_or_404
from app.db import get_db_session
from app.models import Event, Family, User
from app.services.icalendar_service import generate_family_feed, generate_single_event_ics
from app.services.permissions import permissions

logger = logging.getLogger(__name__)

router = APIRouter()

ICS_CONTENT_TYPE = "text/calendar; charset=utf-8"


@router.get("/events/{event_id}/calendar.ics")
async def download_event_ics(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    """Download a single event as an .ics file."""
    event = await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    ics_data = generate_single_event_ics(event)
    filename = f"{event.title.replace(' ', '_')}.ics"

    return Response(
        content=ics_data,
        media_type=ICS_CONTENT_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/calendar/{feed_token}/feed.ics")
async def family_calendar_feed(
    feed_token: str,
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    """Public calendar feed URL. No auth — secured by unique feed token."""
    result = await db.execute(select(Family).where(Family.calendar_feed_token == feed_token))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="Calendar feed not found")

    # Get all non-cancelled events for this family
    result = await db.execute(
        select(Event)
        .where(Event.family_id == family.id)
        .options(selectinload(Event.birthday_detail))
        .order_by(Event.event_date.asc())
    )
    events = list(result.scalars().all())

    ics_data = generate_family_feed(events, family.name)

    return Response(
        content=ics_data,
        media_type=ICS_CONTENT_TYPE,
        headers={
            "Content-Disposition": f'inline; filename="{family.name}_calendar.ics"',
            "Cache-Control": "public, max-age=900",  # 15 min cache
        },
    )


@router.get("/calendar/feed-url")
async def get_feed_url(
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get the calendar feed URL for the current family."""
    result = await db.execute(select(Family).where(Family.id == user.current_family_id))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Generate token if not set
    if not family.calendar_feed_token:
        family.calendar_feed_token = uuid.uuid4().hex + uuid.uuid4().hex[:32]
        await db.commit()

    return {
        "feed_token": family.calendar_feed_token,
        "feed_url": f"/api/calendar/{family.calendar_feed_token}/feed.ics",
    }


@router.post("/calendar/regenerate-token")
async def regenerate_feed_token(
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Regenerate the calendar feed token. Admin only. Old URL stops working."""
    is_admin = await permissions.is_family_admin(db, user, user.current_family_id or "")
    if not is_admin:
        raise HTTPException(
            status_code=403, detail="Only family admins can regenerate the feed token"
        )

    result = await db.execute(select(Family).where(Family.id == user.current_family_id))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    family.calendar_feed_token = uuid.uuid4().hex + uuid.uuid4().hex[:32]
    await db.commit()

    return {
        "message": "Feed token regenerated. Old calendar URLs will stop working.",
        "feed_token": family.calendar_feed_token,
        "feed_url": f"/api/calendar/{family.calendar_feed_token}/feed.ics",
    }
