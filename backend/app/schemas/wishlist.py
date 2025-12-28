"""Wishlist schemas."""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class WishlistItemCreate(BaseModel):
    """Create wishlist item."""

    name: str
    link: Optional[str] = None
    notes: Optional[str] = None


class WishlistItemUpdate(BaseModel):
    """Update wishlist item."""

    name: Optional[str] = None
    link: Optional[str] = None
    notes: Optional[str] = None


class WishlistItemResponse(BaseModel):
    """Wishlist item response."""

    id: str
    name: str
    link: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
