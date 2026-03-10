"""Events API endpoints - multi-family aware."""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
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
from app.models.baby_shower_detail import BabyShowerDetail
from app.models.birthday_detail import BirthdayDetail
from app.models.event import EventType, RSVPStatus
from app.models.holiday_detail import HolidayDetail
from app.models.wedding_detail import WeddingDetail, WeddingPartyMember
from app.schemas.event import EventCreate, EventUpdate
from app.schemas.wedding import WeddingPartyMemberCreate
from app.services.email import get_smtp_config, send_event_cancelled_email
from app.services.notifications.dispatcher import NotificationDispatcher
from app.services.permissions import permissions
from app.services.recurrence import recurrence_to_dict

logger = logging.getLogger(__name__)

router = APIRouter()


class EventCancel(BaseModel):
    """Cancel event request."""

    reason: str | None = None


class RSVPRequest(BaseModel):
    """RSVP request."""

    status: str  # yes, no, maybe


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

    # Type-specific details
    if event.holiday_detail:
        result["holiday_detail"] = {
            "holiday_name": event.holiday_detail.holiday_name,
            "custom_holiday_name": event.holiday_detail.custom_holiday_name,
            "display_name": event.holiday_detail.display_name,
            "year": event.holiday_detail.year,
        }
    else:
        result["holiday_detail"] = None

    if event.birthday_detail:
        result["birthday_detail"] = {
            "birthday_person_id": event.birthday_detail.birthday_person_id,
            "birthday_person_name": event.birthday_detail.birthday_person_name,
            "birth_date": (
                event.birthday_detail.birth_date.isoformat()
                if event.birthday_detail.birth_date
                else None
            ),
            "age_turning": event.birthday_detail.age_turning,
            "is_secret": event.birthday_detail.is_secret,
            "theme": event.birthday_detail.theme,
        }
    else:
        result["birthday_detail"] = None

    if event.baby_shower_detail:
        result["baby_shower_detail"] = {
            "parent1_name": event.baby_shower_detail.parent1_name,
            "parent2_name": event.baby_shower_detail.parent2_name,
            "baby_name": event.baby_shower_detail.baby_name,
            "gender": event.baby_shower_detail.gender,
            "due_date": (
                event.baby_shower_detail.due_date.isoformat()
                if event.baby_shower_detail.due_date
                else None
            ),
            "registry_url": event.baby_shower_detail.registry_url,
            "is_gender_reveal": event.baby_shower_detail.is_gender_reveal,
            "display_parents": event.baby_shower_detail.display_parents,
        }
    else:
        result["baby_shower_detail"] = None

    if event.wedding_detail:
        result["wedding_detail"] = {
            "partner1_name": event.wedding_detail.partner1_name,
            "partner2_name": event.wedding_detail.partner2_name,
            "wedding_date": (
                event.wedding_detail.wedding_date.isoformat()
                if event.wedding_detail.wedding_date
                else None
            ),
            "venue_name": event.wedding_detail.venue_name,
            "registry_url": event.wedding_detail.registry_url,
            "color_theme": event.wedding_detail.color_theme,
            "display_couple": event.wedding_detail.display_couple,
        }
    else:
        result["wedding_detail"] = None

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

    # Create type-specific details
    if request.event_type == EventType.HOLIDAY.value and request.holiday_detail:
        detail = HolidayDetail(
            event_id=event.id,
            holiday_name=request.holiday_detail.holiday_name,
            custom_holiday_name=request.holiday_detail.custom_holiday_name,
            year=request.holiday_detail.year,
        )
        db.add(detail)

    if request.event_type == EventType.BIRTHDAY.value and request.birthday_detail:
        detail = BirthdayDetail(
            event_id=event.id,
            birthday_person_id=request.birthday_detail.birthday_person_id,
            birthday_person_name=request.birthday_detail.birthday_person_name,
            birth_date=request.birthday_detail.birth_date,
            age_turning=request.birthday_detail.age_turning,
            is_secret=request.birthday_detail.is_secret,
            theme=request.birthday_detail.theme,
        )
        db.add(detail)

    if request.event_type == EventType.BABY_SHOWER.value and request.baby_shower_detail:
        detail = BabyShowerDetail(
            event_id=event.id,
            parent1_name=request.baby_shower_detail.parent1_name,
            parent2_name=request.baby_shower_detail.parent2_name,
            baby_name=request.baby_shower_detail.baby_name,
            gender=request.baby_shower_detail.gender,
            due_date=request.baby_shower_detail.due_date,
            registry_url=request.baby_shower_detail.registry_url,
            is_gender_reveal=request.baby_shower_detail.is_gender_reveal,
        )
        db.add(detail)

    if request.event_type == EventType.WEDDING.value and request.wedding_detail:
        sub_event_template = request.wedding_detail.sub_event_template
        detail = WeddingDetail(
            event_id=event.id,
            partner1_name=request.wedding_detail.partner1_name,
            partner2_name=request.wedding_detail.partner2_name,
            wedding_date=request.wedding_detail.wedding_date,
            venue_name=request.wedding_detail.venue_name,
            registry_url=request.wedding_detail.registry_url,
            color_theme=request.wedding_detail.color_theme,
            sub_event_template=sub_event_template,
        )
        db.add(detail)

        # Auto-create sub-events from template
        if sub_event_template:
            await db.flush()  # Ensure event.id is available
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

    # Fire notification (non-blocking, errors logged)
    try:
        family_id = user.current_family_id or ""
        creator_name = await get_member_display_name(db, user.id, family_id)
        from app.models import Family

        family_result = await db.execute(select(Family).where(Family.id == family_id))
        family = family_result.scalar_one_or_none()
        family_name = family.name if family else "your family"
        event_date_str = event.event_date.strftime("%B %d, %Y") if event.event_date else "TBD"

        dispatcher = NotificationDispatcher(db)
        await dispatcher.notify_event_created(
            event_title=event.title,
            family_name=family_name,
            creator_name=creator_name,
            event_date=event_date_str,
        )
    except Exception as e:
        logger.error("Failed to send event_created notification: %s", e)

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

    # Update type-specific details (upsert pattern)
    if request.holiday_detail is not None and event.event_type == EventType.HOLIDAY.value:
        if event.holiday_detail:
            event.holiday_detail.holiday_name = request.holiday_detail.holiday_name
            event.holiday_detail.custom_holiday_name = request.holiday_detail.custom_holiday_name
            event.holiday_detail.year = request.holiday_detail.year
        else:
            db.add(
                HolidayDetail(
                    event_id=event.id,
                    holiday_name=request.holiday_detail.holiday_name,
                    custom_holiday_name=request.holiday_detail.custom_holiday_name,
                    year=request.holiday_detail.year,
                )
            )

    if request.birthday_detail is not None and event.event_type == EventType.BIRTHDAY.value:
        if event.birthday_detail:
            event.birthday_detail.birthday_person_id = request.birthday_detail.birthday_person_id
            event.birthday_detail.birthday_person_name = (
                request.birthday_detail.birthday_person_name
            )
            event.birthday_detail.birth_date = request.birthday_detail.birth_date
            event.birthday_detail.age_turning = request.birthday_detail.age_turning
            event.birthday_detail.is_secret = request.birthday_detail.is_secret
            event.birthday_detail.theme = request.birthday_detail.theme
        else:
            db.add(
                BirthdayDetail(
                    event_id=event.id,
                    birthday_person_id=request.birthday_detail.birthday_person_id,
                    birthday_person_name=request.birthday_detail.birthday_person_name,
                    birth_date=request.birthday_detail.birth_date,
                    age_turning=request.birthday_detail.age_turning,
                    is_secret=request.birthday_detail.is_secret,
                    theme=request.birthday_detail.theme,
                )
            )

    if request.baby_shower_detail is not None and event.event_type == EventType.BABY_SHOWER.value:
        if event.baby_shower_detail:
            event.baby_shower_detail.parent1_name = request.baby_shower_detail.parent1_name
            event.baby_shower_detail.parent2_name = request.baby_shower_detail.parent2_name
            event.baby_shower_detail.baby_name = request.baby_shower_detail.baby_name
            event.baby_shower_detail.gender = request.baby_shower_detail.gender
            event.baby_shower_detail.due_date = request.baby_shower_detail.due_date
            event.baby_shower_detail.registry_url = request.baby_shower_detail.registry_url
            event.baby_shower_detail.is_gender_reveal = request.baby_shower_detail.is_gender_reveal
        else:
            db.add(
                BabyShowerDetail(
                    event_id=event.id,
                    parent1_name=request.baby_shower_detail.parent1_name,
                    parent2_name=request.baby_shower_detail.parent2_name,
                    baby_name=request.baby_shower_detail.baby_name,
                    gender=request.baby_shower_detail.gender,
                    due_date=request.baby_shower_detail.due_date,
                    registry_url=request.baby_shower_detail.registry_url,
                    is_gender_reveal=request.baby_shower_detail.is_gender_reveal,
                )
            )

    if request.wedding_detail is not None and event.event_type == EventType.WEDDING.value:
        if event.wedding_detail:
            event.wedding_detail.partner1_name = request.wedding_detail.partner1_name
            event.wedding_detail.partner2_name = request.wedding_detail.partner2_name
            event.wedding_detail.wedding_date = request.wedding_detail.wedding_date
            event.wedding_detail.venue_name = request.wedding_detail.venue_name
            event.wedding_detail.registry_url = request.wedding_detail.registry_url
            event.wedding_detail.color_theme = request.wedding_detail.color_theme
        else:
            db.add(
                WeddingDetail(
                    event_id=event.id,
                    partner1_name=request.wedding_detail.partner1_name,
                    partner2_name=request.wedding_detail.partner2_name,
                    wedding_date=request.wedding_detail.wedding_date,
                    venue_name=request.wedding_detail.venue_name,
                    registry_url=request.wedding_detail.registry_url,
                    color_theme=request.wedding_detail.color_theme,
                )
            )

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

    # Fire notification via dispatcher
    try:
        canceller_name = await get_member_display_name(db, user.id, user.current_family_id or "")
        dispatcher = NotificationDispatcher(db)
        await dispatcher.notify_event_cancelled(
            event_title=event.title,
            cancelled_by=canceller_name,
            reason=request.reason,
        )
    except Exception as e:
        logger.error("Failed to send event_cancelled notification: %s", e)

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

    # Check event exists and user can access it (family + secret birthday → 404)
    event = await resolve_event_or_404(db, event_id, user)

    if event.is_cancelled:
        raise HTTPException(status_code=400, detail="Cannot RSVP to a cancelled event")

    # Check for event conflicts (same day, across all families)
    conflict_warning = None
    if status == RSVPStatus.YES:
        conflicts = await check_event_conflicts(db, user.id, event)
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

    # Fire notification for RSVP
    try:
        member_name = await get_member_display_name(db, user.id, user.current_family_id or "")
        dispatcher = NotificationDispatcher(db)
        await dispatcher.notify_rsvp_received(
            event_title=event.title,
            member_name=member_name,
            status=status.value,
        )
    except Exception as e:
        logger.error("Failed to send rsvp_received notification: %s", e)

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
    await resolve_event_or_404(db, event_id, user)

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


async def check_event_conflicts(db: AsyncSession, user_id: str, target_event: Event) -> list[dict]:
    """Check for events on the same day that user has RSVPed yes to."""
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
    for event, _rsvp in result.all():
        if event.event_date.date() == event_date:
            # Get family name
            from app.models import Family

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

    # Create type-specific details (same as create_event)
    if request.event_type == EventType.HOLIDAY.value and request.holiday_detail:
        db.add(
            HolidayDetail(
                event_id=event.id,
                holiday_name=request.holiday_detail.holiday_name,
                custom_holiday_name=request.holiday_detail.custom_holiday_name,
                year=request.holiday_detail.year,
            )
        )

    if request.event_type == EventType.BIRTHDAY.value and request.birthday_detail:
        db.add(
            BirthdayDetail(
                event_id=event.id,
                birthday_person_id=request.birthday_detail.birthday_person_id,
                birthday_person_name=request.birthday_detail.birthday_person_name,
                birth_date=request.birthday_detail.birth_date,
                age_turning=request.birthday_detail.age_turning,
                is_secret=request.birthday_detail.is_secret,
                theme=request.birthday_detail.theme,
            )
        )

    if request.event_type == EventType.BABY_SHOWER.value and request.baby_shower_detail:
        db.add(
            BabyShowerDetail(
                event_id=event.id,
                parent1_name=request.baby_shower_detail.parent1_name,
                parent2_name=request.baby_shower_detail.parent2_name,
                baby_name=request.baby_shower_detail.baby_name,
                gender=request.baby_shower_detail.gender,
                due_date=request.baby_shower_detail.due_date,
                registry_url=request.baby_shower_detail.registry_url,
                is_gender_reveal=request.baby_shower_detail.is_gender_reveal,
            )
        )

    if request.event_type == EventType.WEDDING.value and request.wedding_detail:
        db.add(
            WeddingDetail(
                event_id=event.id,
                partner1_name=request.wedding_detail.partner1_name,
                partner2_name=request.wedding_detail.partner2_name,
                wedding_date=request.wedding_detail.wedding_date,
                venue_name=request.wedding_detail.venue_name,
                registry_url=request.wedding_detail.registry_url,
                color_theme=request.wedding_detail.color_theme,
            )
        )

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
