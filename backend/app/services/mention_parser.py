"""Parse @mentions from comment text and resolve to user IDs."""

import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FamilyMembership

logger = logging.getLogger(__name__)

# Match @DisplayName patterns (handles names with spaces, stops at punctuation)
MENTION_PATTERN = re.compile(r"@([A-Za-z][A-Za-z0-9 ]{0,49})")


async def extract_mentions(
    db: AsyncSession,
    content: str,
    family_id: str,
) -> list[str]:
    """Extract @mentions from text and resolve to user IDs.

    Returns a list of unique user IDs that were mentioned.
    """
    matches = MENTION_PATTERN.findall(content)
    if not matches:
        return []

    # Normalize matches (strip trailing spaces)
    mentioned_names = {m.strip().lower() for m in matches}

    # Load all family members' display names for matching
    result = await db.execute(
        select(FamilyMembership).where(FamilyMembership.family_id == family_id)
    )
    memberships = result.scalars().all()

    resolved_user_ids: list[str] = []
    for membership in memberships:
        if membership.display_name and membership.display_name.lower() in mentioned_names:
            resolved_user_ids.append(str(membership.user_id))

    return list(set(resolved_user_ids))
