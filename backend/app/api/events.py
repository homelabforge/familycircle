"""Events API endpoints - multi-family aware."""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import require_family_context
from app.api.event_helpers import (
    is_secret_birthday_for_user,
    resolve_event_or_404,
    validate_event_type_and_details,
)
from app.db import get_db_session
from app.models import Event, EventRSVP, FamilyMembership, User
from app.models.event import EventType, RSVPStatus
from app.models.wedding_detail import WeddingPartyMember
from app.schemas.event import EventCreate, EventUpdate
from app.schemas.wedding import WeddingPartyMemberCreate
from app.services.email import get_smtp_config, send_event_cancelled_email
from app.services.notifications.fire import send_notification_background
from app.services.permissions import permissions
from app.services.recurrence import recurrence_to_dict

logger = logging.getLogger(__name__)

router = APIRouter()


class EventCancel(BaseModel):
    """Cancel event request."""

    reason: str | None = None


async def get_member_display_name(db: AsyncSession, user_id: str, family_id: str) -> str:
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
    user_rsvp: EventRSVP | None = None,
    can_manage: bool = False,
) -> dict:
    """Convert event to response dict."""
    result = {
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
        "has_rsvp": event.has_rsvp,
        # Potluck configuration
        "potluck_mode": event.potluck_mode,
        "potluck_host_providing": event.potluck_host_providing,
        "secret_santa_assigned": event.secret_santa_assigned,
        # Gift Exchange rules
        "secret_santa_budget_min": event.secret_santa_budget_min,
        "secret_santa_budget_max": event.secret_santa_budget_max,
        "secret_santa_notes": event.secret_santa_notes,
        # Event type
        "event_type": event.event_type,
        "parent_event_id": str(event.parent_event_id) if event.parent_event_id else None,
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
        # Headcount: attending members + their additional guests
        "headcount": sum(1 + len(r.guests) for r in event.rsvps if r.status == RSVPStatus.YES),
        "user_rsvp": user_rsvp.status.value if user_rsvp else None,
        "can_manage": can_manage,
        # Recurrence
        "is_recurring": event.is_recurring,
        "recurrence": recurrence_to_dict(event.recurrence),
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }

    # Type-specific details (via registry)
    from app.services.event_detail_registry import serialize_all_details

    result.update(serialize_all_details(event))

    # Sub-events (for wedding or any parent event)
    active_sub_events = [s for s in event.sub_events if not s.is_cancelled]
    result["sub_event_count"] = len(active_sub_events)
    if event.sub_events:
        result["sub_events"] = [
            {
                "id": str(sub.id),
                "title": sub.title,
                "event_date": sub.event_date.isoformat() if sub.event_date else None,
                "event_type": sub.event_type,
                "is_cancelled": sub.is_cancelled,
            }
            for sub in event.sub_events
        ]
    else:
        result["sub_events"] = []

    # Wedding party members
    if event.wedding_party_members:
        result["wedding_party"] = [
            {
                "id": str(m.id),
                "name": m.name,
                "role": m.role,
                "side": m.side,
                "user_id": str(m.user_id) if m.user_id else None,
                "display_role": m.display_role,
            }
            for m in event.wedding_party_members
        ]
    else:
        result["wedding_party"] = []

    return result


@router.get("")
async def list_events(
    event_type: str | None = None,
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
    cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

    query = (
        select(Event)
        .where(
            Event.family_id == user.current_family_id,
            # Filter out cancelled events older than retention period
            or_(
                Event.cancelled_at.is_(None),  # Not cancelled
                Event.cancelled_at >= cutoff_date,  # Cancelled but within retention
            ),
        )
        .order_by(Event.event_date.desc())
        .options(selectinload(Event.sub_events))
    )

    # Optional event type filter
    if event_type:
        query = query.where(Event.event_type == event_type)

    result = await db.execute(query)
    events = result.scalars().all()

    # Filter out secret birthday events for the birthday person
    events = [
        e for e in events if not is_secret_birthday_for_user(e, str(user.id), user.is_super_admin)
    ]

    # Get user's RSVPs
    rsvp_result = await db.execute(select(EventRSVP).where(EventRSVP.user_id == user.id))
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
        .options(selectinload(Event.sub_events))
    )
    events = result.scalars().all()

    # Filter out secret birthday events for the birthday person
    events = [
        e for e in events if not is_secret_birthday_for_user(e, str(user.id), user.is_super_admin)
    ]

    # Get user's RSVPs
    rsvp_result = await db.execute(select(EventRSVP).where(EventRSVP.user_id == user.id))
    user_rsvps = {str(r.event_id): r for r in rsvp_result.scalars().all()}

    events_data = []
    for e in events:
        can_manage = await permissions.can_manage_event(db, user, e)
        events_data.append(event_to_dict(e, user_rsvps.get(str(e.id)), can_manage))

    return {"events": events_data}


@router.get("/holidays")
async def list_predefined_holidays():
    """Get list of predefined holidays for the holiday picker."""
    from app.models.holiday_detail import PREDEFINED_HOLIDAYS

    return {"holidays": PREDEFINED_HOLIDAYS}


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a specific event."""
    event = await resolve_event_or_404(
        db, event_id, user, options=[selectinload(Event.rsvps), selectinload(Event.sub_events)]
    )

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
        rsvps.append(
            {
                "user_id": str(rsvp.user_id),
                "display_name": display_name,
                "status": rsvp.status.value,
            }
        )

    can_manage = await permissions.can_manage_event(db, user, event)
    response = event_to_dict(event, user_rsvp, can_manage)
    response["rsvps"] = rsvps

    return response


@router.post("")
async def create_event(
    request: EventCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new event in current family."""
    validate_event_type_and_details(request)

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
        has_rsvp=request.has_rsvp,
        potluck_mode=request.potluck_mode,
        potluck_host_providing=request.potluck_host_providing,
        secret_santa_budget_min=request.secret_santa_budget_min,
        secret_santa_budget_max=request.secret_santa_budget_max,
        secret_santa_notes=request.secret_santa_notes,
        event_type=request.event_type,
    )
    db.add(event)
    await db.flush()  # Get event.id before adding detail rows

    # Create type-specific details (via registry)
    from app.services.event_detail_registry import create_detail_from_request

    detail = create_detail_from_request(event.id, request.event_type, request)
    if detail:
        db.add(detail)

    # Wedding-specific: auto-create sub-events from template
    if request.event_type == EventType.WEDDING.value and request.wedding_detail:
        sub_event_template = request.wedding_detail.sub_event_template
        if sub_event_template:
            await db.flush()
            from app.services.wedding_templates import create_sub_events_from_template

            await create_sub_events_from_template(db, event, sub_event_template)

    # Set up recurrence if requested
    if request.recurrence_type:
        from app.models.event_recurrence import RECURRENCE_TYPES
        from app.services.recurrence import setup_recurrence

        if request.recurrence_type not in RECURRENCE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid recurrence type. Must be one of: {', '.join(RECURRENCE_TYPES)}",
            )
        await db.flush()
        await setup_recurrence(
            db,
            event,
            recurrence_type=request.recurrence_type,
            end_date=request.recurrence_end_date,
            max_occurrences=request.recurrence_max_occurrences,
        )

    await db.commit()
    await db.refresh(event)

    # Gather notification data before backgrounding (uses request-scoped db)
    family_id = user.current_family_id or ""
    creator_name = await get_member_display_name(db, user.id, family_id)
    from app.models import Family

    family_result = await db.execute(select(Family).where(Family.id == family_id))
    family = family_result.scalar_one_or_none()
    family_name = family.name if family else "your family"
    event_date_str = event.event_date.strftime("%B %d, %Y") if event.event_date else "TBD"

    background_tasks.add_task(
        send_notification_background,
        "notify_event_created",
        event_title=event.title,
        family_name=family_name,
        creator_name=creator_name,
        event_date=event_date_str,
    )

    return {"message": "Event created", "id": str(event.id)}


@router.put("/{event_id}")
async def update_event(
    event_id: str,
    request: EventUpdate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Update an event (creator or admin only)."""
    event = await resolve_event_or_404(db, event_id, user)

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
    if request.has_rsvp is not None:
        event.has_rsvp = request.has_rsvp
    if request.potluck_mode is not None:
        event.potluck_mode = request.potluck_mode
    if request.potluck_host_providing is not None:
        event.potluck_host_providing = request.potluck_host_providing
    if request.secret_santa_budget_min is not None:
        event.secret_santa_budget_min = request.secret_santa_budget_min
    if request.secret_santa_budget_max is not None:
        event.secret_santa_budget_max = request.secret_santa_budget_max
    if request.secret_santa_notes is not None:
        event.secret_santa_notes = request.secret_santa_notes

    # Update type-specific details (upsert via registry)
    from app.services.event_detail_registry import update_detail_from_request

    update_detail_from_request(event, event.event_type, request, db)

    await db.commit()

    return {"message": "Event updated"}


@router.post("/{event_id}/cancel")
async def cancel_event(
    event_id: str,
    request: EventCancel,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Cancel an event (creator or admin only)."""
    event = await resolve_event_or_404(db, event_id, user)

    if not await permissions.can_manage_event(db, user, event):
        raise HTTPException(
            status_code=403, detail="You don't have permission to cancel this event"
        )

    # Load rsvps for notification emails
    await db.refresh(event, ["rsvps"])

    if event.is_cancelled:
        raise HTTPException(status_code=400, detail="Event is already cancelled")

    event.cancelled_at = datetime.now(UTC)
    event.cancellation_reason = request.reason

    await db.commit()

    # Send notifications to RSVPed users (yes or maybe)
    smtp_config = await get_smtp_config(db)
    if smtp_config.is_configured:
        # Get attendees who RSVPed yes or maybe
        attendee_user_ids = [
            r.user_id for r in event.rsvps if r.status in (RSVPStatus.YES, RSVPStatus.MAYBE)
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
                    user_result = await db.execute(select(User).where(User.id == attendee_id))
                    attendee = user_result.scalar_one_or_none()
                    if not attendee:
                        continue

                    # Get display name
                    attendee_name = await get_member_display_name(db, attendee_id, event.family_id)

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

    # Fire notification in background
    canceller_name = await get_member_display_name(db, user.id, user.current_family_id or "")
    background_tasks.add_task(
        send_notification_background,
        "notify_event_cancelled",
        event_title=event.title,
        cancelled_by=canceller_name,
        reason=request.reason,
    )

    return {"message": "Event cancelled"}


@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete an event (creator or admin only)."""
    event = await resolve_event_or_404(db, event_id, user)

    if not await permissions.can_manage_event(db, user, event):
        raise HTTPException(
            status_code=403, detail="You don't have permission to delete this event"
        )

    # Load rsvps to check for YES responses
    await db.refresh(event, ["rsvps"])

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


@router.get("/{event_id}/health-summary")
async def get_event_health_summary(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get anonymous health information for event attendees.

    Only returns health info from users who:
    1. Have RSVPed 'yes' to this event
    2. Have explicitly enabled health info sharing (share_health_info = true)

    Information is returned anonymously - no names are attached.
    Only event managers (creator or family admins) can access this.
    """
    from app.models import UserProfile

    event = await resolve_event_or_404(db, event_id, user)

    # Check user has permission to view health summary
    if not await permissions.can_manage_event(db, user, event):
        raise HTTPException(
            status_code=403, detail="Only event organizers can view health information"
        )

    # Load rsvps for attendee check
    await db.refresh(event, ["rsvps"])

    # Get user IDs who RSVPed yes
    attending_user_ids = [rsvp.user_id for rsvp in event.rsvps if rsvp.status == RSVPStatus.YES]

    if not attending_user_ids:
        return {
            "event_id": str(event.id),
            "attendee_count": 0,
            "guest_count": 0,
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
            UserProfile.share_health_info.is_(True),
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
            for allergy in profile.allergies.split(","):
                allergy = allergy.strip()
                if allergy and allergy not in allergies:
                    allergies.append(allergy)

        if profile.dietary_restrictions:
            for restriction in profile.dietary_restrictions.split(","):
                restriction = restriction.strip()
                if restriction and restriction not in dietary_restrictions:
                    dietary_restrictions.append(restriction)

        if profile.medical_needs:
            if profile.medical_needs not in medical_needs:
                medical_needs.append(profile.medical_needs)

        if profile.mobility_notes:
            if profile.mobility_notes not in mobility_notes:
                mobility_notes.append(profile.mobility_notes)

    # Also collect dietary/allergy info from RSVP additional guests
    guest_allergies: list[str] = []
    guest_dietary: list[str] = []
    guest_count = 0
    for rsvp in event.rsvps:
        if rsvp.status == RSVPStatus.YES:
            for guest in rsvp.guests:
                guest_count += 1
                if guest.allergies:
                    for a in guest.allergies.split(","):
                        a = a.strip()
                        if a and a not in allergies and a not in guest_allergies:
                            guest_allergies.append(a)
                if guest.dietary_restrictions:
                    for d in guest.dietary_restrictions.split(","):
                        d = d.strip()
                        if d and d not in dietary_restrictions and d not in guest_dietary:
                            guest_dietary.append(d)

    return {
        "event_id": str(event.id),
        "attendee_count": len(attending_user_ids),
        "guest_count": guest_count,
        "shared_count": len(profiles),
        "allergies": allergies + guest_allergies,
        "dietary_restrictions": dietary_restrictions + guest_dietary,
        "medical_needs": medical_needs,
        "mobility_notes": mobility_notes,
    }


# --- Sub-events endpoints ---


@router.get("/{event_id}/sub-events")
async def list_sub_events(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List sub-events for a parent event."""
    await resolve_event_or_404(db, event_id, user)

    # Get sub-events
    result = await db.execute(
        select(Event)
        .where(Event.parent_event_id == event_id, Event.cancelled_at.is_(None))
        .order_by(Event.event_date.asc())
        .options(selectinload(Event.sub_events))
    )
    sub_events = result.scalars().all()

    # Filter secret birthdays
    sub_events = [
        e
        for e in sub_events
        if not is_secret_birthday_for_user(e, str(user.id), user.is_super_admin)
    ]

    # Get user RSVPs for sub-events
    sub_event_ids = [str(e.id) for e in sub_events]
    rsvp_result = await db.execute(
        select(EventRSVP).where(
            EventRSVP.user_id == user.id,
            EventRSVP.event_id.in_(sub_event_ids),
        )
    )
    user_rsvps = {str(r.event_id): r for r in rsvp_result.scalars().all()}

    events_data = []
    for e in sub_events:
        can_manage = await permissions.can_manage_event(db, user, e)
        events_data.append(event_to_dict(e, user_rsvps.get(str(e.id)), can_manage))

    return {"sub_events": events_data}


@router.post("/{event_id}/sub-events")
async def create_sub_event(
    event_id: str,
    request: EventCreate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a sub-event under a parent event."""
    parent = await resolve_event_or_404(db, event_id, user)

    if not await permissions.can_manage_event(db, user, parent):
        raise HTTPException(status_code=403, detail="You don't have permission to add sub-events")

    if parent.is_cancelled:
        raise HTTPException(status_code=400, detail="Cannot add sub-events to a cancelled event")

    # Validate event type and required details
    validate_event_type_and_details(request)

    # Override parent_event_id and family_id
    event = Event(
        family_id=parent.family_id,
        created_by_id=user.id,
        title=request.title,
        description=request.description,
        event_date=request.event_date,
        location_name=request.location_name,
        location_address=request.location_address,
        has_secret_santa=request.has_secret_santa,
        has_potluck=request.has_potluck,
        has_rsvp=request.has_rsvp,
        potluck_mode=request.potluck_mode,
        potluck_host_providing=request.potluck_host_providing,
        secret_santa_budget_min=request.secret_santa_budget_min,
        secret_santa_budget_max=request.secret_santa_budget_max,
        secret_santa_notes=request.secret_santa_notes,
        event_type=request.event_type,
        parent_event_id=event_id,
    )
    db.add(event)
    await db.flush()

    # Create type-specific details (via registry — shared with create_event)
    from app.services.event_detail_registry import create_detail_from_request

    detail = create_detail_from_request(event.id, request.event_type, request)
    if detail:
        db.add(detail)

    await db.commit()
    await db.refresh(event)

    return {"message": "Sub-event created", "id": str(event.id)}


# --- Wedding party endpoints ---


@router.get("/{event_id}/wedding-party")
async def list_wedding_party(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List wedding party members for an event."""
    await resolve_event_or_404(db, event_id, user)

    result = await db.execute(
        select(WeddingPartyMember)
        .where(WeddingPartyMember.event_id == event_id)
        .order_by(WeddingPartyMember.side, WeddingPartyMember.role)
    )
    members = result.scalars().all()

    return {
        "members": [
            {
                "id": str(m.id),
                "name": m.name,
                "role": m.role,
                "side": m.side,
                "user_id": str(m.user_id) if m.user_id else None,
                "display_role": m.display_role,
            }
            for m in members
        ]
    }


@router.post("/{event_id}/wedding-party")
async def add_wedding_party_member(
    event_id: str,
    request: WeddingPartyMemberCreate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Add a wedding party member."""
    event = await resolve_event_or_404(db, event_id, user)

    if event.event_type != EventType.WEDDING.value:
        raise HTTPException(status_code=400, detail="Wedding party is only for wedding events")

    if not await permissions.can_manage_event(db, user, event):
        raise HTTPException(
            status_code=403, detail="You don't have permission to manage the wedding party"
        )

    member = WeddingPartyMember(
        event_id=event_id,
        user_id=request.user_id,
        name=request.name,
        role=request.role,
        side=request.side,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return {
        "message": "Wedding party member added",
        "member": {
            "id": str(member.id),
            "name": member.name,
            "role": member.role,
            "side": member.side,
            "user_id": str(member.user_id) if member.user_id else None,
            "display_role": member.display_role,
        },
    }


@router.delete("/{event_id}/wedding-party/{member_id}")
async def remove_wedding_party_member(
    event_id: str,
    member_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Remove a wedding party member."""
    event = await resolve_event_or_404(db, event_id, user)

    if not await permissions.can_manage_event(db, user, event):
        raise HTTPException(
            status_code=403, detail="You don't have permission to manage the wedding party"
        )

    result = await db.execute(
        select(WeddingPartyMember).where(
            WeddingPartyMember.id == member_id,
            WeddingPartyMember.event_id == event_id,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404, detail="Wedding party member not found")

    await db.delete(member)
    await db.commit()

    return {"message": "Wedding party member removed"}
