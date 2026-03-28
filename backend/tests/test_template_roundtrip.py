"""Round-trip tests for JSON template storage in TEXT columns.

Verifies that JSON stored in EventTemplate.template_json and
PollTemplate.options_json survives a write-read cycle through SQLite
and that Pydantic schemas enforce structure correctly.
"""

from __future__ import annotations

import json
import os
import uuid

os.environ.setdefault("DATABASE_PATH", "/tmp/test-familycircle.db")

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_template import EventTemplate
from app.models.family import Family
from app.models.poll_template import PollTemplate
from app.schemas.event_template import EventTemplateCreate
from app.schemas.poll_template import PollTemplateCreate, PollTemplateResponse


def _uuid() -> str:
    return str(uuid.uuid4())


@pytest.fixture
async def family(db: AsyncSession) -> Family:
    """Create a minimal family for FK constraints."""
    fam = Family(id=_uuid(), name="Template Test Family", family_code="TMPL01")
    db.add(fam)
    await db.commit()
    return fam


# ---------------------------------------------------------------------------
# EventTemplate round-trip
# ---------------------------------------------------------------------------


class TestEventTemplateRoundTrip:
    """Verify EventTemplate.template_json survives a write-read cycle."""

    async def test_simple_object_roundtrip(self, db: AsyncSession, family: Family) -> None:
        """A flat JSON object stored in template_json deserializes identically."""
        payload = {"title": "Game Night", "duration_hours": 3, "indoor": True}
        tmpl = EventTemplate(
            id=_uuid(),
            family_id=family.id,
            name="Game Night Template",
            template_json=json.dumps(payload),
        )
        db.add(tmpl)
        await db.commit()

        row = await db.get(EventTemplate, tmpl.id)
        assert row is not None
        assert json.loads(row.template_json) == payload

    async def test_nested_object_roundtrip(self, db: AsyncSession, family: Family) -> None:
        """Nested JSON with arrays and sub-objects round-trips correctly."""
        payload = {
            "title": "Potluck Dinner",
            "categories": ["appetizer", "main", "dessert"],
            "location": {"name": "Community Hall", "capacity": 80},
            "recurring": None,
        }
        tmpl = EventTemplate(
            id=_uuid(),
            family_id=family.id,
            name="Potluck Template",
            template_json=json.dumps(payload),
        )
        db.add(tmpl)
        await db.commit()

        result = await db.execute(select(EventTemplate).where(EventTemplate.id == tmpl.id))
        row = result.scalar_one()
        deserialized = json.loads(row.template_json)
        assert deserialized == payload
        assert deserialized["location"]["capacity"] == 80
        assert deserialized["recurring"] is None

    async def test_unicode_and_special_chars(self, db: AsyncSession, family: Family) -> None:
        """Unicode, emoji, and special characters survive the round-trip."""
        payload = {"title": "Fête de Noël 🎄", "note": 'Line1\nLine2\t"quoted"'}
        tmpl = EventTemplate(
            id=_uuid(),
            family_id=family.id,
            name="Holiday Template",
            template_json=json.dumps(payload, ensure_ascii=False),
        )
        db.add(tmpl)
        await db.commit()

        row = await db.get(EventTemplate, tmpl.id)
        assert row is not None
        assert json.loads(row.template_json) == payload


# ---------------------------------------------------------------------------
# PollTemplate round-trip
# ---------------------------------------------------------------------------


class TestPollTemplateRoundTrip:
    """Verify PollTemplate.options_json survives a write-read cycle."""

    async def test_options_roundtrip(self, db: AsyncSession, family: Family) -> None:
        """A list of string options stored as JSON round-trips correctly."""
        options = ["Pizza", "Tacos", "Sushi", "Burgers"]
        tmpl = PollTemplate(
            id=_uuid(),
            family_id=family.id,
            name="Dinner Vote",
            options_json=json.dumps(options),
            allow_multiple=False,
            is_builtin=False,
        )
        db.add(tmpl)
        await db.commit()

        row = await db.get(PollTemplate, tmpl.id)
        assert row is not None
        assert json.loads(row.options_json) == options

    async def test_many_options_roundtrip(self, db: AsyncSession, family: Family) -> None:
        """Ten options (the schema max) round-trip without truncation."""
        options = [f"Option {i}" for i in range(1, 11)]
        tmpl = PollTemplate(
            id=_uuid(),
            family_id=family.id,
            name="Big Poll",
            options_json=json.dumps(options),
            allow_multiple=True,
            is_builtin=False,
        )
        db.add(tmpl)
        await db.commit()

        row = await db.get(PollTemplate, tmpl.id)
        assert row is not None
        recovered = json.loads(row.options_json)
        assert recovered == options
        assert len(recovered) == 10

    async def test_builtin_template_no_family(self, db: AsyncSession) -> None:
        """Built-in templates (family_id=NULL) round-trip correctly."""
        options = ["Yes", "No"]
        tmpl = PollTemplate(
            id=_uuid(),
            family_id=None,
            name="Yes/No",
            options_json=json.dumps(options),
            allow_multiple=False,
            is_builtin=True,
        )
        db.add(tmpl)
        await db.commit()

        row = await db.get(PollTemplate, tmpl.id)
        assert row is not None
        assert row.family_id is None
        assert row.is_builtin is True
        assert json.loads(row.options_json) == options

    async def test_response_schema_deserializes_options(
        self, db: AsyncSession, family: Family
    ) -> None:
        """PollTemplateResponse.from_model correctly parses options_json."""
        options = ["Red", "Blue", "Green"]
        tmpl = PollTemplate(
            id=_uuid(),
            family_id=family.id,
            name="Color Poll",
            options_json=json.dumps(options),
            allow_multiple=False,
            is_builtin=False,
        )
        db.add(tmpl)
        await db.commit()

        row = await db.get(PollTemplate, tmpl.id)
        assert row is not None
        resp = PollTemplateResponse.from_model(row)
        assert resp.options == options
        assert resp.name == "Color Poll"


# ---------------------------------------------------------------------------
# Pydantic schema validation
# ---------------------------------------------------------------------------


class TestEventTemplateCreateValidation:
    """Verify EventTemplateCreate catches bad JSON."""

    def test_valid_json_accepted(self) -> None:
        schema = EventTemplateCreate(
            name="Valid",
            template_json='{"key": "value"}',
        )
        assert schema.template_json == '{"key": "value"}'

    def test_invalid_json_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            EventTemplateCreate(
                name="Bad JSON",
                template_json="{not valid json}",
            )
        errors = exc_info.value.errors()
        assert any("Invalid JSON" in str(e["msg"]) for e in errors)

    def test_empty_json_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            EventTemplateCreate(
                name="Empty",
                template_json="",
            )
        errors = exc_info.value.errors()
        assert any("Template data is required" in str(e["msg"]) for e in errors)

    def test_whitespace_only_json_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            EventTemplateCreate(
                name="Whitespace",
                template_json="   ",
            )
        errors = exc_info.value.errors()
        assert any("Template data is required" in str(e["msg"]) for e in errors)

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EventTemplateCreate(
                name="",
                template_json='{"a": 1}',
            )


class TestPollTemplateCreateValidation:
    """Verify PollTemplateCreate validates option structure."""

    def test_valid_options_accepted(self) -> None:
        schema = PollTemplateCreate(
            name="Valid Poll",
            options=["A", "B"],
        )
        assert schema.options == ["A", "B"]

    def test_fewer_than_two_options_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            PollTemplateCreate(name="One Option", options=["Only one"])
        errors = exc_info.value.errors()
        assert any("At least 2 options" in str(e["msg"]) for e in errors)

    def test_empty_options_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            PollTemplateCreate(name="No Options", options=[])
        errors = exc_info.value.errors()
        assert any("At least 2 options" in str(e["msg"]) for e in errors)

    def test_more_than_ten_options_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            PollTemplateCreate(
                name="Too Many",
                options=[f"Opt {i}" for i in range(11)],
            )
        errors = exc_info.value.errors()
        assert any("Maximum 10 options" in str(e["msg"]) for e in errors)

    def test_whitespace_only_options_stripped(self) -> None:
        """Whitespace-only options are stripped, leaving fewer than 2 real options."""
        with pytest.raises(ValidationError) as exc_info:
            PollTemplateCreate(name="Blanks", options=["  ", "  ", "Real"])
        errors = exc_info.value.errors()
        assert any("At least 2 options" in str(e["msg"]) for e in errors)

    def test_options_are_trimmed(self) -> None:
        schema = PollTemplateCreate(
            name="Trimmed",
            options=["  Alpha  ", "  Beta  "],
        )
        assert schema.options == ["Alpha", "Beta"]

    def test_allow_multiple_defaults_false(self) -> None:
        schema = PollTemplateCreate(name="Default", options=["A", "B"])
        assert schema.allow_multiple is False

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PollTemplateCreate(name="", options=["A", "B"])

    def test_long_name_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            PollTemplateCreate(name="X" * 201, options=["A", "B"])
        errors = exc_info.value.errors()
        assert any("200 characters" in str(e["msg"]) for e in errors)
