"""Auth-related schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class FamilyInfo(BaseModel):
    """Family basic info for listing."""

    id: str
    name: str
    family_code: str
    role: str  # admin or member

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """User response (public info)."""

    id: str
    email: str
    is_super_admin: bool
    theme: str
    big_mode: bool
    current_family_id: str | None = None
    families: list[FamilyInfo] = []

    model_config = ConfigDict(from_attributes=True)


class UserWithFamilyContext(BaseModel):
    """User response with current family context."""

    id: str
    email: str
    is_super_admin: bool
    theme: str
    big_mode: bool
    current_family_id: str | None = None
    current_family_name: str | None = None
    display_name: str | None = None  # Name in current family
    role_in_family: str | None = None  # admin/member in current family
    families: list[FamilyInfo] = []

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """Email + password login."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Register with family code."""

    family_code: str
    email: EmailStr
    password: str = Field(min_length=6)
    display_name: str


class ForgotPasswordRequest(BaseModel):
    """Request password reset."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password with magic link token."""

    token: str
    new_password: str = Field(min_length=6)


class SwitchFamilyRequest(BaseModel):
    """Switch active family context."""

    family_id: str


class SetupRequest(BaseModel):
    """Initial setup - create super admin + first family."""

    email: EmailStr
    password: str = Field(min_length=6)
    display_name: str
    family_name: str


class AdminFamilyInfo(BaseModel):
    """Family info for super admin listing (includes member count, no role)."""

    id: str
    name: str
    family_code: str
    member_count: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class AdminFamilyListResponse(BaseModel):
    """Response for GET /api/auth/families."""

    families: list[AdminFamilyInfo]


class DeleteFamilyResponse(BaseModel):
    """Response for successful family deletion."""

    message: str


class DeleteFamilyErrorResponse(BaseModel):
    """409 response when deletion would orphan users. Returned via JSONResponse."""

    detail: str
    orphaned_users: list[str]


class CreateFamilyRequest(BaseModel):
    """Create a new family (super admin only)."""

    name: str


class ChangePasswordRequest(BaseModel):
    """Change password (for logged-in user)."""

    current_password: str
    new_password: str = Field(min_length=6)


class AdminResetPasswordRequest(BaseModel):
    """Admin resetting another user's password."""

    user_id: str
    new_password: str = Field(min_length=6)


# Legacy schemas for backwards compatibility during transition
class MagicLinkRequest(BaseModel):
    """Request to send magic link (for password recovery)."""

    email: EmailStr


class MagicLinkVerify(BaseModel):
    """Verify magic link token."""

    token: str


# Keep for backwards compat
MemberResponse = UserResponse
OrganizerLogin = LoginRequest
JoinFamilyRequest = RegisterRequest
