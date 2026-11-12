"""Authentication and User Profile endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.api.deps import get_current_user
from backend.app.domain.auth.models import (
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefreshRequest,
    ChangePasswordRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication & Security"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate) -> UserResponse:
    """Register a new platform user with validated password strength."""
    return await AuthService.register_user(user_in)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin) -> TokenResponse:
    """Authenticate with username/email and password to receive JWT access and refresh tokens."""
    user = await AuthService.authenticate_user(
        username_or_email=credentials.username_or_email,
        password=credentials.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthService.create_user_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: TokenRefreshRequest) -> TokenResponse:
    """Exchange a valid refresh token for a fresh access and refresh token pair."""
    return await AuthService.refresh_user_tokens(payload.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve profile and role information for currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Change current authenticated user's password."""
    await AuthService.change_password(
        user=current_user,
        old_password=payload.old_password,
        new_password=payload.new_password,
    )
    return {"detail": "Password successfully updated."}


@router.post("/forgot-password")
async def forgot_password(payload: PasswordResetRequest) -> Dict[str, Any]:
    """
    Request password reset token. In production this would be dispatched via email;
    for testing and programmatic integration, the token is returned in the payload.
    """
    token = await AuthService.generate_reset_token(payload.email)
    return {
        "detail": "Password reset token generated. Use this token with /auth/reset-password.",
        "reset_token": token,
    }


@router.post("/reset-password")
async def reset_password(payload: PasswordResetConfirm) -> Dict[str, str]:
    """Reset password using verified password reset token."""
    await AuthService.reset_password_with_token(
        token=payload.token,
        new_password=payload.new_password,
    )
    return {"detail": "Password successfully reset. You may now log in with your new credentials."}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)) -> Dict[str, str]:
    """Logout endpoint to acknowledge session termination and trigger client token purge."""
    return {"detail": f"Successfully logged out user '{current_user.username}'."}

