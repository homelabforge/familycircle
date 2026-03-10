"""Event template schemas."""

from pydantic import BaseModel, field_validator


class EventTemplateCreate(BaseModel):
    """Schema for creating an event template."""

    name: str
    description: str | None = None
    template_json: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate template name is not empty."""
        v = v.strip()
        if not v:
            msg = "Template name is required"
            raise ValueError(msg)
        return v

    @field_validator("template_json")
    @classmethod
    def validate_json(cls, v: str) -> str:
        """Validate template JSON is not empty."""
        import json

        v = v.strip()
        if not v:
            msg = "Template data is required"
            raise ValueError(msg)
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON: {e}"
            raise ValueError(msg) from e
        return v
