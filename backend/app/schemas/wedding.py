"""Wedding event schemas."""

from datetime import date

from pydantic import BaseModel, field_validator

from app.models.wedding_detail import WEDDING_PARTY_ROLES


class WeddingDetailCreate(BaseModel):
    """Create wedding detail data."""

    partner1_name: str
    partner2_name: str
    wedding_date: date | None = None
    venue_name: str | None = None
    registry_url: str | None = None
    color_theme: str | None = None
    sub_event_template: str | None = None


class WeddingDetailResponse(BaseModel):
    """Wedding detail response."""

    partner1_name: str
    partner2_name: str
    wedding_date: date | None = None
    venue_name: str | None = None
    registry_url: str | None = None
    color_theme: str | None = None
    display_couple: str

    class Config:
        from_attributes = True


class WeddingPartyMemberCreate(BaseModel):
    """Create wedding party member."""

    user_id: str | None = None
    name: str
    role: str
    side: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is a known wedding party role."""
        if v not in WEDDING_PARTY_ROLES:
            msg = f"Invalid role: {v}. Allowed: {', '.join(WEDDING_PARTY_ROLES)}"
            raise ValueError(msg)
        return v

    @field_validator("side")
    @classmethod
    def validate_side(cls, v: str | None) -> str | None:
        """Validate side if provided."""
        allowed = ["partner1", "partner2", "shared"]
        if v is not None and v not in allowed:
            msg = f"Invalid side: {v}. Allowed: {', '.join(allowed)}"
            raise ValueError(msg)
        return v


class WeddingPartyMemberResponse(BaseModel):
    """Wedding party member response."""

    id: str
    name: str
    role: str
    display_role: str
    side: str | None = None
    user_id: str | None = None

    class Config:
        from_attributes = True
