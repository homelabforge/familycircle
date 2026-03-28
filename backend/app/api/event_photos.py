"""Event photo gallery API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import require_family_context
from app.api.event_helpers import resolve_event_or_404
from app.db import get_db_session
from app.models import Event, FamilyMembership, User
from app.models.event_photo import EventPhoto
from app.schemas.event_photo import EventPhotoReorder
from app.services.file_storage import (
    FileStorageError,
    delete_file,
    get_upload_url,
    save_upload,
)
from app.services.permissions import permissions

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_PHOTOS_PER_EVENT = 50


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


def _photo_to_response(photo: EventPhoto, uploader_name: str) -> dict:
    """Convert a photo model to a response dict."""
    return {
        "id": str(photo.id),
        "event_id": str(photo.event_id),
        "uploaded_by_id": str(photo.uploaded_by_id) if photo.uploaded_by_id else None,
        "uploaded_by_name": uploader_name,
        "filename": photo.filename,
        "url": get_upload_url(photo.file_path),
        "file_size": photo.file_size,
        "mime_type": photo.mime_type,
        "caption": photo.caption,
        "display_order": photo.display_order,
        "created_at": photo.created_at.isoformat() if photo.created_at else None,
    }


@router.get("/{event_id}/photos")
async def list_photos(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """List photos for an event, ordered by display_order."""
    event = await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(EventPhoto)
        .where(EventPhoto.event_id == event_id)
        .order_by(EventPhoto.display_order.asc(), EventPhoto.created_at.asc())
    )
    photos = result.scalars().all()

    # Build name cache
    user_ids = {p.uploaded_by_id for p in photos if p.uploaded_by_id}
    name_cache: dict[str, str] = {}
    for uid in user_ids:
        name_cache[uid] = await _get_display_name(db, uid, event.family_id)

    return {
        "photos": [
            _photo_to_response(p, name_cache.get(p.uploaded_by_id or "", "Unknown")) for p in photos
        ]
    }


@router.post("/{event_id}/photos", status_code=201)
async def upload_photo(
    event_id: str,
    file: UploadFile,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Upload a photo to an event."""
    event = await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    if event.is_cancelled:
        raise HTTPException(status_code=400, detail="Cannot upload photos to a cancelled event")

    # Check photo limit
    result = await db.execute(select(EventPhoto).where(EventPhoto.event_id == event_id))
    existing_count = len(result.scalars().all())
    if existing_count >= MAX_PHOTOS_PER_EVENT:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_PHOTOS_PER_EVENT} photos per event",
        )

    try:
        filename, file_path, file_size, mime_type = await save_upload(
            file, event.family_id, event_id
        )
    except FileStorageError as e:
        raise HTTPException(status_code=400, detail=str(e))

    photo = EventPhoto(
        event_id=event_id,
        family_id=event.family_id,
        uploaded_by_id=user.id,
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        display_order=existing_count,
    )
    db.add(photo)
    await db.flush()

    user_name = await _get_display_name(db, user.id, event.family_id)
    return _photo_to_response(photo, user_name)


@router.delete("/{event_id}/photos/{photo_id}", status_code=204)
async def delete_photo(
    event_id: str,
    photo_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a photo. Uploader or admin can delete."""
    event = await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(EventPhoto).where(
            EventPhoto.id == photo_id,
            EventPhoto.event_id == event_id,
        )
    )
    photo = result.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Owner or admin can delete
    is_admin = await permissions.is_family_admin(db, user, event.family_id)
    if photo.uploaded_by_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="You can only delete your own photos")

    # Delete file from disk
    delete_file(photo.file_path)

    await db.delete(photo)


@router.put("/{event_id}/photos/reorder")
async def reorder_photos(
    event_id: str,
    data: EventPhotoReorder,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Reorder photos for an event. Event creator or admin only."""
    event = await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    is_admin = await permissions.is_family_admin(db, user, event.family_id)
    if event.created_by_id != user.id and not is_admin:
        raise HTTPException(
            status_code=403, detail="Only event creator or admin can reorder photos"
        )

    result = await db.execute(select(EventPhoto).where(EventPhoto.event_id == event_id))
    photos = {str(p.id): p for p in result.scalars().all()}

    # Validate all photo IDs belong to this event
    for pid in data.photo_ids:
        if pid not in photos:
            raise HTTPException(status_code=400, detail=f"Photo {pid} not found in this event")

    # Apply new order
    for i, pid in enumerate(data.photo_ids):
        photos[pid].display_order = i

    await db.flush()
    return {"message": "Photos reordered"}
