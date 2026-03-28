"""Holiday event schemas."""

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.holiday_detail import PREDEFINED_HOLIDAYS


class HolidayDetailCreate(BaseModel):
    """Create holiday detail data."""

    holiday_name: str
    custom_holiday_name: str | None = None
    year: int | None = None

    @field_validator("holiday_name")
    @classmethod
    def validate_holiday_name(cls, v: str) -> str:
        """Validate holiday name is predefined or 'custom'."""
        if v != "custom" and v not in PREDEFINED_HOLIDAYS:
            msg = f"Unknown holiday: {v}. Use a predefined holiday or 'custom'."
            raise ValueError(msg)
        return v

    @field_validator("custom_holiday_name")
    @classmethod
    def validate_custom_name(cls, v: str | None, info: object) -> str | None:
        """Require custom name when holiday_name is 'custom'."""
        if hasattr(info, "data") and info.data.get("holiday_name") == "custom" and not v:  # type: ignore[union-attr]
            msg = "Custom holiday name is required when holiday_name is 'custom'"
            raise ValueError(msg)
        return v


class HolidayDetailResponse(BaseModel):
    """Holiday detail response."""

    holiday_name: str
    custom_holiday_name: str | None = None
    display_name: str
    year: int | None = None

    model_config = ConfigDict(from_attributes=True)
