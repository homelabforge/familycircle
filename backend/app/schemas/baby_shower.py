"""Baby shower event schemas."""

from datetime import date

from pydantic import BaseModel, field_validator

from app.models.baby_shower_detail import ALLOWED_GENDERS


class BabyShowerDetailCreate(BaseModel):
    """Create baby shower detail data."""

    parent1_name: str
    parent2_name: str | None = None
    baby_name: str | None = None
    gender: str | None = None
    due_date: date | None = None
    registry_url: str | None = None
    is_gender_reveal: bool = False

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str | None) -> str | None:
        """Validate gender is an allowed value."""
        if v is not None and v not in ALLOWED_GENDERS:
            msg = f"Invalid gender: {v}. Allowed: {', '.join(ALLOWED_GENDERS)}"
            raise ValueError(msg)
        return v


class BabyShowerDetailResponse(BaseModel):
    """Baby shower detail response."""

    parent1_name: str
    parent2_name: str | None = None
    baby_name: str | None = None
    gender: str | None = None
    due_date: date | None = None
    registry_url: str | None = None
    is_gender_reveal: bool
    display_parents: str

    class Config:
        from_attributes = True
