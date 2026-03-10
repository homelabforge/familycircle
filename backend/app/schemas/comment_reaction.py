"""Comment reaction Pydantic schemas."""

from pydantic import BaseModel, field_validator

from app.models.comment_reaction import ALLOWED_EMOJIS


class CommentReactionToggle(BaseModel):
    """Toggle a reaction on a comment."""

    emoji: str

    @field_validator("emoji")
    @classmethod
    def validate_emoji(cls, v: str) -> str:
        """Validate emoji is in the allowed set."""
        if v not in ALLOWED_EMOJIS:
            allowed = ", ".join(sorted(ALLOWED_EMOJIS))
            raise ValueError(f"Emoji must be one of: {allowed}")
        return v
