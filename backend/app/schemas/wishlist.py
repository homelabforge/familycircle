"""Wishlist schemas — re-exports from api/wishlist.py inline definitions.

The canonical schemas are defined inline in api/wishlist.py.
This module exists only for backwards compatibility with schemas/__init__.py
and schemas/gift_exchange.py which import from here.
"""

from datetime import datetime

from pydantic import BaseModel


class WishlistItemCreate(BaseModel):
    """Create wishlist item request."""

    name: str
    description: str | None = None
    url: str | None = None
    price_range: str | None = None
    priority: int | None = 1


class WishlistItemUpdate(BaseModel):
    """Update wishlist item request."""

    name: str | None = None
    description: str | None = None
    url: str | None = None
    price_range: str | None = None
    priority: int | None = None


class WishlistItemResponse(BaseModel):
    """Wishlist item response."""

    id: str
    name: str
    description: str | None = None
    url: str | None = None
    price_range: str | None = None
    priority: int | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True
