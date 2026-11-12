"""Domain models and schemas for User authentication, RBAC, and credentials."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator


class UserRole(str, Enum):
    """Role-Based Access Control roles."""
    ADMIN = "admin"
    RESEARCHER = "researcher"
    USER = "user"


class User(BaseModel):
    """User domain entity representation."""
    id: str
    email: str
    username: str
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(BaseModel):
    """Registration schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = UserRole.USER

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(char.isdigit() or not char.isalnum() for char in v):
            raise ValueError("Password must contain at least one digit or special character.")
        return v


class UserLogin(BaseModel):
    """Login schema supporting username or email."""
    username_or_email: str
    password: str


class UserResponse(BaseModel):
    """Safe public user response schema (excluding password hash)."""
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT Token exchange response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    """Token refresh schema."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Password update schema."""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(char.isdigit() or not char.isalnum() for char in v):
            raise ValueError("Password must contain at least one digit or special character.")
        return v


class PasswordResetRequest(BaseModel):
    """Forgot password request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset token submission schema."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_reset_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(char.isdigit() or not char.isalnum() for char in v):
            raise ValueError("Password must contain at least one digit or special character.")
        return v

