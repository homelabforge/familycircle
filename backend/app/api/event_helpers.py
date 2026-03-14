"""Centralized event access helpers — shared by events, comments, and polls routers."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, User
from app.models.event import EventType


def is_secret_birthday_for_user(event: Event, user_id: str, is_super_admin: bool = False) -> bool:
    """Check if this event is a secret birthday hidden from the given user.

    Returns True if the event should be HIDDEN from this user.
    Super admins bypass the filter.
    """
    if is_super_admin:
        return False
    if event.event_type != EventType.BIRTHDAY.value:
        return False
    if not event.birthday_detail:
        return False
    if not event.birthday_detail.is_secret:
        return False
    return event.birthday_detail.birthday_person_id == user_id


async def resolve_event_or_404(
    db: AsyncSession,
    event_id: str,
    user: User,
    options: list[Any] | None = None,
) -> Event:
    """Load event, enforce strict tenant boundary + secret birthday visibility.

    Returns 404 for all denial paths to avoid leaking resource existence:
    - Event does not exist
    - Event's family doesn't match user's current family context (strict tenant boundary)
    - Event is a secret birthday hidden from this user

    Args:
        options: SQLAlchemy loader options (e.g., selectinload) to apply to the query.

    All callers must use require_family_context to guarantee current_family_id is set.
    """
    stmt = select(Event).where(Event.id == event_id)
    if options:
        stmt = stmt.options(*options)
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Strict tenant boundary: event must belong to user's current family context
    if not user.is_super_admin:
        if event.family_id != user.current_family_id:
            raise HTTPException(status_code=404, detail="Event not found")

    # Secret birthday: 404 to conceal existence from birthday person
    if is_secret_birthday_for_user(event, str(user.id), user.is_super_admin):
        raise HTTPException(status_code=404, detail="Event not found")

    return event


def validate_event_type_and_details(request) -> None:
    """Validate event_type is a valid enum value and required details are provided.

    Used by both create_event and create_sub_event.
    """
    from app.services.event_detail_registry import get_handler

    try:
        EventType(request.event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {request.event_type}")

    handler = get_handler(request.event_type)
    if handler and not getattr(request, handler.detail_attr, None):
        # Map detail_attr to human-readable label, e.g., "holiday_detail" -> "Holiday"
        # Use capitalize() on first word only to match existing error messages
        # ("Baby shower detail", not "Baby Shower Detail")
        label = handler.detail_attr.replace("_detail", "").replace("_", " ").capitalize()
        raise HTTPException(
            status_code=400, detail=f"{label} detail required for {request.event_type} events"
        )
