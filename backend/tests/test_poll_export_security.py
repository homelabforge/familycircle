"""Regression tests for CSV formula-injection neutralization in poll export (F9)."""

from __future__ import annotations

import csv
import io
import uuid

import pytest

from app.models.poll import Poll, PollOption
from app.services.poll_export import _neutralize_csv, generate_poll_csv


def _uuid() -> str:
    return str(uuid.uuid4())


class TestNeutralizeHelper:
    @pytest.mark.parametrize(
        "payload",
        ["=HYPERLINK(1)", "+SUM(1,1)", "-2+3", "@SUM(1,1)", "\tTAB", "\rCR"],
    )
    def test_formula_prefixes_get_quoted(self, payload: str):
        assert _neutralize_csv(payload) == "'" + payload

    def test_plain_text_unchanged(self):
        assert _neutralize_csv("Movie night?") == "Movie night?"

    def test_non_string_unchanged(self):
        assert _neutralize_csv(5) == 5
        assert _neutralize_csv(None) is None


class TestGeneratePollCsv:
    def test_malicious_title_description_and_option_neutralized(self):
        poll = Poll(
            id=_uuid(),
            family_id=_uuid(),
            title="=cmd|' /C calc'!A1",
            description="+SUM(1,1)",
        )
        poll.options = [
            PollOption(
                id=_uuid(), poll_id=poll.id, text='=HYPERLINK("http://evil")', display_order=0
            )
        ]
        poll.votes = []

        rows = list(csv.reader(io.StringIO(generate_poll_csv(poll))))

        assert ["Poll", "'=cmd|' /C calc'!A1"] in rows
        assert ["Description", "'+SUM(1,1)"] in rows
        # The option cell is neutralized too (not just the title).
        assert any(row and row[0] == '\'=HYPERLINK("http://evil")' for row in rows)
