"""Authentication endpoints - login, register, password management."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.models import FamilyRole, User
from app.schemas.auth import (
    AdminResetPasswordRequest,
    ChangePasswordRequest,
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


# ============ Dependencies ============


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependency to get current authenticated user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Please log in to continue")

    user = await auth_service.get_user_by_session(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User | None:
    """Dependency to optionally get current user (no error if not authenticated)."""
    if not credentials:
        return None

    return await auth_service.get_user_by_session(db, credentials.credentials)


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

    membership = await auth_service.get_user_membership(db, user.id, user.current_family_id)
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
    """Build user response with family context."""
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
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current authenticated user with family context."""
    return build_user_response(user)


@router.post("/login")
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Login with email and password."""
    user = await auth_service.verify_password(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "session_token": user.session_token,
        "user": build_user_response(user),
    }


@router.post("/register")
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Register with a family code."""
    user, error = await auth_service.register_with_family_code(
        db,
        request.family_code,
        request.email,
        request.password,
        request.display_name,
    )

    if error:
        raise HTTPException(status_code=400, detail=error)

    return {
        "message": "Welcome to the family!",
        "session_token": user.session_token,
        "user": build_user_response(user),
    }


@router.post("/logout")
async def logout(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Logout current user."""
    await auth_service.logout(db, user)
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

    # Refresh user to get updated context
    user = await auth_service.get_user_by_id(db, user.id)

    return {
        "message": f"Switched to {membership.family.name}",
        "user": build_user_response(user),
    }


# ============ Password Management ============


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Request password reset email."""
    token = await auth_service.create_magic_link(db, request.email)

    # Always return success to prevent email enumeration
    response = {
        "message": f"If an account exists for {request.email}, a password reset link has been sent.",
    }

    if token:
        # Get base URL from request
        base_url = str(req.base_url).rstrip("/")

        # Check if SMTP is configured
        smtp_config = await get_smtp_config(db)

        if smtp_config.is_configured:
            # Send actual email
            await send_password_reset_email(
                db=db,
                to_email=request.email,
                reset_token=token,
                base_url=base_url,
            )
        else:
            # Development mode - return token directly
            response["dev_token"] = token

    return response


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Reset password using magic link token."""
    user = await auth_service.verify_magic_token_and_reset_password(
        db, request.token, request.new_password
    )
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset link",
        )

    return {
        "message": "Password reset successfully",
        "session_token": user.session_token,
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
            db, target_user.id, admin.current_family_id
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
    db: AsyncSession = Depends(get_db_session),
):
    """
    Initial platform setup - creates super admin and first family.
    Only works if no super admins exist.
    """
    needs_setup = await auth_service.check_needs_setup(db)
    if not needs_setup:
        raise HTTPException(
            status_code=400,
            detail="Setup already complete. Use normal login.",
        )

    try:
        user, family = await auth_service.initial_setup(
            db,
            request.email,
            request.password,
            request.display_name,
            request.family_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "message": "Setup complete! Welcome to FamilyCircle.",
        "session_token": user.session_token,
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
    request: dict,
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new family (super admin only).

    The creating user is automatically added as admin of the new family.
    """
    name = request.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Family name is required")

    display_name = request.get("display_name", "Admin")

    # Create the family
    family = await auth_service.create_family(db, name)

    # Add the creator as admin of the new family
    await auth_service.add_user_to_family(db, admin, family, display_name, FamilyRole.ADMIN)

    return {
        "message": f"Family '{name}' created successfully",
        "family": {
            "id": family.id,
            "name": family.name,
            "family_code": family.family_code,
        },
    }


@router.get("/families")
async def list_families(
    admin: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """List all families (super admin only)."""
    from sqlalchemy import select

    from app.models import Family

    result = await db.execute(select(Family).order_by(Family.name))
    families = result.scalars().all()

    return {
        "families": [
            {
                "id": f.id,
                "name": f.name,
                "family_code": f.family_code,
                "created_at": f.created_at.isoformat(),
            }
            for f in families
        ]
    }


# ============ Family Code (for family admins) ============


@router.get("/family-code")
async def get_family_code(
    user: User = Depends(require_family_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Get family code for current family (admins only)."""
    family = await auth_service.get_family_by_id(db, user.current_family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    return {"code": family.family_code}


@router.post("/family-code/regenerate")
async def regenerate_family_code(
    user: User = Depends(require_family_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """Regenerate family code (admins only)."""
    family = await auth_service.get_family_by_id(db, user.current_family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Generate new unique code
    new_code = auth_service.generate_family_code()
    while await auth_service.get_family_by_code(db, new_code):
        new_code = auth_service.generate_family_code()

    family.family_code = new_code
    await db.commit()

    return {
        "message": "Family code regenerated",
        "code": new_code,
    }


# ============ Backwards Compatibility ============


# Keep old endpoint for magic link (now used for password recovery)
@router.post("/magic-link")
async def send_magic_link(
    request: ForgotPasswordRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Send a magic link for password recovery (backwards compat)."""
    return await forgot_password(request, req, db)


# Alias for backwards compatibility
get_current_member = get_current_user
