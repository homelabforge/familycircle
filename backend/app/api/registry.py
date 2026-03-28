"""Registry API — gift registry items for events (baby showers, weddings, etc.)."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import require_family_context
from app.api.event_helpers import resolve_event_or_404
from app.db import get_db_session
from app.models import Event, FamilyMembership, User
from app.models.registry_item import RegistryItem
from app.schemas.registry_item import RegistryItemCreate, RegistryItemUpdate
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


def _item_to_dict(item: RegistryItem, claimed_by_name: str | None = None) -> dict:
    """Convert a registry item to a response dict."""
    return {
        "id": str(item.id),
        "event_id": str(item.event_id),
        "item_name": item.item_name,
        "item_url": item.item_url,
        "price": float(item.price) if item.price is not None else None,
        "image_url": item.image_url,
        "quantity": item.quantity,
        "claimed_by_id": str(item.claimed_by_id) if item.claimed_by_id else None,
        "claimed_by_name": claimed_by_name,
        "is_claimed": item.is_claimed,
        "is_purchased": item.is_purchased,
        "purchased_at": item.purchased_at.isoformat() if item.purchased_at else None,
        "notes": item.notes,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("/{event_id}/registry")
async def list_registry_items(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List registry items for an event."""
    event = await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(RegistryItem)
        .where(RegistryItem.event_id == event_id)
        .order_by(RegistryItem.created_at.asc())
    )
    items = list(result.scalars().all())

    # Build name cache for claimed_by
    user_ids = {i.claimed_by_id for i in items if i.claimed_by_id}
    name_cache: dict[str, str] = {}
    for uid in user_ids:
        name_cache[uid] = await _get_display_name(db, uid, event.family_id)

    return {
        "items": [_item_to_dict(i, name_cache.get(i.claimed_by_id or "")) for i in items],
        "stats": {
            "total": len(items),
            "claimed": len([i for i in items if i.is_claimed]),
            "purchased": len([i for i in items if i.is_purchased]),
        },
    }


@router.post("/{event_id}/registry", status_code=201)
async def create_registry_item(
    event_id: str,
    data: RegistryItemCreate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Add a registry item. Requires event creator or family admin."""
    event = await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    is_admin = await permissions.is_family_admin(db, user, event.family_id)
    is_creator = event.created_by_id == user.id
    if not is_admin and not is_creator:
        raise HTTPException(
            status_code=403,
            detail="Only the event creator or a family admin can add registry items",
        )

    item = RegistryItem(
        event_id=event_id,
        item_name=data.item_name,
        item_url=data.item_url,
        price=data.price,
        image_url=data.image_url,
        quantity=data.quantity,
        notes=data.notes,
    )
    db.add(item)
    await db.flush()

    return _item_to_dict(item)


@router.put("/{event_id}/registry/{item_id}")
async def update_registry_item(
    event_id: str,
    item_id: str,
    data: RegistryItemUpdate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Update a registry item. Requires event creator or family admin."""
    event = await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(RegistryItem).where(
            RegistryItem.id == item_id,
            RegistryItem.event_id == event_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Registry item not found")

    is_admin = await permissions.is_family_admin(db, user, event.family_id)
    is_creator = event.created_by_id == user.id
    if not is_admin and not is_creator:
        raise HTTPException(
            status_code=403,
            detail="Only the event creator or a family admin can edit registry items",
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    await db.flush()

    claimed_name = None
    if item.claimed_by_id:
        claimed_name = await _get_display_name(db, item.claimed_by_id, event.family_id)
    return _item_to_dict(item, claimed_name)


@router.post("/{event_id}/registry/{item_id}/claim")
async def claim_registry_item(
    event_id: str,
    item_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Claim (reserve) a registry item."""
    event = await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(RegistryItem).where(
            RegistryItem.id == item_id,
            RegistryItem.event_id == event_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Registry item not found")

    if item.claimed_by_id:
        raise HTTPException(status_code=400, detail="This item has already been claimed")

    item.claimed_by_id = user.id
    await db.flush()

    claimed_name = await _get_display_name(db, user.id, event.family_id)
    return _item_to_dict(item, claimed_name)


@router.delete("/{event_id}/registry/{item_id}/claim")
async def unclaim_registry_item(
    event_id: str,
    item_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Unclaim (release) a registry item. Only the claimer can unclaim."""
    await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(RegistryItem).where(
            RegistryItem.id == item_id,
            RegistryItem.event_id == event_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Registry item not found")

    if item.claimed_by_id != user.id:
        raise HTTPException(status_code=403, detail="You can only unclaim items you claimed")

    item.claimed_by_id = None
    item.purchased_at = None
    await db.flush()

    return _item_to_dict(item)


@router.post("/{event_id}/registry/{item_id}/purchase")
async def mark_purchased(
    event_id: str,
    item_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Mark a claimed registry item as purchased. Only the claimer can mark."""
    await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(RegistryItem).where(
            RegistryItem.id == item_id,
            RegistryItem.event_id == event_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Registry item not found")

    if item.claimed_by_id != user.id:
        raise HTTPException(
            status_code=403, detail="You can only mark items you claimed as purchased"
        )

    item.purchased_at = datetime.now(UTC)
    await db.flush()

    claimed_name = await _get_display_name(db, user.id, user.current_family_id or "")
    return _item_to_dict(item, claimed_name)


@router.delete("/{event_id}/registry/{item_id}", status_code=204)
async def delete_registry_item(
    event_id: str,
    item_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a registry item. Requires event creator or family admin."""
    event = await resolve_event_or_404(
        db,
        event_id,
        user,
        options=[selectinload(Event.birthday_detail)],
    )

    result = await db.execute(
        select(RegistryItem).where(
            RegistryItem.id == item_id,
            RegistryItem.event_id == event_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Registry item not found")

    is_admin = await permissions.is_family_admin(db, user, event.family_id)
    is_creator = event.created_by_id == user.id
    if not is_admin and not is_creator:
        raise HTTPException(
            status_code=403,
            detail="Only the event creator or a family admin can delete registry items",
        )

    await db.delete(item)
