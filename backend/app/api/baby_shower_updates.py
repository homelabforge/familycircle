"""Baby shower updates API — timeline of updates for baby shower events."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_family_context
from app.api.event_helpers import resolve_event_or_404
from app.db import get_db_session
from app.models import FamilyMembership, User
from app.models.baby_shower_update import BabyShowerUpdate
from app.schemas.baby_shower_update import BabyShowerUpdateCreate
from app.services.notifications.dispatcher import NotificationDispatcher
from app.services.permissions import permissions

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_display_name(db: AsyncSession, user_id: str, family_id: str) -> str:
    """Get user's display name in a family."""
    result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == family_id,
        )
    )
    membership = result.scalar_one_or_none()
    return membership.display_name if membership else "Unknown"


def _update_to_dict(update: BabyShowerUpdate, poster_name: str) -> dict:
    """Convert a baby shower update to a response dict."""
    return {
        "id": str(update.id),
        "event_id": str(update.event_id),
        "update_type": update.update_type,
        "update_date": update.update_date.isoformat() if update.update_date else None,
        "title": update.title,
        "notes": update.notes,
        "photo_id": str(update.photo_id) if update.photo_id else None,
        "photo_url": f"/uploads/{update.photo.file_path}" if update.photo else None,
        "posted_by_id": str(update.posted_by_id) if update.posted_by_id else None,
        "posted_by_name": poster_name,
        "created_at": update.created_at.isoformat() if update.created_at else None,
    }


@router.get("/{event_id}/baby-shower-updates")
async def list_updates(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List baby shower updates for an event, chronologically."""
    event = await resolve_event_or_404(db, event_id, user)

    if event.event_type != "baby_shower":
        raise HTTPException(status_code=400, detail="This event is not a baby shower")

    result = await db.execute(
        select(BabyShowerUpdate)
        .where(BabyShowerUpdate.event_id == event_id)
        .order_by(BabyShowerUpdate.update_date.asc(), BabyShowerUpdate.created_at.asc())
    )
    updates = list(result.scalars().all())

    # Build name cache
    user_ids = {u.posted_by_id for u in updates if u.posted_by_id}
    name_cache: dict[str, str] = {}
    for uid in user_ids:
        name_cache[uid] = await _get_display_name(db, uid, event.family_id)

    return {
        "updates": [
            _update_to_dict(u, name_cache.get(u.posted_by_id or "", "Unknown")) for u in updates
        ]
    }


@router.post("/{event_id}/baby-shower-updates", status_code=201)
async def create_update(
    event_id: str,
    data: BabyShowerUpdateCreate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Add a baby shower update. Requires event creator or family admin."""
    event = await resolve_event_or_404(db, event_id, user)

    if event.event_type != "baby_shower":
        raise HTTPException(status_code=400, detail="This event is not a baby shower")

    is_admin = await permissions.is_family_admin(db, user, event.family_id)
    is_creator = event.created_by_id == user.id
    if not is_admin and not is_creator:
        raise HTTPException(
            status_code=403,
            detail="Only the event creator or a family admin can post updates",
        )

    update = BabyShowerUpdate(
        event_id=event_id,
        update_type=data.update_type,
        update_date=data.update_date,
        title=data.title,
        notes=data.notes,
        photo_id=data.photo_id,
        posted_by_id=user.id,
    )
    db.add(update)
    await db.flush()
    await db.refresh(update, ["photo"])

    poster_name = await _get_display_name(db, user.id, event.family_id)

    # Fire notification for major updates
    if data.update_type in ("baby_born", "name_announced", "gender_revealed"):
        try:
            dispatcher = NotificationDispatcher(db)
            await dispatcher.notify_event_updated(
                event_title=event.title,
                updater_name=poster_name,
            )
        except Exception as e:
            logger.error("Failed to send baby shower update notification: %s", e)

    return _update_to_dict(update, poster_name)


@router.delete("/{event_id}/baby-shower-updates/{update_id}", status_code=204)
async def delete_update(
    event_id: str,
    update_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a baby shower update. Requires event creator or family admin."""
    event = await resolve_event_or_404(db, event_id, user)

    result = await db.execute(
        select(BabyShowerUpdate).where(
            BabyShowerUpdate.id == update_id,
            BabyShowerUpdate.event_id == event_id,
        )
    )
    update = result.scalar_one_or_none()
    if not update:
        raise HTTPException(status_code=404, detail="Update not found")

    is_admin = await permissions.is_family_admin(db, user, event.family_id)
    is_creator = event.created_by_id == user.id
    if not is_admin and not is_creator:
        raise HTTPException(
            status_code=403,
            detail="Only the event creator or a family admin can delete updates",
        )

    await db.delete(update)
