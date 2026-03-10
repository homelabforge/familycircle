"""Wishlist API endpoints - multi-family aware."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, require_family_context
from app.db import get_db_session
from app.models import FamilyMembership, User, WishlistItem
from app.models.gift_exchange import GiftExchangeAssignment
from app.services.permissions import permissions

router = APIRouter()


class WishlistItemCreate(BaseModel):
    """Create wishlist item request."""

    name: str
    description: str | None = None
    url: str | None = None
    price_range: str | None = None  # $, $$, $$$
    priority: int | None = 1  # 1-5, 1 = most wanted


class WishlistItemUpdate(BaseModel):
    """Update wishlist item request."""

    name: str | None = None
    description: str | None = None
    url: str | None = None
    price_range: str | None = None
    priority: int | None = None


def item_to_dict(item: WishlistItem) -> dict:
    """Convert wishlist item to response dict."""
    return {
        "id": str(item.id),
        "name": item.name,
        "description": item.description,
        "url": item.url,
        "price_range": item.price_range,
        "priority": item.priority,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("")
async def get_wishlist(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get current user's wishlist."""
    result = await db.execute(
        select(WishlistItem)
        .where(WishlistItem.user_id == user.id)
        .order_by(WishlistItem.priority.asc(), WishlistItem.created_at.desc())
    )
    items = result.scalars().all()

    return {"items": [item_to_dict(item) for item in items]}


@router.post("")
async def add_wishlist_item(
    request: WishlistItemCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Add an item to wishlist."""
    item = WishlistItem(
        user_id=str(user.id),
        name=request.name,
        description=request.description,
        url=request.url,
        price_range=request.price_range,
        priority=request.priority or 1,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return {"message": "Item added", "id": str(item.id), "item": item_to_dict(item)}


@router.put("/{item_id}")
async def update_wishlist_item(
    item_id: str,
    request: WishlistItemUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update a wishlist item."""
    result = await db.execute(
        select(WishlistItem).where(
            WishlistItem.id == item_id,
            WishlistItem.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=404, detail="Wishlist item not found. It may have been deleted."
        )

    if request.name is not None:
        item.name = request.name
    if request.description is not None:
        item.description = request.description
    if request.url is not None:
        item.url = request.url
    if request.price_range is not None:
        item.price_range = request.price_range
    if request.priority is not None:
        item.priority = request.priority

    await db.commit()

    return {"message": "Item updated", "item": item_to_dict(item)}


@router.delete("/{item_id}")
async def delete_wishlist_item(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a wishlist item."""
    result = await db.execute(
        select(WishlistItem).where(
            WishlistItem.id == item_id,
            WishlistItem.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=404, detail="Wishlist item not found. It may have been deleted."
        )

    await db.delete(item)
    await db.commit()

    return {"message": "Item deleted"}


@router.get("/user/{user_id}")
async def get_user_wishlist(
    user_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get another user's wishlist.

    Only allowed if:
    1. You're viewing your own wishlist
    2. You're a family admin
    3. You're assigned to give a gift to this user (Gift Exchange)
    4. Target user is in the same family
    """
    # Check if viewing own wishlist
    if str(user.id) == user_id:
        result = await db.execute(
            select(WishlistItem)
            .where(WishlistItem.user_id == user_id)
            .order_by(WishlistItem.priority.asc())
        )
        items = result.scalars().all()
        return {"user_id": user_id, "items": [item_to_dict(item) for item in items]}

    # Check if target user is in the same family
    target_membership_result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == user.current_family_id,
        )
    )
    target_membership = target_membership_result.scalar_one_or_none()

    if not target_membership:
        raise HTTPException(
            status_code=403,
            detail="This user is not in your current family",
        )

    # Check if family admin
    is_admin = await permissions.is_family_admin(db, user, user.current_family_id)
    if is_admin:
        result = await db.execute(
            select(WishlistItem)
            .where(WishlistItem.user_id == user_id)
            .order_by(WishlistItem.priority.asc())
        )
        items = result.scalars().all()

        return {
            "user_id": user_id,
            "display_name": target_membership.display_name,
            "items": [item_to_dict(item) for item in items],
        }

    # Check if assigned to this user in any Gift Exchange
    assignment_result = await db.execute(
        select(GiftExchangeAssignment).where(
            GiftExchangeAssignment.giver_id == user.id,
            GiftExchangeAssignment.receiver_id == user_id,
        )
    )
    assignment = assignment_result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=403,
            detail="You can only view another member's wishlist if they're your Gift Exchange assignment",
        )

    # Get wishlist for assigned user
    result = await db.execute(
        select(WishlistItem)
        .where(WishlistItem.user_id == user_id)
        .order_by(WishlistItem.priority.asc())
    )
    items = result.scalars().all()

    return {
        "user_id": user_id,
        "display_name": target_membership.display_name,
        "items": [item_to_dict(item) for item in items],
    }


# Backwards compatibility alias
@router.get("/member/{member_id}")
async def get_member_wishlist(
    member_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Backwards compatible alias for get_user_wishlist."""
    return await get_user_wishlist(member_id, user, db)
