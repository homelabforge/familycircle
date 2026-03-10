"""Birthday event schemas."""

from datetime import date

from pydantic import BaseModel


class BirthdayDetailCreate(BaseModel):
    """Create birthday detail data."""

    birthday_person_id: str | None = None
    birthday_person_name: str
    birth_date: date | None = None
    age_turning: int | None = None
    is_secret: bool = False
    theme: str | None = None


class BirthdayDetailResponse(BaseModel):
    """Birthday detail response."""

    birthday_person_id: str | None = None
    birthday_person_name: str
    birth_date: date | None = None
    age_turning: int | None = None
    is_secret: bool
    theme: str | None = None

    class Config:
        from_attributes = True
