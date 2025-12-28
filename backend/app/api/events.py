"""Events API endpoints - multi-family aware."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db_session
from app.models import Event, EventRSVP, User, FamilyMembership
from app.models.event import RSVPStatus
from app.api.auth import get_current_user, require_family_context, require_family_admin
from app.services.permissions import permissions
from app.services.email import send_event_cancelled_email, get_smtp_config

logger = logging.getLogger(__name__)

router = APIRouter()


class EventCreate(BaseModel):
    """Create event request."""

    title: str
    description: Optional[str] = None
    event_date: datetime
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    has_secret_santa: bool = False
    has_potluck: bool = False
    # Secret Santa rules
    secret_santa_budget_min: Optional[int] = None
    secret_santa_budget_max: Optional[int] = None
    secret_santa_notes: Optional[str] = None


class EventUpdate(BaseModel):
    """Update event request."""

    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    has_secret_santa: Optional[bool] = None
    has_potluck: Optional[bool] = None
    # Secret Santa rules
    secret_santa_budget_min: Optional[int] = None
    secret_santa_budget_max: Optional[int] = None
    secret_santa_notes: Optional[str] = None


class EventCancel(BaseModel):
    """Cancel event request."""

    reason: Optional[str] = None


class RSVPRequest(BaseModel):
    """RSVP request."""

    status: str  # yes, no, maybe


async def get_member_display_name(
    db: AsyncSession, user_id: str, family_id: str
) -> str:
    """Get user's display name in a family."""
    result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == family_id,
        )
    )
    membership = result.scalar_one_or_none()
    return membership.display_name if membership else "Unknown"


def event_to_dict(
    event: Event,
    user_rsvp: Optional[EventRSVP] = None,
    can_manage: bool = False,
) -> dict:
    """Convert event to response dict."""
    return {
        "id": str(event.id),
        "family_id": str(event.family_id),
        "created_by_id": str(event.created_by_id) if event.created_by_id else None,
        "title": event.title,
        "description": event.description,
        "event_date": event.event_date.isoformat() if event.event_date else None,
        "location_name": event.location_name,
        "location_address": event.location_address,
        "has_secret_santa": event.has_secret_santa,
        "has_potluck": event.has_potluck,
        "secret_santa_assigned": event.secret_santa_assigned,
        # Secret Santa rules
        "secret_santa_budget_min": event.secret_santa_budget_min,
        "secret_santa_budget_max": event.secret_santa_budget_max,
        "secret_santa_notes": event.secret_santa_notes,
        # Cancellation
        "is_cancelled": event.is_cancelled,
        "cancelled_at": event.cancelled_at.isoformat() if event.cancelled_at else None,
        "cancellation_reason": event.cancellation_reason,
        # RSVP counts
        "rsvp_counts": {
            "yes": len([r for r in event.rsvps if r.status == RSVPStatus.YES]),
            "no": len([r for r in event.rsvps if r.status == RSVPStatus.NO]),
            "maybe": len([r for r in event.rsvps if r.status == RSVPStatus.MAYBE]),
        },
        "user_rsvp": user_rsvp.status.value if user_rsvp else None,
        "can_manage": can_manage,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


@router.get("")
async def list_events(
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List all events for current family."""
    from app.api.settings import get_global_setting

    # Get cancelled event retention setting (default 7 days)
    retention_days_str = await get_global_setting(db, "cancelled_event_retention_days") or "7"
    try:
        retention_days = int(retention_days_str)
    except ValueError:
        retention_days = 7

    # Calculate cutoff date for cancelled events
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    result = await db.execute(
        select(Event)
        .where(
            Event.family_id == user.current_family_id,
            # Filter out cancelled events older than retention period
            or_(
                Event.cancelled_at.is_(None),  # Not cancelled
                Event.cancelled_at >= cutoff_date,  # Cancelled but within retention
            )
        )
        .order_by(Event.event_date.desc())
    )
    events = result.scalars().all()

    # Get user's RSVPs
    rsvp_result = await db.execute(
        select(EventRSVP).where(EventRSVP.user_id == user.id)
    )
    user_rsvps = {str(r.event_id): r for r in rsvp_result.scalars().all()}

    # Check management permissions for each event
    events_data = []
    for e in events:
        can_manage = await permissions.can_manage_event(db, user, e)
        events_data.append(event_to_dict(e, user_rsvps.get(str(e.id)), can_manage))

    return {"events": events_data}


@router.get("/upcoming")
async def list_upcoming_events(
    limit: int = 5,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List upcoming events for current family."""
    result = await db.execute(
        select(Event)
        .where(
            Event.family_id == user.current_family_id,
            Event.event_date >= datetime.now(),  # Use naive datetime to match DB storage
            Event.cancelled_at.is_(None),  # Exclude cancelled events
        )
        .order_by(Event.event_date.asc())
        .limit(limit)
    )
    events = result.scalars().all()

    # Get user's RSVPs
    rsvp_result = await db.execute(
        select(EventRSVP).where(EventRSVP.user_id == user.id)
    )
    user_rsvps = {str(r.event_id): r for r in rsvp_result.scalars().all()}

    events_data = []
    for e in events:
        can_manage = await permissions.can_manage_event(db, user, e)
        events_data.append(event_to_dict(e, user_rsvps.get(str(e.id)), can_manage))

    return {"events": events_data}


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a specific event."""
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.rsvps))
        .where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found. It may have been deleted.")

    # Verify user can view this event
    if not await permissions.can_view_event(db, user, event):
        raise HTTPException(status_code=403, detail="You don't have access to this event")

    # Get user's RSVP
    rsvp_result = await db.execute(
        select(EventRSVP).where(
            EventRSVP.event_id == event_id,
            EventRSVP.user_id == user.id,
        )
    )
    user_rsvp = rsvp_result.scalar_one_or_none()

    # Get all RSVPs with member names
    rsvps = []
    for rsvp in event.rsvps:
        display_name = await get_member_display_name(db, rsvp.user_id, event.family_id)
        rsvps.append({
            "user_id": str(rsvp.user_id),
            "display_name": display_name,
            "status": rsvp.status.value,
        })

    can_manage = await permissions.can_manage_event(db, user, event)
    response = event_to_dict(event, user_rsvp, can_manage)
    response["rsvps"] = rsvps

    return response


@router.post("")
async def create_event(
    request: EventCreate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new event in current family."""
    # Any member can create an event (they become the event creator)
    event = Event(
        family_id=user.current_family_id,
        created_by_id=user.id,
        title=request.title,
        description=request.description,
        event_date=request.event_date,
        location_name=request.location_name,
        location_address=request.location_address,
        has_secret_santa=request.has_secret_santa,
        has_potluck=request.has_potluck,
        secret_santa_budget_min=request.secret_santa_budget_min,
        secret_santa_budget_max=request.secret_santa_budget_max,
        secret_santa_notes=request.secret_santa_notes,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return {"message": "Event created", "id": str(event.id)}


@router.put("/{event_id}")
async def update_event(
    event_id: str,
    request: EventUpdate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Update an event (creator or admin only)."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found. It may have been deleted.")

    if not await permissions.can_manage_event(db, user, event):
        raise HTTPException(status_code=403, detail="You don't have permission to edit this event")

    if event.is_cancelled:
        raise HTTPException(status_code=400, detail="Cannot edit a cancelled event")

    if request.title is not None:
        event.title = request.title
    if request.description is not None:
        event.description = request.description
    if request.event_date is not None:
        event.event_date = request.event_date
    if request.location_name is not None:
        event.location_name = request.location_name
    if request.location_address is not None:
        event.location_address = request.location_address
    if request.has_secret_santa is not None:
        event.has_secret_santa = request.has_secret_santa
    if request.has_potluck is not None:
        event.has_potluck = request.has_potluck
    if request.secret_santa_budget_min is not None:
        event.secret_santa_budget_min = request.secret_santa_budget_min
    if request.secret_santa_budget_max is not None:
        event.secret_santa_budget_max = request.secret_santa_budget_max
    if request.secret_santa_notes is not None:
        event.secret_santa_notes = request.secret_santa_notes

    await db.commit()

    return {"message": "Event updated"}


@router.post("/{event_id}/cancel")
async def cancel_event(
    event_id: str,
    request: EventCancel,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Cancel an event (creator or admin only)."""
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.rsvps))
        .where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found. It may have been deleted.")

    if not await permissions.can_manage_event(db, user, event):
        raise HTTPException(status_code=403, detail="You don't have permission to cancel this event")

    if event.is_cancelled:
        raise HTTPException(status_code=400, detail="Event is already cancelled")

    event.cancelled_at = datetime.now(timezone.utc)
    event.cancellation_reason = request.reason

    await db.commit()

    # Send notifications to RSVPed users (yes or maybe)
    smtp_config = await get_smtp_config(db)
    if smtp_config.is_configured:
        # Get attendees who RSVPed yes or maybe
        attendee_user_ids = [
            r.user_id for r in event.rsvps
            if r.status in (RSVPStatus.YES, RSVPStatus.MAYBE)
        ]

        if attendee_user_ids:
            # Get canceller's display name
            canceller_name = await get_member_display_name(db, user.id, event.family_id)

            # Format event date
            event_date = event.event_date.strftime("%A, %B %d, %Y") if event.event_date else "TBD"

            # Get user details and send emails
            for attendee_id in attendee_user_ids:
                try:
                    # Get user email
                    user_result = await db.execute(
                        select(User).where(User.id == attendee_id)
                    )
                    attendee = user_result.scalar_one_or_none()
                    if not attendee:
                        continue

                    # Get display name
                    attendee_name = await get_member_display_name(
                        db, attendee_id, event.family_id
                    )

                    await send_event_cancelled_email(
                        db=db,
                        to_email=attendee.email,
                        recipient_name=attendee_name,
                        event_title=event.title,
                        event_date=event_date,
                        cancellation_reason=request.reason,
                        cancelled_by=canceller_name,
                    )
                except Exception as e:
                    logger.error(f"Failed to send cancellation email to {attendee_id}: {e}")

    return {"message": "Event cancelled"}


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete an event (creator or admin only)."""
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.rsvps))
        .where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found. It may have been deleted.")

    if not await permissions.can_manage_event(db, user, event):
        raise HTTPException(status_code=403, detail="You don't have permission to delete this event")

    # Only allow deletion if cancelled or no RSVPs
    has_rsvps = any(r.status == RSVPStatus.YES for r in event.rsvps)
    if has_rsvps and not event.is_cancelled:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete an event with RSVPs. Cancel it first.",
        )

    await db.delete(event)
    await db.commit()

    return {"message": "Event deleted"}


@router.post("/{event_id}/rsvp")
async def rsvp_to_event(
    event_id: str,
    request: RSVPRequest,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """RSVP to an event (yes/no/maybe)."""
    # Validate status
    try:
        status = RSVPStatus(request.status.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid RSVP status. Use yes, no, or maybe.")

    # Check event exists and user can access it
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found. It may have been deleted.")

    if not await permissions.can_view_event(db, user, event):
        raise HTTPException(status_code=403, detail="You don't have access to this event")

    if event.is_cancelled:
        raise HTTPException(status_code=400, detail="Cannot RSVP to a cancelled event")

    # Check for event conflicts (same day, across all families)
    if status == RSVPStatus.YES:
        conflicts = await check_event_conflicts(db, user.id, event)
        # Return conflict info but don't block
        conflict_warning = None
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

    response = {"message": f"RSVP updated to {status.value}"}
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


async def check_event_conflicts(
    db: AsyncSession, user_id: str, target_event: Event
) -> list[dict]:
    """
    Check for events on the same day that user has RSVPed yes to.
    Returns list of conflicting events.
    """
    # Get the date of the target event
    event_date = target_event.event_date.date()

    # Find all events the user has RSVPed yes to
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
    for event, rsvp in result.all():
        if event.event_date.date() == event_date:
            # Get family name
            from app.models import Family
            family_result = await db.execute(
                select(Family).where(Family.id == event.family_id)
            )
            family = family_result.scalar_one_or_none()

            conflicts.append({
                "title": event.title,
                "family_name": family.name if family else "Unknown",
                "date": event.event_date.isoformat(),
            })

    return conflicts


@router.get("/{event_id}/health-summary")
async def get_event_health_summary(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get anonymous health information for event attendees.

    Only returns health info from users who:
    1. Have RSVPed 'yes' to this event
    2. Have explicitly enabled health info sharing (share_health_info = true)

    Information is returned anonymously - no names are attached.
    Only event managers (creator or family admins) can access this.
    """
    from app.models import UserProfile

    # Get the event
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.rsvps))
        .where(Event.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Check user has permission to view health summary
    if not await permissions.can_manage_event(db, user, event):
        raise HTTPException(
            status_code=403,
            detail="Only event organizers can view health information"
        )

    # Get user IDs who RSVPed yes
    attending_user_ids = [
        rsvp.user_id for rsvp in event.rsvps
        if rsvp.status == RSVPStatus.YES
    ]

    if not attending_user_ids:
        return {
            "event_id": str(event.id),
            "attendee_count": 0,
            "shared_count": 0,
            "allergies": [],
            "dietary_restrictions": [],
            "medical_needs": [],
            "mobility_notes": [],
        }

    # Get health profiles for attending users who have opted in to share
    result = await db.execute(
        select(UserProfile).where(
            UserProfile.user_id.in_(attending_user_ids),
            UserProfile.share_health_info == True,
        )
    )
    profiles = result.scalars().all()

    # Collect anonymous health info
    allergies = []
    dietary_restrictions = []
    medical_needs = []
    mobility_notes = []

    for profile in profiles:
        if profile.allergies:
            # Split by comma if multiple allergies
            for allergy in profile.allergies.split(','):
                allergy = allergy.strip()
                if allergy and allergy not in allergies:
                    allergies.append(allergy)

        if profile.dietary_restrictions:
            for restriction in profile.dietary_restrictions.split(','):
                restriction = restriction.strip()
                if restriction and restriction not in dietary_restrictions:
                    dietary_restrictions.append(restriction)

        if profile.medical_needs:
            # Keep medical needs intact (don't split)
            if profile.medical_needs not in medical_needs:
                medical_needs.append(profile.medical_needs)

        if profile.mobility_notes:
            if profile.mobility_notes not in mobility_notes:
                mobility_notes.append(profile.mobility_notes)

    return {
        "event_id": str(event.id),
        "attendee_count": len(attending_user_ids),
        "shared_count": len(profiles),
        "allergies": allergies,
        "dietary_restrictions": dietary_restrictions,
        "medical_needs": medical_needs,
        "mobility_notes": mobility_notes,
    }
