"""Tests for the gift exchange assignment algorithm and service."""

from __future__ import annotations

import random
import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventType
from app.models.family import Family
from app.models.family_membership import FamilyMembership, FamilyRole
from app.models.gift_exchange import GiftExchangeAssignment, GiftExchangeExclusion
from app.models.user import User
from app.services.gift_exchange import (
    build_exclusion_set,
    generate_assignments,
    run_assignments,
)


def _uuid() -> str:
    return str(uuid.uuid4())


def _make_participant(user_id: str | None = None) -> tuple[User, FamilyMembership]:
    """Create a mock (User, FamilyMembership) tuple for pure-function tests."""
    uid = user_id or _uuid()
    user = MagicMock(spec=User)
    user.id = uid
    membership = MagicMock(spec=FamilyMembership)
    membership.display_name = f"User-{uid[:8]}"
    return (user, membership)


def _make_exclusion(giver_id: str, receiver_id: str) -> GiftExchangeExclusion:
    """Create a mock exclusion for pure-function tests."""
    ex = MagicMock(spec=GiftExchangeExclusion)
    ex.giver_id = giver_id
    ex.receiver_id = receiver_id
    return ex


# ============ build_exclusion_set tests ============


class TestBuildExclusionSet:
    def test_empty_exclusions(self):
        result = build_exclusion_set([])
        assert result == set()

    def test_single_exclusion_is_mutual(self):
        ex = _make_exclusion("alice", "bob")
        result = build_exclusion_set([ex])
        assert ("alice", "bob") in result
        assert ("bob", "alice") in result
        assert len(result) == 2

    def test_multiple_exclusions(self):
        ex1 = _make_exclusion("alice", "bob")
        ex2 = _make_exclusion("carol", "dave")
        result = build_exclusion_set([ex1, ex2])
        assert len(result) == 4
        assert ("alice", "bob") in result
        assert ("bob", "alice") in result
        assert ("carol", "dave") in result
        assert ("dave", "carol") in result

    def test_duplicate_exclusion_doesnt_inflate(self):
        ex1 = _make_exclusion("alice", "bob")
        ex2 = _make_exclusion("alice", "bob")
        result = build_exclusion_set([ex1, ex2])
        assert len(result) == 2


# ============ generate_assignments tests ============


class TestGenerateAssignments:
    def test_two_participants_no_exclusions(self):
        p1 = _make_participant("alice")
        p2 = _make_participant("bob")
        result = generate_assignments([p1, p2], set())
        assert result is not None
        assert result["alice"] == "bob"
        assert result["bob"] == "alice"

    def test_two_participants_mutual_exclusion_returns_none(self):
        p1 = _make_participant("alice")
        p2 = _make_participant("bob")
        exclusions = {("alice", "bob"), ("bob", "alice")}
        result = generate_assignments([p1, p2], exclusions, max_attempts=50)
        assert result is None

    def test_single_participant_returns_none(self):
        p1 = _make_participant("alice")
        result = generate_assignments([p1], set())
        assert result is None

    def test_zero_participants_returns_none(self):
        result = generate_assignments([], set())
        assert result is None

    def test_three_participants_valid_derangement(self):
        p1 = _make_participant("a")
        p2 = _make_participant("b")
        p3 = _make_participant("c")
        random.seed(42)
        result = generate_assignments([p1, p2, p3], set())
        assert result is not None
        assert len(result) == 3
        # No self-assignments
        for giver, receiver in result.items():
            assert giver != receiver
        # Everyone receives exactly one gift
        assert set(result.values()) == {"a", "b", "c"}

    def test_five_participants_with_exclusion(self):
        participants = [_make_participant(str(i)) for i in range(5)]
        exclusions = {("0", "1"), ("1", "0")}  # 0 and 1 can't be paired
        random.seed(123)
        result = generate_assignments(participants, exclusions)
        assert result is not None
        assert len(result) == 5
        # No self-assignments
        for giver, receiver in result.items():
            assert giver != receiver
        # Exclusion respected
        assert result.get("0") != "1"
        assert result.get("1") != "0"
        # Everyone receives exactly one gift
        assert set(result.values()) == {str(i) for i in range(5)}

    def test_all_mutually_excluded_returns_none(self):
        """When every pair is excluded, assignment is impossible."""
        ids = ["a", "b", "c"]
        participants = [_make_participant(uid) for uid in ids]
        exclusions = set()
        for i in ids:
            for j in ids:
                if i != j:
                    exclusions.add((i, j))
        result = generate_assignments(participants, exclusions, max_attempts=50)
        assert result is None

    def test_large_group_succeeds(self):
        """20 participants with 10 exclusion pairs should complete."""
        ids = [str(i) for i in range(20)]
        participants = [_make_participant(uid) for uid in ids]
        # 10 exclusion pairs (adjacent)
        exclusions = set()
        for i in range(0, 20, 2):
            exclusions.add((ids[i], ids[i + 1]))
            exclusions.add((ids[i + 1], ids[i]))
        random.seed(999)
        result = generate_assignments(participants, exclusions)
        assert result is not None
        assert len(result) == 20
        for giver, receiver in result.items():
            assert giver != receiver
            assert (giver, receiver) not in exclusions

    def test_determinism_with_seed(self):
        """Same seed produces same assignments."""
        participants = [_make_participant(str(i)) for i in range(6)]
        exclusions: set[tuple[str, str]] = set()

        random.seed(42)
        result1 = generate_assignments(participants, exclusions)

        random.seed(42)
        result2 = generate_assignments(participants, exclusions)

        assert result1 == result2

    def test_every_participant_gives_and_receives(self):
        """Verify bijection: givers == receivers == all participants."""
        ids = [str(i) for i in range(8)]
        participants = [_make_participant(uid) for uid in ids]
        result = generate_assignments(participants, set())
        assert result is not None
        assert set(result.keys()) == set(ids)
        assert set(result.values()) == set(ids)


# ============ run_assignments (async, DB-backed) tests ============


class TestRunAssignments:
    @pytest.fixture
    async def gift_exchange_scenario(self, db: AsyncSession):
        """Create a family with 5 users and a gift exchange event."""
        family = Family(id=_uuid(), name="GX Family", family_code="GXTEST")
        db.add(family)

        users = []
        for i in range(5):
            user = User(
                id=_uuid(),
                email=f"gx{i}@test.com",
                is_super_admin=False,
                current_family_id=family.id,
            )
            db.add(user)
            db.add(
                FamilyMembership(
                    id=_uuid(),
                    user_id=user.id,
                    family_id=family.id,
                    role=FamilyRole.MEMBER,
                    display_name=f"GX User {i}",
                )
            )
            users.append(user)

        from datetime import UTC, datetime, timedelta

        event = Event(
            id=_uuid(),
            family_id=family.id,
            created_by_id=users[0].id,
            event_type=EventType.GENERAL.value,
            title="Gift Exchange",
            has_secret_santa=True,
            event_date=datetime.now(UTC) + timedelta(days=30),
        )
        db.add(event)
        await db.commit()

        return {"family": family, "users": users, "event": event}

    async def test_successful_run_persists_assignments(
        self, db: AsyncSession, gift_exchange_scenario
    ):
        s = gift_exchange_scenario
        result = await run_assignments(db, s["event"].id, s["family"].id)
        assert result is not None
        assert len(result) == 5

        # Verify rows in DB
        rows = await db.execute(
            select(GiftExchangeAssignment).where(GiftExchangeAssignment.event_id == s["event"].id)
        )
        assignments = list(rows.scalars().all())
        assert len(assignments) == 5

    async def test_rerun_clears_old_assignments(self, db: AsyncSession, gift_exchange_scenario):
        s = gift_exchange_scenario
        # Run twice
        await run_assignments(db, s["event"].id, s["family"].id)
        result2 = await run_assignments(db, s["event"].id, s["family"].id)
        assert result2 is not None

        # Should still have exactly 5 assignments (not 10)
        rows = await db.execute(
            select(GiftExchangeAssignment).where(GiftExchangeAssignment.event_id == s["event"].id)
        )
        assignments = list(rows.scalars().all())
        assert len(assignments) == 5

    async def test_impossible_config_returns_none_no_rows(
        self, db: AsyncSession, gift_exchange_scenario
    ):
        s = gift_exchange_scenario
        user_ids = [u.id for u in s["users"]]

        # Exclude everyone from everyone
        for i, giver_id in enumerate(user_ids):
            for j, receiver_id in enumerate(user_ids):
                if i != j:
                    db.add(
                        GiftExchangeExclusion(
                            id=_uuid(),
                            event_id=s["event"].id,
                            giver_id=giver_id,
                            receiver_id=receiver_id,
                        )
                    )
        await db.commit()

        result = await run_assignments(db, s["event"].id, s["family"].id)
        assert result is None

        # No assignments should exist
        rows = await db.execute(
            select(GiftExchangeAssignment).where(GiftExchangeAssignment.event_id == s["event"].id)
        )
        assert len(list(rows.scalars().all())) == 0
