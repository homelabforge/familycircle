"""Tests for event helper functions — validation and secret birthday logic."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.event_helpers import is_secret_birthday_for_user, validate_event_type_and_details
from app.models.event import EventType


class TestValidateEventTypeAndDetails:
    """Tests for validate_event_type_and_details()."""

    def test_general_no_details_succeeds(self):
        request = SimpleNamespace(event_type="general")
        validate_event_type_and_details(request)  # Should not raise

    def test_invalid_event_type_raises_400(self):
        request = SimpleNamespace(event_type="nonexistent_type")
        with pytest.raises(HTTPException) as exc_info:
            validate_event_type_and_details(request)
        assert exc_info.value.status_code == 400

    def test_holiday_without_detail_raises_400(self):
        request = SimpleNamespace(
            event_type=EventType.HOLIDAY.value,
            holiday_detail=None,
        )
        with pytest.raises(HTTPException) as exc_info:
            validate_event_type_and_details(request)
        assert exc_info.value.status_code == 400
        assert "Holiday detail" in exc_info.value.detail

    def test_holiday_with_detail_succeeds(self):
        request = SimpleNamespace(
            event_type=EventType.HOLIDAY.value,
            holiday_detail={"holiday_name": "Christmas"},
        )
        validate_event_type_and_details(request)

    def test_birthday_without_detail_raises_400(self):
        request = SimpleNamespace(
            event_type=EventType.BIRTHDAY.value,
            birthday_detail=None,
        )
        with pytest.raises(HTTPException) as exc_info:
            validate_event_type_and_details(request)
        assert exc_info.value.status_code == 400
        assert "Birthday detail" in exc_info.value.detail

    def test_birthday_with_detail_succeeds(self):
        request = SimpleNamespace(
            event_type=EventType.BIRTHDAY.value,
            birthday_detail={"birthday_person_name": "Alice"},
        )
        validate_event_type_and_details(request)

    def test_baby_shower_without_detail_raises_400(self):
        request = SimpleNamespace(
            event_type=EventType.BABY_SHOWER.value,
            baby_shower_detail=None,
        )
        with pytest.raises(HTTPException) as exc_info:
            validate_event_type_and_details(request)
        assert exc_info.value.status_code == 400
        assert "Baby shower detail" in exc_info.value.detail

    def test_baby_shower_with_detail_succeeds(self):
        request = SimpleNamespace(
            event_type=EventType.BABY_SHOWER.value,
            baby_shower_detail={"parent1_name": "Jane"},
        )
        validate_event_type_and_details(request)

    def test_wedding_without_detail_raises_400(self):
        request = SimpleNamespace(
            event_type=EventType.WEDDING.value,
            wedding_detail=None,
        )
        with pytest.raises(HTTPException) as exc_info:
            validate_event_type_and_details(request)
        assert exc_info.value.status_code == 400
        assert "Wedding detail" in exc_info.value.detail

    def test_wedding_with_detail_succeeds(self):
        request = SimpleNamespace(
            event_type=EventType.WEDDING.value,
            wedding_detail={"partner1_name": "Alice", "partner2_name": "Bob"},
        )
        validate_event_type_and_details(request)


class TestIsSecretBirthdayForUser:
    """Tests for is_secret_birthday_for_user()."""

    def test_non_birthday_event_returns_false(self):
        event = SimpleNamespace(event_type=EventType.GENERAL.value)
        assert is_secret_birthday_for_user(event, "some-user") is False  # type: ignore[arg-type]

    def test_birthday_without_detail_returns_false(self):
        event = SimpleNamespace(
            event_type=EventType.BIRTHDAY.value,
            birthday_detail=None,
        )
        assert is_secret_birthday_for_user(event, "some-user") is False  # type: ignore[arg-type]

    def test_non_secret_birthday_returns_false(self):
        event = SimpleNamespace(
            event_type=EventType.BIRTHDAY.value,
            birthday_detail=SimpleNamespace(is_secret=False, birthday_person_id="target"),
        )
        assert is_secret_birthday_for_user(event, "target") is False  # type: ignore[arg-type]

    def test_secret_birthday_hidden_from_birthday_person(self):
        event = SimpleNamespace(
            event_type=EventType.BIRTHDAY.value,
            birthday_detail=SimpleNamespace(is_secret=True, birthday_person_id="target"),
        )
        assert is_secret_birthday_for_user(event, "target") is True  # type: ignore[arg-type]

    def test_secret_birthday_visible_to_others(self):
        event = SimpleNamespace(
            event_type=EventType.BIRTHDAY.value,
            birthday_detail=SimpleNamespace(is_secret=True, birthday_person_id="target"),
        )
        assert is_secret_birthday_for_user(event, "other-user") is False  # type: ignore[arg-type]

    def test_super_admin_bypasses_secret_filter(self):
        event = SimpleNamespace(
            event_type=EventType.BIRTHDAY.value,
            birthday_detail=SimpleNamespace(is_secret=True, birthday_person_id="target"),
        )
        assert is_secret_birthday_for_user(event, "target", is_super_admin=True) is False  # type: ignore[arg-type]
