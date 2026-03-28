"""User profile API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db import get_db_session
from app.models import ProfileVisibility, User, UserProfile

router = APIRouter()


class ProfileResponse(BaseModel):
    """User profile response."""

    phone: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    allergies: str | None = None
    dietary_restrictions: str | None = None
    medical_needs: str | None = None
    mobility_notes: str | None = None
    share_health_info: bool = False

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    """Update profile request."""

    phone: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    allergies: str | None = None
    dietary_restrictions: str | None = None
    medical_needs: str | None = None
    mobility_notes: str | None = None
    share_health_info: bool | None = None


class VisibilityResponse(BaseModel):
    """Profile visibility settings."""

    show_email: bool = True
    show_phone: bool = True
    show_address: bool = True

    model_config = ConfigDict(from_attributes=True)


class VisibilityUpdate(BaseModel):
    """Update visibility settings."""

    show_email: bool | None = None
    show_phone: bool | None = None
    show_address: bool | None = None


@router.get("")
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get current user's profile."""
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()

    if not profile:
        # Create empty profile if doesn't exist
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return ProfileResponse.model_validate(profile)


@router.put("")
async def update_profile(
    request: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update current user's profile."""
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    # Update fields if provided
    if request.phone is not None:
        profile.phone = request.phone
    if request.address_line1 is not None:
        profile.address_line1 = request.address_line1
    if request.address_line2 is not None:
        profile.address_line2 = request.address_line2
    if request.city is not None:
        profile.city = request.city
    if request.state is not None:
        profile.state = request.state
    if request.zip_code is not None:
        profile.zip_code = request.zip_code
    if request.country is not None:
        profile.country = request.country
    if request.allergies is not None:
        profile.allergies = request.allergies
    if request.dietary_restrictions is not None:
        profile.dietary_restrictions = request.dietary_restrictions
    if request.medical_needs is not None:
        profile.medical_needs = request.medical_needs
    if request.mobility_notes is not None:
        profile.mobility_notes = request.mobility_notes
    if request.share_health_info is not None:
        profile.share_health_info = request.share_health_info

    await db.commit()

    return {"message": "Profile updated"}


@router.get("/visibility/{family_id}")
async def get_visibility(
    family_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get visibility settings for a specific family."""
    result = await db.execute(
        select(ProfileVisibility).where(
            ProfileVisibility.user_id == user.id,
            ProfileVisibility.family_id == family_id,
        )
    )
    visibility = result.scalar_one_or_none()

    if not visibility:
        # Return defaults if not set
        return VisibilityResponse()

    return VisibilityResponse.model_validate(visibility)


@router.put("/visibility/{family_id}")
async def update_visibility(
    family_id: str,
    request: VisibilityUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update visibility settings for a specific family."""
    # Verify user is in this family
    from app.services import auth as auth_service

    membership = await auth_service.get_user_membership(db, user.id, family_id)
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this family",
        )

    result = await db.execute(
        select(ProfileVisibility).where(
            ProfileVisibility.user_id == user.id,
            ProfileVisibility.family_id == family_id,
        )
    )
    visibility = result.scalar_one_or_none()

    if not visibility:
        visibility = ProfileVisibility(
            user_id=user.id,
            family_id=family_id,
        )
        db.add(visibility)

    if request.show_email is not None:
        visibility.show_email = request.show_email
    if request.show_phone is not None:
        visibility.show_phone = request.show_phone
    if request.show_address is not None:
        visibility.show_address = request.show_address

    await db.commit()

    return {"message": "Visibility settings updated"}


@router.get("/health-info")
async def get_health_info(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get health-related profile info (allergies, medical needs)."""
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()

    if not profile:
        return {
            "allergies": None,
            "dietary_restrictions": None,
            "medical_needs": None,
            "mobility_notes": None,
        }

    return {
        "allergies": profile.allergies,
        "dietary_restrictions": profile.dietary_restrictions,
        "medical_needs": profile.medical_needs,
        "mobility_notes": profile.mobility_notes,
    }
