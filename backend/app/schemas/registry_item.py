"""Registry item schemas."""

from pydantic import BaseModel, field_validator


class RegistryItemCreate(BaseModel):
    """Schema for creating a registry item."""

    item_name: str
    item_url: str | None = None
    price: float | None = None
    image_url: str | None = None
    quantity: int = 1
    notes: str | None = None

    @field_validator("item_name")
    @classmethod
    def validate_item_name(cls, v: str) -> str:
        """Validate item name is not empty."""
        v = v.strip()
        if not v:
            msg = "Item name is required"
            raise ValueError(msg)
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is positive."""
        if v < 1:
            msg = "Quantity must be at least 1"
            raise ValueError(msg)
        return v


class RegistryItemUpdate(BaseModel):
    """Schema for updating a registry item."""

    item_name: str | None = None
    item_url: str | None = None
    price: float | None = None
    image_url: str | None = None
    quantity: int | None = None
    notes: str | None = None
