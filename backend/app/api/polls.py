"""Polls API endpoints — family and event-scoped polls."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.auth import require_family_context
from app.api.event_helpers import is_secret_birthday_for_user, resolve_event_or_404
from app.db import get_db_session
from app.models import Event, FamilyMembership, User
from app.models.poll import Poll, PollOption, PollVote
from app.schemas.poll import PollCreate, PollVoteRequest
from app.services.notifications.fire import send_notification_background
from app.services.permissions import permissions
from app.services.poll_export import generate_poll_csv

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_display_name(db: AsyncSession, user_id: str, family_id: str) -> str:
    """Get user's display name in a family."""
    result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == family_id,
        )
    )
    membership = result.scalar_one_or_none()
    return membership.display_name if membership else "Unknown"


async def _resolve_poll_or_404(db: AsyncSession, poll_id: str, user: User) -> Poll:
    """Load poll, enforce family membership + event-scoped secret birthday check.

    Returns 404 for all denial paths.
    """
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    # Normalize cross-family access to 404
    if poll.family_id != user.active_family_id:
        raise HTTPException(status_code=404, detail="Poll not found")

    # If event-scoped, enforce event visibility (secret birthday check)
    if poll.event_id:
        await resolve_event_or_404(
            db,
            str(poll.event_id),
            user,
            options=[selectinload(Event.birthday_detail)],
        )

    return poll


def _poll_to_dict(
    poll: Poll,
    current_user_id: str,
    creator_name: str | None = None,
) -> dict:
    """Convert a Poll model to a response dict."""
    user_votes: list[str] = []
    for vote in poll.votes:
        if vote.user_id == current_user_id:
            user_votes.append(str(vote.option_id))

    options = []
    for opt in sorted(poll.options, key=lambda o: o.display_order):
        opt_votes = [v for v in poll.votes if v.option_id == opt.id]
        opt_dict: dict = {
            "id": str(opt.id),
            "text": opt.text,
            "display_order": opt.display_order,
            "vote_count": len(opt_votes),
        }
        # Only include voter names if not anonymous
        if not poll.is_anonymous:
            opt_dict["voted_by"] = [str(v.user_id) for v in opt_votes]
        else:
            opt_dict["voted_by"] = None
        options.append(opt_dict)

    # Count unique voters
    unique_voters = {v.user_id for v in poll.votes}

    return {
        "id": str(poll.id),
        "family_id": str(poll.family_id),
        "event_id": str(poll.event_id) if poll.event_id else None,
        "created_by_id": str(poll.created_by_id) if poll.created_by_id else None,
        "created_by_name": creator_name,
        "title": poll.title,
        "description": poll.description,
        "allow_multiple": poll.allow_multiple,
        "is_anonymous": poll.is_anonymous,
        "close_date": poll.close_date.isoformat() if poll.close_date else None,
        "is_closed": poll.is_closed,
        "total_votes": len(unique_voters),
        "user_voted": len(user_votes) > 0,
        "user_votes": user_votes,
        "options": options,
        "created_at": poll.created_at.isoformat() if poll.created_at else None,
    }


@router.get("")
async def list_polls(
    event_id: str | None = None,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List polls for the current family, optionally filtered by event."""
    family_id = user.active_family_id

    # If filtering by event, enforce event access first
    if event_id:
        await resolve_event_or_404(
            db,
            event_id,
            user,
            options=[selectinload(Event.birthday_detail)],
        )

    query = select(Poll).where(Poll.family_id == family_id)
    if event_id:
        query = query.where(Poll.event_id == event_id)
    query = query.order_by(Poll.created_at.desc())

    result = await db.execute(query)
    polls = list(result.scalars().all())

    # Filter out polls attached to secret birthday events (when no event_id filter)
    if not event_id:
        event_ids = {str(p.event_id) for p in polls if p.event_id}
        if event_ids:
            event_result = await db.execute(select(Event).where(Event.id.in_(event_ids)))
            hidden_event_ids = {
                str(e.id)
                for e in event_result.scalars().all()
                if is_secret_birthday_for_user(e, str(user.id), user.is_super_admin)
            }
            if hidden_event_ids:
                polls = [
                    p for p in polls if not p.event_id or str(p.event_id) not in hidden_event_ids
                ]

    poll_dicts = []
    for poll in polls:
        creator_name = None
        if poll.created_by_id:
            creator_name = await _get_display_name(db, poll.created_by_id, family_id)
        poll_dicts.append(_poll_to_dict(poll, user.id, creator_name))

    return {"polls": poll_dicts}


@router.post("", status_code=201)
async def create_poll(
    data: PollCreate,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new poll."""
    family_id = user.active_family_id

    # If event-scoped, verify event access (membership + secret birthday)
    if data.event_id:
        await resolve_event_or_404(
            db,
            data.event_id,
            user,
            options=[selectinload(Event.birthday_detail)],
        )

    poll = Poll(
        family_id=family_id,
        event_id=data.event_id,
        created_by_id=user.id,
        title=data.title,
        description=data.description,
        allow_multiple=data.allow_multiple,
        is_anonymous=data.is_anonymous,
        close_date=data.close_date,
    )
    db.add(poll)
    await db.flush()

    # Create options
    for i, opt_data in enumerate(data.options):
        option = PollOption(
            poll_id=poll.id,
            text=opt_data.text,
            display_order=opt_data.display_order if opt_data.display_order else i,
        )
        db.add(option)

    await db.flush()
    # Refresh to load relationships
    await db.refresh(poll, ["options", "votes"])

    creator_name = await _get_display_name(db, user.id, family_id)

    # Fire notification in background
    background_tasks.add_task(
        send_notification_background,
        "notify_poll_created",
        poll_question=poll.title,
        creator_name=creator_name,
    )

    return _poll_to_dict(poll, user.id, creator_name)


@router.get("/{poll_id}")
async def get_poll(
    poll_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a single poll with full details."""
    poll = await _resolve_poll_or_404(db, poll_id, user)

    creator_name = None
    if poll.created_by_id:
        creator_name = await _get_display_name(db, poll.created_by_id, user.active_family_id)
    return _poll_to_dict(poll, user.id, creator_name)


@router.post("/{poll_id}/vote")
async def vote_on_poll(
    poll_id: str,
    data: PollVoteRequest,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Vote on a poll. Single-select replaces previous vote. Multi-select toggles."""
    poll = await _resolve_poll_or_404(db, poll_id, user)

    if poll.is_closed:
        raise HTTPException(status_code=400, detail="This poll is closed")

    # Validate all option IDs belong to this poll
    poll_option_ids = {str(opt.id) for opt in poll.options}
    for opt_id in data.option_ids:
        if opt_id not in poll_option_ids:
            raise HTTPException(status_code=400, detail=f"Invalid option: {opt_id}")

    # Single-select: only one option allowed
    if not poll.allow_multiple and len(data.option_ids) > 1:
        raise HTTPException(status_code=400, detail="This poll only allows a single selection")

    # Get existing votes by this user on this poll
    existing_votes_result = await db.execute(
        select(PollVote).where(
            PollVote.poll_id == poll_id,
            PollVote.user_id == user.id,
        )
    )
    existing_votes = list(existing_votes_result.scalars().all())

    if poll.allow_multiple:
        # Multi-select: toggle — add votes for new options, remove votes for existing options
        existing_option_ids = {str(v.option_id) for v in existing_votes}
        new_option_ids = set(data.option_ids)

        # Remove votes that are being toggled off
        for vote in existing_votes:
            if str(vote.option_id) in new_option_ids:
                await db.delete(vote)

        # Add votes that are new (not toggled off)
        for opt_id in new_option_ids:
            if opt_id not in existing_option_ids:
                db.add(PollVote(poll_id=poll_id, option_id=opt_id, user_id=user.id))
    else:
        # Single-select: replace all existing votes
        for vote in existing_votes:
            await db.delete(vote)
        db.add(
            PollVote(
                poll_id=poll_id,
                option_id=data.option_ids[0],
                user_id=user.id,
            )
        )

    await db.flush()
    await db.refresh(poll, ["options", "votes"])

    creator_name = None
    if poll.created_by_id:
        creator_name = await _get_display_name(db, poll.created_by_id, user.active_family_id)
    return _poll_to_dict(poll, user.id, creator_name)


@router.post("/{poll_id}/close")
async def close_poll(
    poll_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Manually close a poll. Requires creator or family admin."""
    poll = await _resolve_poll_or_404(db, poll_id, user)

    # Only creator or family admin can close
    is_admin = await permissions.is_family_admin(db, user, poll.family_id)
    if poll.created_by_id != user.id and not is_admin:
        raise HTTPException(
            status_code=403, detail="Only the poll creator or a family admin can close this poll"
        )

    if poll.is_closed:
        raise HTTPException(status_code=400, detail="Poll is already closed")

    poll.closed_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(poll, ["options", "votes"])

    creator_name = None
    if poll.created_by_id:
        creator_name = await _get_display_name(db, poll.created_by_id, user.active_family_id)
    return _poll_to_dict(poll, user.id, creator_name)


@router.delete("/{poll_id}", status_code=204)
async def delete_poll(
    poll_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a poll. Requires creator or family admin."""
    poll = await _resolve_poll_or_404(db, poll_id, user)

    is_admin = await permissions.is_family_admin(db, user, poll.family_id)
    if poll.created_by_id != user.id and not is_admin:
        raise HTTPException(
            status_code=403, detail="Only the poll creator or a family admin can delete this poll"
        )

    await db.delete(poll)


@router.get("/{poll_id}/export")
async def export_poll_csv(
    poll_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Export poll results as CSV. Requires creator or family admin."""
    poll = await _resolve_poll_or_404(db, poll_id, user)

    is_admin = await permissions.is_family_admin(db, user, poll.family_id)
    if poll.created_by_id != user.id and not is_admin:
        raise HTTPException(
            status_code=403, detail="Only the poll creator or a family admin can export results"
        )

    csv_content = generate_poll_csv(poll)
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in poll.title)[:50].strip()
    filename = f"poll-{safe_title}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
