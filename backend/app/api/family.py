"""Family members API endpoints - multi-family aware."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_family_admin, require_family_context
from app.db import get_db_session
from app.models import FamilyMembership, FamilyRole, ProfileVisibility, User, UserProfile
from app.services import auth as auth_service
from app.services.email import get_smtp_config, send_family_invitation_email
from app.services.permissions import permissions

router = APIRouter()


class MemberResponse(BaseModel):
    """Member info within a family context."""

    user_id: str
    display_name: str
    email: str | None = None  # Only shown if visibility allows
    role: str
    # Profile fields (shown based on visibility)
    phone: str | None = None
    address: str | None = None

    class Config:
        from_attributes = True


async def get_member_with_visibility(
    db: AsyncSession,
    membership: FamilyMembership,
    viewer: User,
    include_contact: bool = True,
) -> dict:
    """Get member info respecting visibility settings."""
    # Get user profile
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == membership.user_id)
    )
    profile = profile_result.scalar_one_or_none()

    # Get visibility settings for this family
    visibility_result = await db.execute(
        select(ProfileVisibility).where(
            ProfileVisibility.user_id == membership.user_id,
            ProfileVisibility.family_id == membership.family_id,
        )
    )
    visibility = visibility_result.scalar_one_or_none()

    # Get user email
    user_result = await db.execute(select(User).where(User.id == membership.user_id))
    user = user_result.scalar_one_or_none()

    result = {
        "user_id": membership.user_id,
        "display_name": membership.display_name,
        "role": membership.role.value,
    }

    if include_contact and visibility:
        # Include email if visibility allows (or if viewing self)
        if visibility.show_email or membership.user_id == viewer.id:
            result["email"] = user.email if user else None

        if profile:
            # Include phone if visibility allows
            if visibility.show_phone or membership.user_id == viewer.id:
                result["phone"] = profile.phone

            # Include address if visibility allows
            if visibility.show_address or membership.user_id == viewer.id:
                # Build city/state/zip line only if we have data
                city_state_zip = None
                if profile.city or profile.state or profile.zip_code:
                    parts = [profile.city, profile.state]
                    city_state = ", ".join(filter(None, parts))
                    if city_state and profile.zip_code:
                        city_state_zip = f"{city_state} {profile.zip_code}"
                    elif city_state:
                        city_state_zip = city_state
                    elif profile.zip_code:
                        city_state_zip = profile.zip_code

                address_parts = [
                    profile.address_line1,
                    profile.address_line2,
                    city_state_zip,
                    profile.country,
                ]
                result["address"] = ", ".join(filter(None, address_parts)) or None

    return result


@router.get("/members")
async def list_members(
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """List all members in current family."""
    result = await db.execute(
        select(FamilyMembership)
        .where(FamilyMembership.family_id == user.current_family_id)
        .order_by(FamilyMembership.display_name)
    )
    memberships = result.scalars().all()

    members = []
    for membership in memberships:
        member_data = await get_member_with_visibility(db, membership, user)
        members.append(member_data)

    return {"members": members}


@router.get("/members/{user_id}")
async def get_member(
    user_id: str,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a specific family member."""
    result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == user.current_family_id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=404,
            detail="Family member not found. They may have been removed.",
        )

    return await get_member_with_visibility(db, membership, user)


@router.get("/address-book")
async def get_address_book(
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get family address book with contact info (respects visibility)."""
    result = await db.execute(
        select(FamilyMembership)
        .where(FamilyMembership.family_id == user.current_family_id)
        .order_by(FamilyMembership.display_name)
    )
    memberships = result.scalars().all()

    members = []
    for membership in memberships:
        member_data = await get_member_with_visibility(db, membership, user, include_contact=True)
        members.append(member_data)

    return {"members": members}


class InviteRequest(BaseModel):
    """Invite member request."""

    display_name: str
    email: EmailStr


@router.post("/invite")
async def invite_member(
    request: InviteRequest,
    req: Request,
    admin: User = Depends(require_family_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Invite a new member to the family (admin only)."""
    # Check if user already exists
    existing_user = await auth_service.get_user_by_email(db, request.email)

    if existing_user:
        # Check if already in this family
        membership = await auth_service.get_user_membership(
            db, existing_user.id, admin.current_family_id
        )
        if membership:
            raise HTTPException(
                status_code=400,
                detail="This person is already a member of this family",
            )

        # Add existing user to family
        family = await auth_service.get_family_by_id(db, admin.current_family_id)
        await auth_service.add_user_to_family(db, existing_user, family, request.display_name)

        return {
            "message": f"{request.display_name} has been added to the family",
            "user_id": existing_user.id,
        }
    else:
        # Get family info for invitation
        family = await auth_service.get_family_by_id(db, admin.current_family_id)

        # Get admin's display name in this family
        admin_membership = await auth_service.get_user_membership(
            db, admin.id, admin.current_family_id
        )
        inviter_name = admin_membership.display_name if admin_membership else "A family admin"

        # Get base URL from request
        base_url = str(req.base_url).rstrip("/")

        # Check if SMTP is configured and send email
        smtp_config = await get_smtp_config(db)
        email_sent = False

        if smtp_config.is_configured:
            email_sent = await send_family_invitation_email(
                db=db,
                to_email=request.email,
                inviter_name=inviter_name,
                family_name=family.name,
                family_code=family.family_code,
                base_url=base_url,
            )

        if email_sent:
            return {
                "message": f"Invitation sent to {request.email}",
                "email": request.email,
            }
        else:
            # SMTP not configured - return code for manual sharing
            return {
                "message": f"Share the family code with {request.display_name} to join",
                "family_code": family.family_code,
                "email": request.email,
            }


@router.delete("/members/{user_id}")
async def remove_member(
    user_id: str,
    admin: User = Depends(require_family_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Remove a member from the family (admin only)."""
    if admin.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot remove yourself from the family",
        )

    result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == admin.current_family_id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=404,
            detail="Family member not found. They may have already been removed.",
        )

    # Check if this is the last admin
    if membership.role == FamilyRole.ADMIN:
        admin_count_result = await db.execute(
            select(FamilyMembership).where(
                FamilyMembership.family_id == admin.current_family_id,
                FamilyMembership.role == FamilyRole.ADMIN,
            )
        )
        admins = admin_count_result.scalars().all()
        if len(admins) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove the last admin from a family",
            )

    display_name = membership.display_name

    # Also remove visibility settings
    visibility_result = await db.execute(
        select(ProfileVisibility).where(
            ProfileVisibility.user_id == user_id,
            ProfileVisibility.family_id == admin.current_family_id,
        )
    )
    visibility = visibility_result.scalar_one_or_none()
    if visibility:
        await db.delete(visibility)

    await db.delete(membership)
    await db.commit()

    return {"message": f"{display_name} has been removed from the family"}


class RoleUpdate(BaseModel):
    """Update member role."""

    role: str  # admin or member


@router.post("/members/{user_id}/role")
async def update_member_role(
    user_id: str,
    request: RoleUpdate,
    admin: User = Depends(require_family_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Change a member's role (admin only)."""
    try:
        new_role = FamilyRole(request.role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid role. Use 'admin' or 'member'",
        )

    result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == admin.current_family_id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=404,
            detail="Family member not found. They may have been removed.",
        )

    # Prevent removing your own admin status if you're the last admin
    if admin.id == user_id and new_role == FamilyRole.MEMBER:
        admin_count_result = await db.execute(
            select(FamilyMembership).where(
                FamilyMembership.family_id == admin.current_family_id,
                FamilyMembership.role == FamilyRole.ADMIN,
            )
        )
        admins = admin_count_result.scalars().all()
        if len(admins) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove the last admin from a family",
            )

    membership.role = new_role
    await db.commit()

    return {"message": f"Role updated to {new_role.value} for {membership.display_name}"}


class DisplayNameUpdate(BaseModel):
    """Update display name in family."""

    display_name: str


@router.put("/members/{user_id}/display-name")
async def update_display_name(
    user_id: str,
    request: DisplayNameUpdate,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Update display name (self or admin)."""
    result = await db.execute(
        select(FamilyMembership).where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == user.current_family_id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=404,
            detail="Family member not found. They may have been removed.",
        )

    # Can only update own name, or if admin
    if user.id != user_id:
        is_admin = await permissions.is_family_admin(db, user, user.current_family_id)
        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="You can only update your own display name",
            )

    membership.display_name = request.display_name
    await db.commit()

    return {"message": "Display name updated"}
