"""Wedding sub-event template definitions and auto-creation."""

import logging
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event

logger = logging.getLogger(__name__)

WEDDING_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "full_wedding": [
        {"title": "Rehearsal Dinner", "offset_days": "-1"},
        {"title": "Ceremony", "offset_days": "0"},
        {"title": "Reception", "offset_days": "0"},
        {"title": "After-Party", "offset_days": "0"},
    ],
    "simple_wedding": [
        {"title": "Ceremony", "offset_days": "0"},
        {"title": "Reception", "offset_days": "0"},
    ],
}


async def create_sub_events_from_template(
    db: AsyncSession,
    parent_event: Event,
    template_name: str,
) -> list[Event]:
    """Create sub-events from a wedding template.

    Returns the list of created sub-events.
    """
    template = WEDDING_TEMPLATES.get(template_name)
    if not template:
        logger.warning("Unknown wedding template: %s", template_name)
        return []

    created = []
    for item in template:
        # Calculate sub-event date based on offset from parent
        sub_date = parent_event.event_date
        if sub_date and item["offset_days"] != "0":
            sub_date = sub_date + timedelta(days=int(item["offset_days"]))

        sub_event = Event(
            family_id=parent_event.family_id,
            created_by_id=parent_event.created_by_id,
            title=f"{parent_event.title} - {item['title']}",
            event_date=sub_date,
            location_name=parent_event.location_name,
            location_address=parent_event.location_address,
            event_type="general",
            parent_event_id=parent_event.id,
            has_rsvp=True,
        )
        db.add(sub_event)
        created.append(sub_event)

    await db.flush()
    logger.info(
        "Created %d sub-events from template '%s' for wedding %s",
        len(created),
        template_name,
        parent_event.id,
    )
    return created
