"""Potluck contributions API endpoints - multi-family aware."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.models import Event, PotluckItem, User, FamilyMembership
from app.api.auth import get_current_user, require_family_context
from app.services.permissions import permissions

router = APIRouter()


class PotluckItemCreate(BaseModel):
    """Create potluck item request."""

    name: str
    category: Optional[str] = None  # appetizer, main, side, dessert, drink, other
    description: Optional[str] = None
    serves: Optional[int] = None
    dietary_info: Optional[str] = None  # e.g., "vegetarian, gluten-free"
    allergens: Optional[str] = None  # e.g., "nuts, dairy"


class PotluckItemUpdate(BaseModel):
    """Update potluck item request."""

    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    serves: Optional[int] = None
    dietary_info: Optional[str] = None
    allergens: Optional[str] = None


def item_to_dict(item: PotluckItem, claimer_name: Optional[str] = None) -> dict:
    """Convert potluck item to response dict."""
    return {
        "id": str(item.id),
        "name": item.name,
        "category": item.category,
        "description": item.description,
        "serves": item.serves,
        "dietary_info": item.dietary_info,
        "allergens": item.allergens,
        "claimed_by_id": str(item.claimed_by_id) if item.claimed_by_id else None,
        "claimed_by_name": claimer_name,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


async def get_claimer_display_name(
    db: AsyncSession, user_id: str, family_id: str
) -> Optional[str]:
    """Get the display name for a user in a family context."""
    result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == family_id,
        )
    )
    membership = result.scalar_one_or_none()
    return membership.display_name if membership else None


@router.get("/{event_id}")
async def get_potluck(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get potluck info for an event."""
    result = await db.execute(
        select(Event).where(
            Event.id == event_id,
            Event.family_id == user.current_family_id,
        )
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found. It may have been deleted.")

    if not event.has_potluck:
        raise HTTPException(status_code=400, detail="This event does not have a potluck")

    # Get items with claimer names
    items = []
    for item in event.potluck_items:
        claimer_name = None
        if item.claimed_by_id:
            claimer_name = await get_claimer_display_name(
                db, item.claimed_by_id, user.current_family_id
            )
        items.append(item_to_dict(item, claimer_name))

    # Group by category
    categories = {}
    for item in items:
        cat = item["category"] or "other"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    return {
        "event_id": event_id,
        "event_title": event.title,
        "items": items,
        "categories": categories,
        "stats": {
            "total": len(items),
            "claimed": len([i for i in items if i["claimed_by_id"]]),
            "unclaimed": len([i for i in items if not i["claimed_by_id"]]),
        },
    }


@router.get("/{event_id}/items")
async def list_items(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List all potluck items for an event."""
    # Verify event belongs to current family
    event_result = await db.execute(
        select(Event).where(
            Event.id == event_id,
            Event.family_id == user.current_family_id,
        )
    )
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    result = await db.execute(
        select(PotluckItem).where(PotluckItem.event_id == event_id)
    )
    items = result.scalars().all()

    # Get claimer names
    response_items = []
    for item in items:
        claimer_name = None
        if item.claimed_by_id:
            claimer_name = await get_claimer_display_name(
                db, item.claimed_by_id, user.current_family_id
            )
        response_items.append(item_to_dict(item, claimer_name))

    return {"items": response_items}


@router.post("/{event_id}/items")
async def add_item(
    event_id: str,
    request: PotluckItemCreate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Add a potluck item (family admin or event creator only)."""
    # Super admin can access any event, others only their current family
    if user.is_super_admin:
        result = await db.execute(select(Event).where(Event.id == event_id))
    else:
        result = await db.execute(
            select(Event).where(
                Event.id == event_id,
                Event.family_id == user.current_family_id,
            )
        )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found. It may have been deleted.")

    # Check if user can manage this event
    can_manage = await permissions.can_manage_event(db, user, event)
    if not can_manage:
        raise HTTPException(
            status_code=403,
            detail="Only family admins or event creators can add potluck items",
        )

    item = PotluckItem(
        event_id=event_id,
        name=request.name,
        category=request.category,
        description=request.description,
        serves=request.serves,
        dietary_info=request.dietary_info,
        allergens=request.allergens,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return {"message": "Item added", "id": str(item.id)}


@router.put("/{event_id}/items/{item_id}")
async def update_item(
    event_id: str,
    item_id: str,
    request: PotluckItemUpdate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Update a potluck item (family admin or event creator only)."""
    # Super admin can access any event, others only their current family
    if user.is_super_admin:
        event_result = await db.execute(select(Event).where(Event.id == event_id))
    else:
        event_result = await db.execute(
            select(Event).where(
                Event.id == event_id,
                Event.family_id == user.current_family_id,
            )
        )
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    can_manage = await permissions.can_manage_event(db, user, event)
    if not can_manage:
        raise HTTPException(
            status_code=403,
            detail="Only family admins or event creators can edit potluck items",
        )

    result = await db.execute(
        select(PotluckItem).where(
            PotluckItem.id == item_id,
            PotluckItem.event_id == event_id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Potluck item not found. It may have been deleted.")

    if request.name is not None:
        item.name = request.name
    if request.category is not None:
        item.category = request.category
    if request.description is not None:
        item.description = request.description
    if request.serves is not None:
        item.serves = request.serves
    if request.dietary_info is not None:
        item.dietary_info = request.dietary_info
    if request.allergens is not None:
        item.allergens = request.allergens

    await db.commit()

    return {"message": "Item updated"}


@router.delete("/{event_id}/items/{item_id}")
async def delete_item(
    event_id: str,
    item_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a potluck item (family admin or event creator only)."""
    # Super admin can access any event, others only their current family
    if user.is_super_admin:
        event_result = await db.execute(select(Event).where(Event.id == event_id))
    else:
        event_result = await db.execute(
            select(Event).where(
                Event.id == event_id,
                Event.family_id == user.current_family_id,
            )
        )
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    can_manage = await permissions.can_manage_event(db, user, event)
    if not can_manage:
        raise HTTPException(
            status_code=403,
            detail="Only family admins or event creators can delete potluck items",
        )

    result = await db.execute(
        select(PotluckItem).where(
            PotluckItem.id == item_id,
            PotluckItem.event_id == event_id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Potluck item not found. It may have been deleted.")

    await db.delete(item)
    await db.commit()

    return {"message": "Item deleted"}


@router.post("/{event_id}/claim/{item_id}")
async def claim_item(
    event_id: str,
    item_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Claim a potluck item."""
    # Verify event belongs to current family
    event_result = await db.execute(
        select(Event).where(
            Event.id == event_id,
            Event.family_id == user.current_family_id,
        )
    )
    if not event_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")

    result = await db.execute(
        select(PotluckItem).where(
            PotluckItem.id == item_id,
            PotluckItem.event_id == event_id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Potluck item not found. It may have been deleted.")

    if item.claimed_by_id and str(item.claimed_by_id) != str(user.id):
        raise HTTPException(status_code=400, detail="This item has already been claimed by someone else")

    item.claimed_by_id = str(user.id)
    await db.commit()

    return {"message": f"You're bringing {item.name}!"}


@router.delete("/{event_id}/claim/{item_id}")
async def unclaim_item(
    event_id: str,
    item_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Unclaim a potluck item."""
    # Verify event belongs to current family
    event_result = await db.execute(
        select(Event).where(
            Event.id == event_id,
            Event.family_id == user.current_family_id,
        )
    )
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    result = await db.execute(
        select(PotluckItem).where(
            PotluckItem.id == item_id,
            PotluckItem.event_id == event_id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Potluck item not found. It may have been deleted.")

    # Can only unclaim your own items (or admin/event creator can unclaim any)
    is_own_claim = item.claimed_by_id and str(item.claimed_by_id) == str(user.id)
    can_manage = await permissions.can_manage_event(db, user, event)

    if not is_own_claim and not can_manage:
        raise HTTPException(status_code=403, detail="You can only unclaim items you've claimed yourself")

    item.claimed_by_id = None
    await db.commit()

    return {"message": "Item unclaimed"}


@router.get("/{event_id}/my-items")
async def get_my_items(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get items claimed by current user."""
    # Verify event belongs to current family
    event_result = await db.execute(
        select(Event).where(
            Event.id == event_id,
            Event.family_id == user.current_family_id,
        )
    )
    if not event_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")

    result = await db.execute(
        select(PotluckItem).where(
            PotluckItem.event_id == event_id,
            PotluckItem.claimed_by_id == user.id,
        )
    )
    items = result.scalars().all()

    # Get user's display name in this family
    display_name = await get_claimer_display_name(db, str(user.id), user.current_family_id)

    return {
        "items": [item_to_dict(item, display_name) for item in items]
    }
