"""Event detail handler registry — eliminates type-specific if/elif branching.

Each event type (holiday, birthday, baby_shower, wedding) registers a handler
that knows how to create, update, serialize, and clone its detail model.
The 'general' type has no handler (no detail model).

Adding a new event type requires:
1. A new detail model in app/models/
2. A new schema in app/schemas/
3. A new handler class registered here
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.baby_shower_detail import BabyShowerDetail
from app.models.birthday_detail import BirthdayDetail
from app.models.event import EventType
from app.models.holiday_detail import HolidayDetail
from app.models.wedding_detail import WeddingDetail


class EventDetailHandler(ABC):
    """Base class for event type detail handlers."""

    detail_attr: str  # Relationship name on Event model (e.g., "holiday_detail")

    @abstractmethod
    def create_from_request(self, event_id: str, data: Any) -> Any:
        """Create a detail model instance from a request schema."""

    @abstractmethod
    def update_from_request(self, existing: Any, data: Any) -> None:
        """Update an existing detail model from a request schema."""

    @abstractmethod
    def serialize(self, detail: Any) -> dict:
        """Serialize a detail model to a response dict."""

    @abstractmethod
    def clone(self, source_detail: Any, target_event_id: str) -> Any:
        """Clone a detail for recurrence — may transform fields (e.g., year+1)."""


class HolidayDetailHandler(EventDetailHandler):
    detail_attr = "holiday_detail"

    def create_from_request(self, event_id: str, data: Any) -> HolidayDetail:
        return HolidayDetail(
            event_id=event_id,
            holiday_name=data.holiday_name,
            custom_holiday_name=data.custom_holiday_name,
            year=data.year,
        )

    def update_from_request(self, existing: HolidayDetail, data: Any) -> None:
        existing.holiday_name = data.holiday_name
        existing.custom_holiday_name = data.custom_holiday_name
        existing.year = data.year

    def serialize(self, detail: HolidayDetail) -> dict:
        return {
            "holiday_name": detail.holiday_name,
            "custom_holiday_name": detail.custom_holiday_name,
            "display_name": detail.display_name,
            "year": detail.year,
        }

    def clone(self, source_detail: HolidayDetail, target_event_id: str) -> HolidayDetail:
        return HolidayDetail(
            event_id=target_event_id,
            holiday_name=source_detail.holiday_name,
            custom_holiday_name=source_detail.custom_holiday_name,
            year=source_detail.year + 1 if source_detail.year else None,
        )


class BirthdayDetailHandler(EventDetailHandler):
    detail_attr = "birthday_detail"

    def create_from_request(self, event_id: str, data: Any) -> BirthdayDetail:
        return BirthdayDetail(
            event_id=event_id,
            birthday_person_id=data.birthday_person_id,
            birthday_person_name=data.birthday_person_name,
            birth_date=data.birth_date,
            age_turning=data.age_turning,
            is_secret=data.is_secret,
            theme=data.theme,
        )

    def update_from_request(self, existing: BirthdayDetail, data: Any) -> None:
        existing.birthday_person_id = data.birthday_person_id
        existing.birthday_person_name = data.birthday_person_name
        existing.birth_date = data.birth_date
        existing.age_turning = data.age_turning
        existing.is_secret = data.is_secret
        existing.theme = data.theme

    def serialize(self, detail: BirthdayDetail) -> dict:
        return {
            "birthday_person_id": detail.birthday_person_id,
            "birthday_person_name": detail.birthday_person_name,
            "birth_date": detail.birth_date.isoformat() if detail.birth_date else None,
            "age_turning": detail.age_turning,
            "is_secret": detail.is_secret,
            "theme": detail.theme,
        }

    def clone(self, source_detail: BirthdayDetail, target_event_id: str) -> BirthdayDetail:
        return BirthdayDetail(
            event_id=target_event_id,
            birthday_person_id=source_detail.birthday_person_id,
            birthday_person_name=source_detail.birthday_person_name,
            birth_date=source_detail.birth_date,
            age_turning=source_detail.age_turning + 1 if source_detail.age_turning else None,
            is_secret=source_detail.is_secret,
            theme=source_detail.theme,
        )


class BabyShowerDetailHandler(EventDetailHandler):
    detail_attr = "baby_shower_detail"

    def create_from_request(self, event_id: str, data: Any) -> BabyShowerDetail:
        return BabyShowerDetail(
            event_id=event_id,
            parent1_name=data.parent1_name,
            parent2_name=data.parent2_name,
            baby_name=data.baby_name,
            gender=data.gender,
            due_date=data.due_date,
            registry_url=data.registry_url,
            is_gender_reveal=data.is_gender_reveal,
        )

    def update_from_request(self, existing: BabyShowerDetail, data: Any) -> None:
        existing.parent1_name = data.parent1_name
        existing.parent2_name = data.parent2_name
        existing.baby_name = data.baby_name
        existing.gender = data.gender
        existing.due_date = data.due_date
        existing.registry_url = data.registry_url
        existing.is_gender_reveal = data.is_gender_reveal

    def serialize(self, detail: BabyShowerDetail) -> dict:
        return {
            "parent1_name": detail.parent1_name,
            "parent2_name": detail.parent2_name,
            "baby_name": detail.baby_name,
            "gender": detail.gender,
            "due_date": detail.due_date.isoformat() if detail.due_date else None,
            "registry_url": detail.registry_url,
            "is_gender_reveal": detail.is_gender_reveal,
            "display_parents": detail.display_parents,
        }

    def clone(self, source_detail: BabyShowerDetail, target_event_id: str) -> BabyShowerDetail:
        return BabyShowerDetail(
            event_id=target_event_id,
            parent1_name=source_detail.parent1_name,
            parent2_name=source_detail.parent2_name,
            baby_name=source_detail.baby_name,
            gender=source_detail.gender,
            due_date=source_detail.due_date,
            registry_url=source_detail.registry_url,
            is_gender_reveal=source_detail.is_gender_reveal,
        )


class WeddingDetailHandler(EventDetailHandler):
    detail_attr = "wedding_detail"

    def create_from_request(self, event_id: str, data: Any) -> WeddingDetail:
        return WeddingDetail(
            event_id=event_id,
            partner1_name=data.partner1_name,
            partner2_name=data.partner2_name,
            wedding_date=data.wedding_date,
            venue_name=data.venue_name,
            registry_url=data.registry_url,
            color_theme=data.color_theme,
            sub_event_template=data.sub_event_template,
        )

    def update_from_request(self, existing: WeddingDetail, data: Any) -> None:
        existing.partner1_name = data.partner1_name
        existing.partner2_name = data.partner2_name
        existing.wedding_date = data.wedding_date
        existing.venue_name = data.venue_name
        existing.registry_url = data.registry_url
        existing.color_theme = data.color_theme

    def serialize(self, detail: WeddingDetail) -> dict:
        return {
            "partner1_name": detail.partner1_name,
            "partner2_name": detail.partner2_name,
            "wedding_date": detail.wedding_date.isoformat() if detail.wedding_date else None,
            "venue_name": detail.venue_name,
            "registry_url": detail.registry_url,
            "color_theme": detail.color_theme,
            "display_couple": detail.display_couple,
        }

    def clone(self, source_detail: WeddingDetail, target_event_id: str) -> WeddingDetail:
        return WeddingDetail(
            event_id=target_event_id,
            partner1_name=source_detail.partner1_name,
            partner2_name=source_detail.partner2_name,
            wedding_date=source_detail.wedding_date,
            venue_name=source_detail.venue_name,
            registry_url=source_detail.registry_url,
            color_theme=source_detail.color_theme,
        )


# --- Registry ---

EVENT_DETAIL_HANDLERS: dict[str, EventDetailHandler] = {
    EventType.HOLIDAY.value: HolidayDetailHandler(),
    EventType.BIRTHDAY.value: BirthdayDetailHandler(),
    EventType.BABY_SHOWER.value: BabyShowerDetailHandler(),
    EventType.WEDDING.value: WeddingDetailHandler(),
}

# All detail attribute names for iteration (e.g., in event_to_dict)
ALL_DETAIL_ATTRS = [h.detail_attr for h in EVENT_DETAIL_HANDLERS.values()]


def get_handler(event_type: str) -> EventDetailHandler | None:
    """Get the detail handler for an event type, or None for 'general'."""
    return EVENT_DETAIL_HANDLERS.get(event_type)


def create_detail_from_request(event_id: str, event_type: str, request: Any) -> Any | None:
    """Create a detail model from request data, if applicable.

    Returns the model instance to add to the session, or None.
    """
    handler = get_handler(event_type)
    if not handler:
        return None
    detail_data = getattr(request, handler.detail_attr, None)
    if not detail_data:
        return None
    return handler.create_from_request(event_id, detail_data)


def update_detail_from_request(event: Any, event_type: str, request: Any, db: Any) -> None:
    """Update or create a detail from request data (upsert pattern)."""
    handler = get_handler(event_type)
    if not handler:
        return
    detail_data = getattr(request, handler.detail_attr, None)
    if detail_data is None:
        return
    existing = getattr(event, handler.detail_attr, None)
    if existing:
        handler.update_from_request(existing, detail_data)
    else:
        db.add(handler.create_from_request(event.id, detail_data))


def serialize_all_details(event: Any) -> dict:
    """Serialize all type-specific details for an event. Returns a dict of detail_attr -> dict|None."""
    result = {}
    for handler in EVENT_DETAIL_HANDLERS.values():
        detail = getattr(event, handler.detail_attr, None)
        result[handler.detail_attr] = handler.serialize(detail) if detail else None
    return result


def clone_detail(source_event: Any, target_event_id: str) -> Any | None:
    """Clone a type-specific detail for recurrence. Returns model instance or None."""
    handler = get_handler(source_event.event_type)
    if not handler:
        return None
    detail = getattr(source_event, handler.detail_attr, None)
    if not detail:
        return None
    return handler.clone(detail, target_event_id)
