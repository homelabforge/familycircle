"""RSVP guest schemas."""

from pydantic import BaseModel, field_validator


class RSVPGuestCreate(BaseModel):
    """Schema for adding a guest to an RSVP."""

    guest_name: str
    dietary_restrictions: str | None = None
    allergies: str | None = None

    @field_validator("guest_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate guest name is not empty."""
        v = v.strip()
        if not v:
            msg = "Guest name is required"
            raise ValueError(msg)
        return v


class RSVPGuestUpdate(BaseModel):
    """Schema for updating a guest."""

    guest_name: str | None = None
    dietary_restrictions: str | None = None
    allergies: str | None = None
