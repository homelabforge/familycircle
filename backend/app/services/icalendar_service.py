"""iCalendar generation service for event export and family feed."""

import logging
from datetime import timedelta

from icalendar import Calendar
from icalendar import Event as ICalEvent

from app.models.event import Event

logger = logging.getLogger(__name__)

PRODID = "-//FamilyCircle//EN"
CALENDAR_NAME = "FamilyCircle"


def _make_base_calendar(name: str) -> Calendar:
    """Create a base iCalendar with standard properties."""
    cal = Calendar()
    cal.add("prodid", PRODID)
    cal.add("version", "2.0")
    cal.add("x-wr-calname", name)
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    return cal


def _event_to_vevent(event: Event) -> ICalEvent:
    """Convert a FamilyCircle Event model to an iCal VEVENT."""
    vevent = ICalEvent()
    vevent.add("uid", f"{event.id}@familycircle")
    vevent.add("summary", event.title)
    vevent.add("dtstart", event.event_date)
    # Default to 2-hour duration
    vevent.add("dtend", event.event_date + timedelta(hours=2))

    if event.description:
        vevent.add("description", event.description)

    # Location
    location_parts = []
    if event.location_name:
        location_parts.append(event.location_name)
    if event.location_address:
        location_parts.append(event.location_address)
    if location_parts:
        vevent.add("location", ", ".join(location_parts))

    if event.created_at:
        vevent.add("dtstamp", event.created_at)

    if event.is_cancelled:
        vevent.add("status", "CANCELLED")
    else:
        vevent.add("status", "CONFIRMED")

    # Event type as category
    vevent.add("categories", [event.event_type])

    return vevent


def generate_single_event_ics(event: Event) -> bytes:
    """Generate an .ics file for a single event."""
    cal = _make_base_calendar(event.title)
    cal.add_component(_event_to_vevent(event))
    return cal.to_ical()


def generate_family_feed(events: list[Event], family_name: str) -> bytes:
    """Generate an .ics feed for all events in a family."""
    cal = _make_base_calendar(f"{family_name} - {CALENDAR_NAME}")

    for event in events:
        # Skip secret birthdays
        if (
            event.event_type == "birthday"
            and event.birthday_detail
            and event.birthday_detail.is_secret
        ):
            continue

        # Skip cancelled events
        if event.is_cancelled:
            continue

        cal.add_component(_event_to_vevent(event))

    return cal.to_ical()
