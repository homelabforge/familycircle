"""Gift Exchange API endpoints - multi-family aware."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_family_context
from app.api.event_helpers import resolve_event_or_404
from app.db import get_db_session
from app.models import FamilyMembership, User, WishlistItem
from app.services import gift_exchange as ss_service
from app.services.permissions import permissions

router = APIRouter()


class GiftExchangeStatus(BaseModel):
    """Gift Exchange status response."""

    event_id: str
    status: str  # not_assigned, assigned, revealed
    participant_count: int
    has_assignment: bool


async def get_user_display_name(db: AsyncSession, user_id: str, family_id: str) -> str:
    """Get user's display name in family context."""
    result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == family_id,
        )
    )
    membership = result.scalar_one_or_none()
    return membership.display_name if membership else "Unknown"


@router.get("/{event_id}")
async def get_gift_exchange(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get Gift Exchange info for an event."""
    await resolve_event_or_404(db, event_id, user)

    assignments = await ss_service.get_assignments(db, event_id)
    participants = await ss_service.get_participants(db, event_id, user.active_family_id)

    user_assignment = await ss_service.get_user_assignment(db, event_id, str(user.id))

    return {
        "event_id": event_id,
        "status": "assigned" if assignments else "not_assigned",
        "participant_count": len(participants),
        "has_assignment": user_assignment is not None,
    }


class AssignmentResponse(BaseModel):
    """Assignment response with giftee info."""

    giftee_id: str | None
    giftee_name: str | None
    wishlist: list[dict]


@router.get("/{event_id}/assignment")
async def get_assignment(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get current user's Gift Exchange assignment (who they give to)."""
    await resolve_event_or_404(db, event_id, user)

    assignment = await ss_service.get_user_assignment(db, event_id, str(user.id))

    if not assignment:
        return {"giftee_id": None, "giftee_name": None, "wishlist": []}

    # Get giftee's display name in this family
    giftee_name = await get_user_display_name(db, assignment.receiver_id, user.active_family_id)

    # Get giftee's wishlist
    wishlist_result = await db.execute(
        select(WishlistItem).where(WishlistItem.user_id == assignment.receiver_id)
    )
    wishlist_items = wishlist_result.scalars().all()

    return {
        "giftee_id": str(assignment.receiver_id),
        "giftee_name": giftee_name,
        "wishlist": [
            {
                "id": str(item.id),
                "name": item.name,
                "description": item.description,
                "url": item.url,
                "price_range": item.price_range,
                "priority": item.priority,
            }
            for item in wishlist_items
        ],
    }


@router.post("/{event_id}/run")
async def run_assignment(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Run the Gift Exchange assignment algorithm (family admin or event creator only)."""
    event = await resolve_event_or_404(db, event_id, user)

    can_manage = await permissions.can_manage_event(db, user, event)
    if not can_manage:
        raise HTTPException(
            status_code=403,
            detail="Only family admins or event creators can run Gift Exchange assignments",
        )

    result = await ss_service.run_assignments(db, event_id, user.active_family_id)

    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Unable to generate valid assignments. Check exclusion rules.",
        )

    return {"message": "Assignments created", "assignment_count": len(result)}


class ExclusionResponse(BaseModel):
    """Exclusion rule response."""

    id: str
    user1_id: str
    user1_name: str
    user2_id: str
    user2_name: str


@router.get("/{event_id}/exclusions")
async def list_exclusions(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List exclusion rules for Gift Exchange."""
    event = await resolve_event_or_404(db, event_id, user)

    can_manage = await permissions.can_manage_event(db, user, event)
    if not can_manage:
        raise HTTPException(
            status_code=403,
            detail="Only family admins or event creators can view exclusion rules",
        )

    exclusions = await ss_service.get_exclusions(db, event_id)

    result = []
    for ex in exclusions:
        # Get user display names
        giver_name = await get_user_display_name(db, ex.giver_id, user.active_family_id)
        receiver_name = await get_user_display_name(db, ex.receiver_id, user.active_family_id)

        result.append(
            {
                "id": str(ex.id),
                "user1_id": str(ex.giver_id),
                "user1_name": giver_name,
                "user2_id": str(ex.receiver_id),
                "user2_name": receiver_name,
            }
        )

    return {"exclusions": result}


class AddExclusionRequest(BaseModel):
    """Add exclusion request."""

    user1_id: str
    user2_id: str


@router.post("/{event_id}/exclusions")
async def add_exclusion(
    event_id: str,
    request: AddExclusionRequest,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Add an exclusion rule (family admin or event creator only)."""
    event = await resolve_event_or_404(db, event_id, user)

    can_manage = await permissions.can_manage_event(db, user, event)
    if not can_manage:
        raise HTTPException(
            status_code=403,
            detail="Only family admins or event creators can add exclusion rules",
        )

    if request.user1_id == request.user2_id:
        raise HTTPException(status_code=400, detail="Cannot exclude a user from themselves")

    # Verify both users are in this family
    for uid in [request.user1_id, request.user2_id]:
        membership_result = await db.execute(
            select(FamilyMembership).where(
                FamilyMembership.user_id == uid,
                FamilyMembership.family_id == user.active_family_id,
            )
        )
        if not membership_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"User {uid} is not a member of this family",
            )

    exclusion = await ss_service.add_exclusion(db, event_id, request.user1_id, request.user2_id)

    return {"message": "Exclusion added", "id": str(exclusion.id)}


@router.delete("/{event_id}/exclusions/{exclusion_id}")
async def remove_exclusion(
    event_id: str,
    exclusion_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Remove an exclusion rule (family admin or event creator only)."""
    event = await resolve_event_or_404(db, event_id, user)

    can_manage = await permissions.can_manage_event(db, user, event)
    if not can_manage:
        raise HTTPException(
            status_code=403,
            detail="Only family admins or event creators can remove exclusion rules",
        )

    success = await ss_service.remove_exclusion(db, exclusion_id)

    if not success:
        raise HTTPException(
            status_code=404, detail="Exclusion rule not found. It may have already been removed."
        )

    return {"message": "Exclusion removed"}


class SendMessageRequest(BaseModel):
    """Send anonymous message request."""

    content: str


@router.post("/{event_id}/message")
async def send_anonymous_message(
    event_id: str,
    request: SendMessageRequest,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Send an anonymous message to your Gift Exchange giftee."""
    await resolve_event_or_404(db, event_id, user)

    # Get user's assignment (who they give to)
    assignment = await ss_service.get_user_assignment(db, event_id, str(user.id))

    if not assignment:
        raise HTTPException(
            status_code=400, detail="You don't have a Gift Exchange assignment for this event yet"
        )

    await ss_service.send_message(
        db, event_id, str(user.id), str(assignment.receiver_id), request.content
    )

    return {"message": "Message sent"}


@router.get("/{event_id}/messages")
async def get_messages(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get anonymous messages for Gift Exchange (messages received from your match)."""
    await resolve_event_or_404(db, event_id, user)

    messages = await ss_service.get_received_messages(db, event_id, str(user.id))

    return {
        "messages": [
            {
                "id": str(msg.id),
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ]
    }


@router.get("/{event_id}/participants")
async def get_participants(
    event_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get list of participants for Gift Exchange."""
    await resolve_event_or_404(db, event_id, user)

    participants = await ss_service.get_participants(db, event_id, user.active_family_id)

    return {
        "participants": [
            {
                "id": str(u.id),
                "display_name": membership.display_name,
                "email": u.email,
            }
            for u, membership in participants
        ]
    }
