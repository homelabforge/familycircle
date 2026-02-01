"""Wishlist schemas."""

from datetime import datetime

from pydantic import BaseModel


class WishlistItemCreate(BaseModel):
    """Create wishlist item."""

    name: str
    link: str | None = None
    notes: str | None = None


class WishlistItemUpdate(BaseModel):
    """Update wishlist item."""

    name: str | None = None
    link: str | None = None
    notes: str | None = None


class WishlistItemResponse(BaseModel):
    """Wishlist item response."""

    id: str
    name: str
    link: str | None
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True
