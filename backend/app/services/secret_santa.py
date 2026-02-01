"""Secret Santa service - assignment algorithm and management (multi-family aware)."""

import random

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Event,
    FamilyMembership,
    SecretSantaAssignment,
    SecretSantaExclusion,
    SecretSantaMessage,
    User,
)


async def get_event(session: AsyncSession, event_id: str) -> Event | None:
    """Get an event by ID."""
    result = await session.execute(select(Event).where(Event.id == event_id))
    return result.scalar_one_or_none()


async def get_participants(
    session: AsyncSession, event_id: str, family_id: str
) -> list[tuple[User, FamilyMembership]]:
    """Get all participants in a Secret Santa event (family members).

    Returns list of (User, FamilyMembership) tuples for the family.
    """
    result = await session.execute(
        select(User, FamilyMembership)
        .join(FamilyMembership, User.id == FamilyMembership.user_id)
        .where(FamilyMembership.family_id == family_id)
        .order_by(FamilyMembership.display_name)
    )
    return list(result.all())


async def get_exclusions(session: AsyncSession, event_id: str) -> list[SecretSantaExclusion]:
    """Get all exclusion rules for an event."""
    result = await session.execute(
        select(SecretSantaExclusion).where(SecretSantaExclusion.event_id == event_id)
    )
    return list(result.scalars().all())


async def add_exclusion(
    session: AsyncSession, event_id: str, user1_id: str, user2_id: str
) -> SecretSantaExclusion:
    """Add a mutual exclusion rule between two users."""
    exclusion = SecretSantaExclusion(
        event_id=event_id,
        giver_id=user1_id,
        receiver_id=user2_id,
    )
    session.add(exclusion)
    await session.commit()
    await session.refresh(exclusion)
    return exclusion


async def remove_exclusion(session: AsyncSession, exclusion_id: str) -> bool:
    """Remove an exclusion rule."""
    result = await session.execute(
        select(SecretSantaExclusion).where(SecretSantaExclusion.id == exclusion_id)
    )
    exclusion = result.scalar_one_or_none()
    if exclusion:
        await session.delete(exclusion)
        await session.commit()
        return True
    return False


async def get_assignments(session: AsyncSession, event_id: str) -> list[SecretSantaAssignment]:
    """Get all assignments for an event."""
    result = await session.execute(
        select(SecretSantaAssignment).where(SecretSantaAssignment.event_id == event_id)
    )
    return list(result.scalars().all())


async def get_user_assignment(
    session: AsyncSession, event_id: str, giver_id: str
) -> SecretSantaAssignment | None:
    """Get a specific user's assignment (who they give to)."""
    result = await session.execute(
        select(SecretSantaAssignment).where(
            and_(
                SecretSantaAssignment.event_id == event_id,
                SecretSantaAssignment.giver_id == giver_id,
            )
        )
    )
    return result.scalar_one_or_none()


# Backwards compatibility alias
get_member_assignment = get_user_assignment


async def clear_assignments(session: AsyncSession, event_id: str) -> None:
    """Clear all existing assignments for an event."""
    assignments = await get_assignments(session, event_id)
    for assignment in assignments:
        await session.delete(assignment)
    await session.commit()


def build_exclusion_set(exclusions: list[SecretSantaExclusion]) -> set[tuple[str, str]]:
    """Build a set of (giver_id, receiver_id) pairs that are not allowed."""
    excluded = set()
    for ex in exclusions:
        excluded.add((str(ex.giver_id), str(ex.receiver_id)))
        # Make exclusions mutual
        excluded.add((str(ex.receiver_id), str(ex.giver_id)))
    return excluded


def generate_assignments(
    participants: list[tuple[User, FamilyMembership]],
    exclusions: set[tuple[str, str]],
    max_attempts: int = 100,
) -> dict[str, str] | None:
    """
    Generate Secret Santa assignments using a derangement algorithm.

    Uses a randomized algorithm to generate a valid assignment where:
    - No one gets themselves
    - Exclusion pairs are respected
    - Everyone gives exactly one gift and receives exactly one gift

    Returns a dict mapping giver_id -> receiver_id, or None if impossible.
    """
    if len(participants) < 2:
        return None

    user_ids = [str(user.id) for user, _ in participants]

    for _ in range(max_attempts):
        assignments = {}
        available = user_ids.copy()
        random.shuffle(available)

        valid = True
        for giver_id in user_ids:
            # Find a valid receiver for this giver
            found = False
            for i, receiver_id in enumerate(available):
                # Check constraints
                if receiver_id == giver_id:
                    continue
                if (giver_id, receiver_id) in exclusions:
                    continue

                # Valid assignment
                assignments[giver_id] = receiver_id
                available.pop(i)
                found = True
                break

            if not found:
                # Backtrack - this attempt failed
                valid = False
                break

        if valid and len(assignments) == len(user_ids):
            return assignments

    return None


async def run_assignments(
    session: AsyncSession, event_id: str, family_id: str
) -> dict[str, str] | None:
    """
    Run the Secret Santa assignment algorithm for an event.

    Returns the assignments dict if successful, None if impossible.
    """
    # Get participants and exclusions
    participants = await get_participants(session, event_id, family_id)
    exclusions = await get_exclusions(session, event_id)
    exclusion_set = build_exclusion_set(exclusions)

    # Generate assignments
    assignments = generate_assignments(participants, exclusion_set)

    if not assignments:
        return None

    # Clear old assignments
    await clear_assignments(session, event_id)

    # Save new assignments
    for giver_id, receiver_id in assignments.items():
        assignment = SecretSantaAssignment(
            event_id=event_id,
            giver_id=giver_id,
            receiver_id=receiver_id,
        )
        session.add(assignment)

    await session.commit()
    return assignments


async def send_message(
    session: AsyncSession,
    event_id: str,
    sender_id: str,
    recipient_id: str,
    content: str,
) -> SecretSantaMessage:
    """Send an anonymous message between Secret Santa participants."""
    message = SecretSantaMessage(
        event_id=event_id,
        sender_id=sender_id,
        recipient_id=recipient_id,
        content=content,
    )
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def get_received_messages(
    session: AsyncSession, event_id: str, recipient_id: str
) -> list[SecretSantaMessage]:
    """Get messages received by a participant (from their Secret Santa)."""
    result = await session.execute(
        select(SecretSantaMessage)
        .where(
            and_(
                SecretSantaMessage.event_id == event_id,
                SecretSantaMessage.recipient_id == recipient_id,
            )
        )
        .order_by(SecretSantaMessage.created_at.desc())
    )
    return list(result.scalars().all())


async def get_sent_messages(
    session: AsyncSession, event_id: str, sender_id: str
) -> list[SecretSantaMessage]:
    """Get messages sent by a participant (to their giftee)."""
    result = await session.execute(
        select(SecretSantaMessage)
        .where(
            and_(
                SecretSantaMessage.event_id == event_id,
                SecretSantaMessage.sender_id == sender_id,
            )
        )
        .order_by(SecretSantaMessage.created_at.desc())
    )
    return list(result.scalars().all())
