"""Authentication endpoints - login, register, password management."""

import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_base_url
from app.constants import SESSION_COOKIE_MAX_AGE_SECONDS
from app.db import get_db_session
from app.models import Family, FamilyMembership, FamilyRole, User
from app.rate_limit import limiter
from app.schemas.auth import (
    AdminFamilyListResponse,
    AdminResetPasswordRequest,
    ChangePasswordRequest,
    CreateFamilyRequest,
    DeleteFamilyErrorResponse,
    DeleteFamilyResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SetupRequest,
    SwitchFamilyRequest,
    UserWithFamilyContext,
)
from app.services import auth as auth_service
from app.services.email import get_smtp_config, send_password_reset_email

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Cookie configuration (H5)
SESSION_COOKIE_NAME = "fc_session"
_IS_PRODUCTION = os.getenv("DEBUG", "").lower() not in ("true", "1", "yes")


def _set_session_cookie(response: Response, token: str) -> None:
    """Set httpOnly session cookie on the response."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=_IS_PRODUCTION,
        samesite="lax",
        max_age=SESSION_COOKIE_MAX_AGE_SECONDS,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    """Clear the session cookie."""
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=_IS_PRODUCTION,
        samesite="lax",
        path="/",
    )


# ============ Dependencies ============


def _extract_token(
    request: Request, credentials: HTTPAuthorizationCredentials | None
) -> str | None:
    """Extract session token from cookie (preferred) or Authorization header (fallback).

    H5: Cookie-first auth with bearer token fallback for non-browser clients.
    """
    # 1. httpOnly cookie (browser clients)
    cookie_token = request.cookies.get(SESSION_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    # 2. Authorization: Bearer header (API clients, scripts)
    if credentials:
        return credentials.credentials

    return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependency to get current authenticated user (lightweight — no family eager loading).

    H2: This is the default auth dependency. Most endpoints only need the user's
    identity and basic fields. Family memberships are NOT loaded here.

    H5: Checks httpOnly cookie first, falls back to Authorization header.
    """
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(status_code=401, detail="Please log in to continue")

    user = await auth_service.get_user_by_session(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User | None:
    """Dependency to optionally get current user (no error if not authenticated)."""
    token = _extract_token(request, credentials)
    if not token:
        return None

    return await auth_service.get_user_by_session(db, token)


async def require_family_context(
    user: User = Depends(get_current_user),
) -> User:
    """Require user to have an active family context."""
    if not user.current_family_id:
        raise HTTPException(
            status_code=400,
            detail="Please select a family first",
        )
    return user


async def require_family_admin(
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Require user to be admin of current family (or super admin)."""
    if user.is_super_admin:
        return user

    membership = await auth_service.get_user_membership(db, user.id, user.active_family_id)
    if not membership or membership.role != FamilyRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="You must be a family admin to perform this action",
        )
    return user


async def require_super_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Require user to be super admin."""
    if not user.is_super_admin:
        raise HTTPException(
            status_code=403,
            detail="Super admin access required",
        )
    return user


# ============ Helper Functions ============


def build_user_response(user: User) -> dict:
    """Build user response with family context.

    Caller contract: the User passed here MUST have been loaded with
    get_user_by_id_with_families() or get_user_by_email_with_families(),
    because this function walks user.family_memberships[].family.
    """
    context = auth_service.get_current_family_context(user)
    families = auth_service.get_user_families_info(user)

    return {
        "id": user.id,
        "email": user.email,
        "is_super_admin": user.is_super_admin,
        "theme": user.theme,
        "big_mode": user.big_mode,
        "current_family_id": context["current_family_id"],
        "current_family_name": context["current_family_name"],
        "display_name": context["display_name"],
        "role_in_family": context["role_in_family"],
        "families": families,
    }


# ============ Auth Endpoints ============


@router.get("/me", response_model=UserWithFamilyContext)
async def get_current_user_info(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get current authenticated user with family context.

    H2: This endpoint needs family-loaded user for build_user_response().
    """
    refreshed = await auth_service.get_user_by_id_with_families(db, user.id)
    if not refreshed:
        raise HTTPException(status_code=404, detail="User not found")
    return build_user_response(refreshed)


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """Login with email and password."""
    user, session_token = await auth_service.verify_password(db, body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    _set_session_cookie(response, session_token)  # type: ignore[arg-type]  # guarded by if-not-user above
    return {
        "user": build_user_response(user),
    }


@router.post("/register")
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    """Register with a family code."""
    user, error, session_token = await auth_service.register_with_family_code(
        db,
        body.family_code,
        body.email,
        body.password,
        body.display_name,
    )

    if error:
        raise HTTPException(status_code=400, detail=error)

    # Notify family that a new member joined (user-initiated join)
    from app.services.notifications.fire import send_notification_background

    background_tasks.add_task(
        send_notification_background,
        "notify_family_member_joined",
        member_name=body.display_name,
        family_name=body.family_code,
    )

    _set_session_cookie(response, session_token)  # type: ignore[arg-type]  # guarded by if-error above
    return {
        "message": "Welcome to the family!",
        "user": build_user_response(user),  # type: ignore[arg-type]  # guarded by if-error above
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Logout current user.

    H5: Deletes token from Token table and clears httpOnly cookie.
    """
    token = _extract_token(request, credentials)
    if token:
        await auth_service.logout(db, token)
    _clear_session_cookie(response)
    return {"message": "Logged out successfully"}


@router.post("/switch-family")
async def switch_family(
    request: SwitchFamilyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Switch active family context."""
    membership = await auth_service.switch_family(db, user, request.family_id)
    if not membership:
        raise HTTPException(
            status_code=400,
            detail="You are not a member of this family",
        )

    # Re-fetch with families for build_user_response
    refreshed = await auth_service.get_user_by_id_with_families(db, user.id)
    if not refreshed:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": f"Switched to {membership.family.name}",
        "user": build_user_response(refreshed),
    }


# ============ Password Management ============


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Request password reset email."""
    result = await auth_service.create_magic_link(db, body.email)

    # Always return success to prevent email enumeration
    response = {
        "message": f"If an account exists for {body.email}, a password reset link has been sent.",
    }

    if result:
        token, expiry_days = result
        base_url = get_base_url(request)

        # Check if SMTP is configured
        smtp_config = await get_smtp_config(db)

        if smtp_config.is_configured:
            # Send actual email
            await send_password_reset_email(
                db=db,
                to_email=body.email,
                reset_token=token,
                base_url=base_url,
                expiry_days=expiry_days,
            )
        elif not _IS_PRODUCTION:
            # Development mode only - return token directly
            response["dev_token"] = token

    return response


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """Reset password using magic link token."""
    user, session_token = await auth_service.verify_magic_token_and_reset_password(
        db, request.token, request.new_password
    )
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset link",
        )

    _set_session_cookie(response, session_token)  # type: ignore[arg-type]  # guarded by if-not-user above
    return {
        "message": "Password reset successfully",
        "user": build_user_response(user),
    }


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Change password (requires current password)."""
    success = await auth_service.change_password(
        db, user, request.current_password, request.new_password
    )
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect",
        )

    return {"message": "Password changed successfully"}


@router.post("/admin/reset-password")
async def admin_reset_password(
    request: AdminResetPasswordRequest,
    admin: User = Depends(require_family_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Reset another user's password (admin only)."""
    target_user = await auth_service.get_user_by_id(db, request.user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # If not super admin, verify target is in same family
    if not admin.is_super_admin:
        target_membership = await auth_service.get_user_membership(
            db, target_user.id, admin.active_family_id
        )
        if not target_membership:
            raise HTTPException(
                status_code=403,
                detail="You can only reset passwords for members of your family",
            )

    await auth_service.set_password(db, target_user, request.new_password)

    return {"message": "Password reset successfully"}


# ============ Setup ============


@router.get("/setup-status")
async def get_setup_status(db: AsyncSession = Depends(get_db_session)):
    """Check if initial setup is needed (no super admins exist)."""
    needs_setup = await auth_service.check_needs_setup(db)
    return {"needs_setup": needs_setup}


@router.post("/setup")
async def initial_setup(
    request: SetupRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """Initial platform setup - creates super admin and first family.

    Only works if no super admins exist.
    """
    needs_setup = await auth_service.check_needs_setup(db)
    if not needs_setup:
        raise HTTPException(
            status_code=400,
            detail="Setup already complete. Use normal login.",
        )

    try:
        user, family, session_token = await auth_service.initial_setup(
            db,
            request.email,
            request.password,
            request.display_name,
            request.family_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    _set_session_cookie(response, session_token)
    return {
        "message": "Setup complete! Welcome to FamilyCircle.",
        "user": build_user_response(user),
        "family": {
            "id": family.id,
            "name": family.name,
            "family_code": family.family_code,
        },
    }


# ============ Family Management (Super Admin) ============


@router.post("/families")
async def create_family(
    request: CreateFamilyRequest,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new family (super admin only).

    The creating user is automatically added as admin of the new family.
    """
    # Create the family
    family = await auth_service.create_family(db, request.name)

    # Add the creator as admin of the new family
    await auth_service.add_user_to_family(db, admin, family, request.display_name, FamilyRole.ADMIN)

    return {
        "message": f"Family '{request.name}' created successfully",
        "family": {
            "id": family.id,
            "name": family.name,
            "family_code": family.family_code,
        },
    }


@router.get("/families", response_model=AdminFamilyListResponse)
async def list_families(
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """List all families with member counts (super admin only)."""
    stmt = (
        select(
            Family.id,
            Family.name,
            Family.family_code,
            Family.created_at,
            func.count(FamilyMembership.id).label("member_count"),
        )
        .outerjoin(FamilyMembership, Family.id == FamilyMembership.family_id)
        .group_by(Family.id, Family.name, Family.family_code, Family.created_at)
        .order_by(Family.name)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return {
        "families": [
            {
                "id": row.id,
                "name": row.name,
                "family_code": row.family_code,
                "member_count": row.member_count,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.delete(
    "/families/{family_id}",
    response_model=DeleteFamilyResponse,
    responses={409: {"model": DeleteFamilyErrorResponse}},
)
async def delete_family(
    family_id: str,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a family and all associated data (super admin only).

    Returns 409 if any users would be orphaned (left with no family).
    """
    try:
        family_name, orphaned_emails = await auth_service.delete_family(db, family_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Family not found")

    if orphaned_emails is not None:
        return JSONResponse(
            status_code=409,
            content={
                "detail": (
                    f"Cannot delete '{family_name}': {len(orphaned_emails)} user(s) "
                    f"belong only to this family and would be orphaned."
                ),
                "orphaned_users": orphaned_emails,
            },
        )

    return {"message": f"Family '{family_name}' deleted successfully"}


# ============ Family Code (for family admins) ============


@router.get("/family-code")
async def get_family_code(
    user: User = Depends(require_family_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Get family code for current family (admins only)."""
    family = await auth_service.get_family_by_id(db, user.active_family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    return {"code": family.family_code}


@router.post("/family-code/regenerate")
async def regenerate_family_code(
    user: User = Depends(require_family_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Regenerate family code (admins only)."""
    family = await auth_service.get_family_by_id(db, user.active_family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Generate new unique code
    new_code = auth_service.generate_family_code()
    while await auth_service.get_family_by_code(db, new_code):
        new_code = auth_service.generate_family_code()

    family.family_code = new_code

    return {
        "message": "Family code regenerated",
        "code": new_code,
    }


# ============ Backwards Compatibility ============


# Keep old endpoint for magic link (now used for password recovery)
@router.post("/magic-link")
@limiter.limit("3/minute")
async def send_magic_link(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Send a magic link for password recovery (backwards compat)."""
    return await forgot_password(request=request, body=body, db=db)


# Alias for backwards compatibility
get_current_member = get_current_user
