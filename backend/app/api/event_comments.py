"""Event comments API endpoints — chronological discussion threads on events."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_family_context
from app.api.event_helpers import resolve_event_or_404
from app.db import get_db_session
from app.models import FamilyMembership, User
from app.models.comment_mention import CommentMention
from app.models.event_comment import EventComment
from app.schemas.event_comment import EventCommentCreate, EventCommentUpdate
from app.services.mention_parser import extract_mentions
from app.services.notifications.dispatcher import NotificationDispatcher
from app.services.permissions import permissions

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


def _reactions_summary(comment: EventComment) -> list[dict]:
    """Build a summary of reactions on a comment."""
    emoji_counts: dict[str, list[str]] = {}
    for r in comment.reactions:
        emoji_counts.setdefault(r.emoji, []).append(str(r.user_id))
    return [
        {"emoji": emoji, "count": len(user_ids), "user_ids": user_ids}
        for emoji, user_ids in sorted(emoji_counts.items())
    ]


def _comment_to_dict(comment: EventComment, current_user_id: str, user_name: str) -> dict:
    """Convert a comment model to a response dict."""
    return {
        "id": str(comment.id),
        "event_id": str(comment.event_id),
        "user_id": str(comment.user_id),
        "user_name": user_name,
        "content": comment.content,
        "edited_at": comment.edited_at.isoformat() if comment.edited_at else None,
        "is_own": comment.user_id == current_user_id,
        "is_pinned": comment.pinned_at is not None,
        "pinned_at": comment.pinned_at.isoformat() if comment.pinned_at else None,
        "reactions": _reactions_summary(comment),
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }


@router.get("/{event_id}/comments")
async def list_comments(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List comments for an event. Pinned comments appear first, then chronological."""
    event = await resolve_event_or_404(db, event_id, user)

    result = await db.execute(
        select(EventComment)
        .where(EventComment.event_id == event_id)
        .order_by(EventComment.created_at.asc())
    )
    comments = list(result.scalars().all())

    # Sort: pinned first (by pinned_at), then unpinned chronologically
    pinned = [c for c in comments if c.pinned_at is not None]
    unpinned = [c for c in comments if c.pinned_at is None]
    pinned.sort(key=lambda c: c.pinned_at or datetime.min)
    sorted_comments = pinned + unpinned

    # Build display name cache to avoid N+1
    user_ids = {c.user_id for c in comments}
    name_cache: dict[str, str] = {}
    for uid in user_ids:
        name_cache[uid] = await _get_display_name(db, uid, event.family_id)

    return {
        "comments": [
            _comment_to_dict(c, user.id, name_cache.get(c.user_id, "Unknown"))
            for c in sorted_comments
        ]
    }


@router.post("/{event_id}/comments", status_code=201)
async def create_comment(
    event_id: str,
    data: EventCommentCreate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Add a comment to an event. Parses @mentions and fires notifications."""
    event = await resolve_event_or_404(db, event_id, user)

    if event.is_cancelled:
        raise HTTPException(status_code=400, detail="Cannot comment on a cancelled event")

    comment = EventComment(
        event_id=event_id,
        user_id=user.id,
        content=data.content,
    )
    db.add(comment)
    await db.flush()

    user_name = await _get_display_name(db, user.id, event.family_id)

    # Parse @mentions and create records
    mentioned_user_ids = await extract_mentions(db, data.content, event.family_id)
    # Don't mention yourself
    mentioned_user_ids = [uid for uid in mentioned_user_ids if uid != user.id]

    for uid in mentioned_user_ids:
        db.add(CommentMention(comment_id=comment.id, mentioned_user_id=uid))

    await db.flush()

    # Fire notifications
    try:
        dispatcher = NotificationDispatcher(db)
        await dispatcher.notify_comment_added(
            event_title=event.title,
            commenter_name=user_name,
        )
        # Fire separate mention notifications
        for mid in mentioned_user_ids:
            mentioned_name = await _get_display_name(db, mid, event.family_id)
            await dispatcher.notify_comment_mention(
                event_title=event.title,
                mentioner_name=user_name,
                mentioned_name=mentioned_name,
            )
    except Exception as e:
        logger.error("Failed to send comment notification: %s", e)

    await db.refresh(comment, ["reactions", "mentions"])
    return _comment_to_dict(comment, user.id, user_name)


@router.put("/{event_id}/comments/{comment_id}")
async def update_comment(
    event_id: str,
    comment_id: str,
    data: EventCommentUpdate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Edit own comment. Sets edited_at timestamp."""
    await resolve_event_or_404(db, event_id, user)

    result = await db.execute(
        select(EventComment).where(
            EventComment.id == comment_id,
            EventComment.event_id == event_id,
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")

    comment.content = data.content
    comment.edited_at = datetime.now(UTC)
    await db.flush()

    user_name = await _get_display_name(db, user.id, user.current_family_id or "")
    return _comment_to_dict(comment, user.id, user_name)


@router.post("/{event_id}/comments/{comment_id}/pin")
async def pin_comment(
    event_id: str,
    comment_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Pin a comment. Only event creator or family admin can pin."""
    event = await resolve_event_or_404(db, event_id, user)

    result = await db.execute(
        select(EventComment).where(
            EventComment.id == comment_id,
            EventComment.event_id == event_id,
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Only event creator or family admin
    is_admin = await permissions.is_family_admin(db, user, event.family_id)
    is_event_creator = event.created_by_id == user.id
    if not is_admin and not is_event_creator:
        raise HTTPException(
            status_code=403, detail="Only the event creator or a family admin can pin comments"
        )

    comment.pinned_at = datetime.now(UTC)
    await db.flush()

    user_name = await _get_display_name(db, comment.user_id, event.family_id)
    return _comment_to_dict(comment, user.id, user_name)


@router.delete("/{event_id}/comments/{comment_id}/pin")
async def unpin_comment(
    event_id: str,
    comment_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Unpin a comment. Only event creator or family admin can unpin."""
    event = await resolve_event_or_404(db, event_id, user)

    result = await db.execute(
        select(EventComment).where(
            EventComment.id == comment_id,
            EventComment.event_id == event_id,
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    is_admin = await permissions.is_family_admin(db, user, event.family_id)
    is_event_creator = event.created_by_id == user.id
    if not is_admin and not is_event_creator:
        raise HTTPException(
            status_code=403, detail="Only the event creator or a family admin can unpin comments"
        )

    comment.pinned_at = None
    await db.flush()

    user_name = await _get_display_name(db, comment.user_id, event.family_id)
    return _comment_to_dict(comment, user.id, user_name)


@router.delete("/{event_id}/comments/{comment_id}", status_code=204)
async def delete_comment(
    event_id: str,
    comment_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete own comment. Family admins can delete any comment."""
    event = await resolve_event_or_404(db, event_id, user)

    result = await db.execute(
        select(EventComment).where(
            EventComment.id == comment_id,
            EventComment.event_id == event_id,
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Owner can delete their own, admins can delete any
    is_admin = await permissions.is_family_admin(db, user, event.family_id)
    if comment.user_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")

    await db.delete(comment)
