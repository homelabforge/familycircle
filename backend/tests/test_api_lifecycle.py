"""API lifecycle integration tests — exercises real HTTP endpoints via httpx AsyncClient.

Tests the full request/response cycle including auth, serialization, and DB persistence.
Each test class covers one lifecycle flow:
  1. Event CRUD: create -> get -> update -> cancel -> delete
  2. Poll: create -> vote -> close -> verify results
  3. Comment: post -> edit -> react -> delete
  4. RSVP: yes -> add guest -> update guest -> remove guest -> change to no
"""

from __future__ import annotations

import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta

# Must be set before any app imports
os.environ["DATABASE_PATH"] = "/tmp/test-familycircle-lifecycle.db"

# Patch UPLOAD_DIR before app.main is imported — main.py calls mkdir at module level
# and /data doesn't exist on the test host.
import sys
from pathlib import Path

_test_upload_dir = Path("/tmp/test-fc-uploads")
_test_upload_dir.mkdir(parents=True, exist_ok=True)

# Remove cached modules so we can patch before re-import
for mod_name in list(sys.modules):
    if mod_name.startswith("app.main"):
        del sys.modules[mod_name]

# Patch Path.mkdir and StaticFiles to use our temp dir.
# main.py does: UPLOAD_DIR = Path("/data/uploads"); UPLOAD_DIR.mkdir(...);
#               app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), ...)
_orig_mkdir = Path.mkdir


def _patched_mkdir(self, *args, **kwargs):
    if str(self).startswith("/data"):
        _test_upload_dir.mkdir(parents=True, exist_ok=True)
        return
    return _orig_mkdir(self, *args, **kwargs)


from starlette.staticfiles import StaticFiles  # noqa: E402

_orig_staticfiles_init = StaticFiles.__init__


def _patched_staticfiles_init(self, *args, **kwargs):
    directory = kwargs.get("directory") or (args[0] if args else None)
    if directory and str(directory).startswith("/data"):
        kwargs["directory"] = str(_test_upload_dir)
        if args:
            args = (str(_test_upload_dir),) + args[1:]
    return _orig_staticfiles_init(self, *args, **kwargs)


Path.mkdir = _patched_mkdir  # type: ignore[assignment]
StaticFiles.__init__ = _patched_staticfiles_init  # type: ignore[assignment]

import app.main as _main_mod  # noqa: E402, F401

Path.mkdir = _orig_mkdir  # type: ignore[assignment]
StaticFiles.__init__ = _orig_staticfiles_init  # type: ignore[assignment]

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.base import Base  # noqa: E402
from app.models.family import Family  # noqa: E402
from app.models.family_membership import FamilyMembership, FamilyRole  # noqa: E402
from app.models.token import Token, TokenType  # noqa: E402
from app.models.user import User  # noqa: E402


def _uuid() -> str:
    return str(uuid.uuid4())


def _token() -> str:
    return secrets.token_hex(32)


# ---------------------------------------------------------------------------
# Shared engine / session factory — one in-memory DB per test function
# ---------------------------------------------------------------------------


@pytest.fixture
async def engine():
    """Create a fresh in-memory SQLite engine for each test."""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session_factory(engine):
    """Session factory bound to the in-memory engine."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def seed(session_factory):
    """Seed a user + family + membership + session token. Returns a dict of IDs/token."""
    async with session_factory() as db:
        family_id = _uuid()
        user_id = _uuid()
        token_value = _token()

        family = Family(id=family_id, name="Test Family", family_code="TEST01")
        user = User(
            id=user_id,
            email="lifecycle@test.com",
            is_super_admin=False,
            current_family_id=family_id,
        )
        membership = FamilyMembership(
            id=_uuid(),
            user_id=user_id,
            family_id=family_id,
            role=FamilyRole.ADMIN,
            display_name="Lifecycle User",
        )
        token = Token(
            id=_uuid(),
            user_id=user_id,
            token=token_value,
            token_type=TokenType.SESSION,
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )

        # Default settings required by init_default_settings / lifespan
        from app.models.settings import Setting

        db.add_all(
            [
                family,
                user,
                membership,
                token,
                Setting(key="secret_key", value=secrets.token_hex(32), family_id=None),
                Setting(key="app_name", value="FamilyCircle", family_id=None),
                Setting(key="magic_link_expiry_days", value="1", family_id=None),
            ]
        )
        await db.commit()

    return {
        "family_id": family_id,
        "user_id": user_id,
        "token": token_value,
    }


@pytest.fixture
async def client(engine, session_factory, seed):
    """AsyncClient wired to the FastAPI app with DB dependency overridden."""
    from app.db import get_db_session
    from app.main import app

    async def _override_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_db

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


def _auth_headers(token: str) -> dict[str, str]:
    """Build Authorization header for the test client."""
    return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# 1. Event CRUD Lifecycle
# ===========================================================================


class TestEventCRUDLifecycle:
    """Create -> get -> update -> cancel -> delete."""

    async def test_full_lifecycle(self, client: AsyncClient, seed: dict):
        headers = _auth_headers(seed["token"])
        tomorrow = (datetime.now(UTC) + timedelta(days=1)).isoformat()

        # --- CREATE ---
        resp = await client.post(
            "/api/events",
            json={
                "title": "Lifecycle Dinner",
                "description": "Test event",
                "event_date": tomorrow,
                "location_name": "Home",
                "has_rsvp": True,
                "event_type": "general",
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["message"] == "Event created"
        event_id = body["id"]

        # --- GET ---
        resp = await client.get(f"/api/events/{event_id}", headers=headers)
        assert resp.status_code == 200, resp.text
        event_data = resp.json()
        assert event_data["title"] == "Lifecycle Dinner"
        assert event_data["description"] == "Test event"
        assert event_data["location_name"] == "Home"
        assert event_data["can_manage"] is True

        # --- UPDATE ---
        resp = await client.put(
            f"/api/events/{event_id}",
            json={"title": "Lifecycle Brunch", "location_name": "Restaurant"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["message"] == "Event updated"

        # Verify update
        resp = await client.get(f"/api/events/{event_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Lifecycle Brunch"
        assert resp.json()["location_name"] == "Restaurant"

        # --- CANCEL ---
        resp = await client.post(
            f"/api/events/{event_id}/cancel",
            json={"reason": "Rain"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["message"] == "Event cancelled"

        # Verify cancelled state
        resp = await client.get(f"/api/events/{event_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["is_cancelled"] is True
        assert resp.json()["cancellation_reason"] == "Rain"

        # --- DELETE ---
        resp = await client.delete(f"/api/events/{event_id}", headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["message"] == "Event deleted"

        # Verify gone
        resp = await client.get(f"/api/events/{event_id}", headers=headers)
        assert resp.status_code == 404


# ===========================================================================
# 2. Poll Lifecycle
# ===========================================================================


class TestPollLifecycle:
    """Create poll -> vote -> close -> verify results."""

    async def test_full_lifecycle(self, client: AsyncClient, seed: dict):
        headers = _auth_headers(seed["token"])
        tomorrow = (datetime.now(UTC) + timedelta(days=1)).isoformat()

        # Create an event to attach the poll to (optional but realistic)
        resp = await client.post(
            "/api/events",
            json={"title": "Poll Event", "event_date": tomorrow, "event_type": "general"},
            headers=headers,
        )
        assert resp.status_code == 200
        event_id = resp.json()["id"]

        # --- CREATE POLL ---
        resp = await client.post(
            "/api/polls",
            json={
                "title": "What to eat?",
                "description": "Pick a cuisine",
                "event_id": event_id,
                "allow_multiple": False,
                "is_anonymous": False,
                "options": [
                    {"text": "Pizza", "display_order": 0},
                    {"text": "Sushi", "display_order": 1},
                    {"text": "Tacos", "display_order": 2},
                ],
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        poll = resp.json()
        poll_id = poll["id"]
        assert poll["title"] == "What to eat?"
        assert len(poll["options"]) == 3
        assert poll["is_closed"] is False
        assert poll["total_votes"] == 0

        # --- VOTE ---
        pizza_option_id = poll["options"][0]["id"]
        resp = await client.post(
            f"/api/polls/{poll_id}/vote",
            json={"option_ids": [pizza_option_id]},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        voted_poll = resp.json()
        assert voted_poll["user_voted"] is True
        assert voted_poll["total_votes"] == 1
        # Find the pizza option and verify vote count
        pizza_opt = next(o for o in voted_poll["options"] if o["id"] == pizza_option_id)
        assert pizza_opt["vote_count"] == 1

        # --- CLOSE ---
        resp = await client.post(f"/api/polls/{poll_id}/close", headers=headers)
        assert resp.status_code == 200, resp.text
        closed_poll = resp.json()
        assert closed_poll["is_closed"] is True

        # --- VERIFY CLOSED POLL REJECTS VOTES ---
        sushi_option_id = poll["options"][1]["id"]
        resp = await client.post(
            f"/api/polls/{poll_id}/vote",
            json={"option_ids": [sushi_option_id]},
            headers=headers,
        )
        assert resp.status_code == 400
        assert "closed" in resp.json()["detail"].lower()

        # --- GET FINAL STATE ---
        resp = await client.get(f"/api/polls/{poll_id}", headers=headers)
        assert resp.status_code == 200
        final = resp.json()
        assert final["is_closed"] is True
        assert final["total_votes"] == 1


# ===========================================================================
# 3. Comment Lifecycle
# ===========================================================================


class TestCommentLifecycle:
    """Post comment -> edit -> react -> delete."""

    async def test_full_lifecycle(self, client: AsyncClient, seed: dict):
        headers = _auth_headers(seed["token"])
        tomorrow = (datetime.now(UTC) + timedelta(days=1)).isoformat()

        # Create event
        resp = await client.post(
            "/api/events",
            json={"title": "Comment Event", "event_date": tomorrow, "event_type": "general"},
            headers=headers,
        )
        assert resp.status_code == 200
        event_id = resp.json()["id"]

        # --- POST COMMENT ---
        resp = await client.post(
            f"/api/events/{event_id}/comments",
            json={"content": "Hello everyone!"},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        comment = resp.json()
        comment_id = comment["id"]
        assert comment["content"] == "Hello everyone!"
        assert comment["is_own"] is True
        assert comment["edited_at"] is None

        # --- LIST COMMENTS ---
        resp = await client.get(f"/api/events/{event_id}/comments", headers=headers)
        assert resp.status_code == 200
        comments = resp.json()["comments"]
        assert len(comments) == 1
        assert comments[0]["id"] == comment_id

        # --- EDIT COMMENT ---
        resp = await client.put(
            f"/api/events/{event_id}/comments/{comment_id}",
            json={"content": "Hello everyone! (edited)"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        edited = resp.json()
        assert edited["content"] == "Hello everyone! (edited)"
        assert edited["edited_at"] is not None

        # --- ADD REACTION ---
        resp = await client.post(
            f"/api/events/{event_id}/comments/{comment_id}/reactions",
            json={"emoji": "👍"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        reaction_resp = resp.json()
        assert reaction_resp["action"] == "added"
        assert any(r["emoji"] == "👍" for r in reaction_resp["reactions"])

        # --- TOGGLE REACTION OFF ---
        resp = await client.post(
            f"/api/events/{event_id}/comments/{comment_id}/reactions",
            json={"emoji": "👍"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["action"] == "removed"

        # --- DELETE COMMENT ---
        resp = await client.delete(
            f"/api/events/{event_id}/comments/{comment_id}",
            headers=headers,
        )
        assert resp.status_code == 204

        # Verify gone
        resp = await client.get(f"/api/events/{event_id}/comments", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()["comments"]) == 0


# ===========================================================================
# 4. RSVP Lifecycle
# ===========================================================================


class TestRSVPLifecycle:
    """RSVP yes -> add guest -> update guest -> remove guest -> change to no."""

    async def test_full_lifecycle(self, client: AsyncClient, seed: dict):
        headers = _auth_headers(seed["token"])
        tomorrow = (datetime.now(UTC) + timedelta(days=1)).isoformat()

        # Create event with RSVP
        resp = await client.post(
            "/api/events",
            json={
                "title": "RSVP Event",
                "event_date": tomorrow,
                "has_rsvp": True,
                "event_type": "general",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        event_id = resp.json()["id"]

        # --- RSVP YES ---
        resp = await client.post(
            f"/api/events/{event_id}/rsvp",
            json={"status": "yes"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert "yes" in resp.json()["message"]

        # Verify RSVP reflected in event
        resp = await client.get(f"/api/events/{event_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["user_rsvp"] == "yes"
        assert resp.json()["rsvp_counts"]["yes"] == 1

        # --- ADD GUEST ---
        resp = await client.post(
            f"/api/events/{event_id}/rsvp/guests",
            json={"guest_name": "Plus One", "dietary_restrictions": "Vegetarian"},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        guest = resp.json()
        guest_id = guest["id"]
        assert guest["guest_name"] == "Plus One"
        assert guest["dietary_restrictions"] == "Vegetarian"

        # --- LIST GUESTS ---
        resp = await client.get(
            f"/api/events/{event_id}/rsvp/guests",
            headers=headers,
        )
        assert resp.status_code == 200
        guests = resp.json()["guests"]
        assert len(guests) == 1
        assert guests[0]["guest_name"] == "Plus One"

        # --- UPDATE GUEST ---
        resp = await client.put(
            f"/api/events/{event_id}/rsvp/guests/{guest_id}",
            json={"guest_name": "Plus One (updated)", "allergies": "Peanuts"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        updated_guest = resp.json()
        assert updated_guest["guest_name"] == "Plus One (updated)"
        assert updated_guest["allergies"] == "Peanuts"

        # Verify headcount: 1 member + 1 guest = 2
        resp = await client.get(f"/api/events/{event_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["headcount"] == 2

        # --- REMOVE GUEST ---
        resp = await client.delete(
            f"/api/events/{event_id}/rsvp/guests/{guest_id}",
            headers=headers,
        )
        assert resp.status_code == 204

        # Verify guest removed
        resp = await client.get(
            f"/api/events/{event_id}/rsvp/guests",
            headers=headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()["guests"]) == 0

        # --- CHANGE RSVP TO NO ---
        resp = await client.post(
            f"/api/events/{event_id}/rsvp",
            json={"status": "no"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert "no" in resp.json()["message"]

        # Verify counts updated
        resp = await client.get(f"/api/events/{event_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["user_rsvp"] == "no"
        assert resp.json()["rsvp_counts"]["yes"] == 0
        assert resp.json()["rsvp_counts"]["no"] == 1
