"""Comment reactions API — toggle emoji reactions on event comments."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_family_context
from app.api.event_helpers import resolve_event_or_404
from app.db import get_db_session
from app.models import User
from app.models.comment_reaction import CommentReaction
from app.models.event_comment import EventComment
from app.schemas.comment_reaction import CommentReactionToggle

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{event_id}/comments/{comment_id}/reactions")
async def toggle_reaction(
    event_id: str,
    comment_id: str,
    data: CommentReactionToggle,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Toggle a reaction on a comment. Add if not present, remove if already there."""
    await resolve_event_or_404(db, event_id, user)

    # Verify comment exists on this event
    result = await db.execute(
        select(EventComment).where(
            EventComment.id == comment_id,
            EventComment.event_id == event_id,
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Check if reaction already exists
    result = await db.execute(
        select(CommentReaction).where(
            CommentReaction.comment_id == comment_id,
            CommentReaction.user_id == user.id,
            CommentReaction.emoji == data.emoji,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Remove reaction
        await db.delete(existing)
        action = "removed"
    else:
        # Add reaction
        reaction = CommentReaction(
            comment_id=comment_id,
            user_id=user.id,
            emoji=data.emoji,
        )
        db.add(reaction)
        action = "added"

    await db.flush()

    # Reload comment to get updated reactions
    await db.refresh(comment, ["reactions"])

    return {
        "action": action,
        "reactions": _reactions_summary(comment),
    }


def _reactions_summary(comment: EventComment) -> list[dict]:
    """Build a summary of reactions on a comment."""
    emoji_counts: dict[str, list[str]] = {}
    for r in comment.reactions:
        emoji_counts.setdefault(r.emoji, []).append(str(r.user_id))
    return [
        {"emoji": emoji, "count": len(user_ids), "user_ids": user_ids}
        for emoji, user_ids in sorted(emoji_counts.items())
    ]
