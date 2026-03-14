"""Recurring event service — generate next occurrences automatically."""

import json
import logging
from datetime import UTC, datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.event_recurrence import EventRecurrence

logger = logging.getLogger(__name__)


def _compute_next_date(
    current_date: datetime,
    recurrence_type: str,
) -> datetime:
    """Compute the next occurrence date from the current one."""
    if recurrence_type == "yearly":
        return current_date + relativedelta(years=1)
    if recurrence_type == "monthly":
        return current_date + relativedelta(months=1)
    if recurrence_type == "weekly":
        return current_date + timedelta(weeks=1)
    msg = f"Unknown recurrence type: {recurrence_type}"
    raise ValueError(msg)


async def setup_recurrence(
    db: AsyncSession,
    event: Event,
    recurrence_type: str,
    end_date: datetime | None = None,
    max_occurrences: int | None = None,
) -> EventRecurrence:
    """Set up recurrence for an event.

    Computes the first next_occurrence and creates the EventRecurrence row.
    """
    event.is_recurring = True
    next_date = _compute_next_date(event.event_date, recurrence_type)

    recurrence = EventRecurrence(
        event_id=event.id,
        recurrence_type=recurrence_type,
        next_occurrence=next_date,
        end_date=end_date,
        max_occurrences=max_occurrences,
        occurrences_created=0,
    )
    db.add(recurrence)
    await db.flush()
    return recurrence


async def generate_pending_occurrences(
    db: AsyncSession,
    lookahead_days: int = 30,
) -> int:
    """Generate upcoming occurrences for all recurring events.

    Called by the scheduler. Creates new Event instances for recurrences
    whose next_occurrence falls within the lookahead window.
    Returns the number of new events created.
    """
    now = datetime.now(UTC)
    cutoff = now + timedelta(days=lookahead_days)

    # Find recurrences that need generating
    result = await db.execute(
        select(EventRecurrence)
        .join(Event, Event.id == EventRecurrence.event_id)
        .where(
            EventRecurrence.next_occurrence.isnot(None),
            EventRecurrence.next_occurrence <= cutoff,
            Event.cancelled_at.is_(None),
        )
    )
    recurrences = list(result.scalars().all())

    if not recurrences:
        return 0

    created = 0
    for rec in recurrences:
        # Check limits
        if rec.end_date and rec.next_occurrence and rec.next_occurrence > rec.end_date:
            rec.next_occurrence = None
            continue

        if rec.max_occurrences and rec.occurrences_created >= rec.max_occurrences:
            rec.next_occurrence = None
            continue

        # Load the source event
        source_result = await db.execute(select(Event).where(Event.id == rec.event_id))
        source = source_result.scalar_one_or_none()
        if not source:
            continue

        # Create the new occurrence
        new_event = Event(
            family_id=source.family_id,
            created_by_id=source.created_by_id,
            title=source.title,
            description=source.description,
            event_date=rec.next_occurrence,
            location_name=source.location_name,
            location_address=source.location_address,
            has_secret_santa=source.has_secret_santa,
            has_potluck=source.has_potluck,
            has_rsvp=source.has_rsvp,
            potluck_mode=source.potluck_mode,
            potluck_host_providing=source.potluck_host_providing,
            secret_santa_budget_min=source.secret_santa_budget_min,
            secret_santa_budget_max=source.secret_santa_budget_max,
            secret_santa_notes=source.secret_santa_notes,
            event_type=source.event_type,
            parent_event_id=source.parent_event_id,
        )
        db.add(new_event)
        await db.flush()

        # Copy type-specific details
        await _copy_type_details(db, source, new_event)

        # Advance the recurrence
        rec.occurrences_created = (rec.occurrences_created or 0) + 1
        current_next = rec.next_occurrence
        assert current_next is not None  # guaranteed by WHERE clause above
        new_next = _compute_next_date(current_next, rec.recurrence_type)
        rec.next_occurrence = new_next

        # Check if we've hit limits after advancing
        if rec.end_date and new_next > rec.end_date:
            rec.next_occurrence = None
        if rec.max_occurrences and rec.occurrences_created >= rec.max_occurrences:
            rec.next_occurrence = None

        created += 1

    await db.flush()
    return created


async def _copy_type_details(
    db: AsyncSession,
    source: Event,
    target: Event,
) -> None:
    """Copy type-specific detail rows from source to target event."""
    from app.services.event_detail_registry import clone_detail

    cloned = clone_detail(source, target.id)
    if cloned:
        db.add(cloned)


def recurrence_to_dict(recurrence: EventRecurrence | None) -> dict | None:
    """Convert an EventRecurrence to a response dict."""
    if not recurrence:
        return None
    return {
        "recurrence_type": recurrence.recurrence_type,
        "next_occurrence": (
            recurrence.next_occurrence.isoformat() if recurrence.next_occurrence else None
        ),
        "end_date": (recurrence.end_date.isoformat() if recurrence.end_date else None),
        "max_occurrences": recurrence.max_occurrences,
        "occurrences_created": recurrence.occurrences_created,
    }


def event_to_template_json(event: Event) -> str:
    """Serialize an event's config into template JSON for reuse."""
    data = {
        "title": event.title,
        "description": event.description,
        "location_name": event.location_name,
        "location_address": event.location_address,
        "event_type": event.event_type,
        "has_secret_santa": event.has_secret_santa,
        "has_potluck": event.has_potluck,
        "has_rsvp": event.has_rsvp,
        "potluck_mode": event.potluck_mode,
        "potluck_host_providing": event.potluck_host_providing,
        "secret_santa_budget_min": event.secret_santa_budget_min,
        "secret_santa_budget_max": event.secret_santa_budget_max,
        "secret_santa_notes": event.secret_santa_notes,
    }
    return json.dumps(data)
