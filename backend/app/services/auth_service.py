"""Authentication and User Management Service."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    decode_token,
)
from backend.app.db.mongodb import db_manager
from backend.app.domain.auth.models import (
    User,
    UserRole,
    UserCreate,
    UserResponse,
    TokenResponse,
)


class AuthService:
    """Manages user registration, authentication, RBAC, and credentials."""

    COLLECTION_NAME = "users"

    @classmethod
    async def get_user_by_id(cls, user_id: str) -> Optional[User]:
        """Fetch user by primary ID."""
        if db_manager.is_connected and db_manager.db is not None:
            doc = await db_manager.db[cls.COLLECTION_NAME].find_one({"id": user_id})
        else:
            doc = db_manager.memory_get(cls.COLLECTION_NAME, user_id)
        if doc:
            return User(**doc)
        return None

    @classmethod
    async def get_user_by_username_or_email(cls, identifier: str) -> Optional[User]:
        """Look up user by username or email (case-insensitive)."""
        ident_lower = identifier.strip().lower()
        if db_manager.is_connected and db_manager.db is not None:
            doc = await db_manager.db[cls.COLLECTION_NAME].find_one({
                "$or": [
                    {"email": ident_lower},
                    {"username": ident_lower},
                ]
            })
            if doc:
                return User(**doc)
        else:
            all_users = db_manager.memory_list(cls.COLLECTION_NAME)
            for u in all_users:
                if u.get("email", "").lower() == ident_lower or u.get("username", "").lower() == ident_lower:
                    return User(**u)
        return None

    @classmethod
    async def register_user(cls, user_in: UserCreate) -> UserResponse:
        """Register a new user after verifying unique email and username."""
        email_clean = user_in.email.strip().lower()
        username_clean = user_in.username.strip().lower()

        existing_user = await cls.get_user_by_username_or_email(email_clean)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        existing_user_by_name = await cls.get_user_by_username_or_email(username_clean)
        if existing_user_by_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists.",
            )

        user_id = str(uuid.uuid4())
        hashed_pw = get_password_hash(user_in.password)
        now = datetime.now(timezone.utc)

        user = User(
            id=user_id,
            email=email_clean,
            username=username_clean,
            hashed_password=hashed_pw,
            full_name=user_in.full_name,
            role=user_in.role or UserRole.USER,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        user_dict = user.model_dump()
        if db_manager.is_connected and db_manager.db is not None:
            await db_manager.db[cls.COLLECTION_NAME].insert_one(user_dict)
        else:
            db_manager.memory_insert(cls.COLLECTION_NAME, user_id, user_dict)

        logger.info(f"Registered user '{user.username}' with role '{user.role.value}' [id={user.id}]")
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    @classmethod
    async def authenticate_user(cls, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password."""
        user = await cls.get_user_by_username_or_email(username_or_email)
        if not user:
            return None
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated. Please contact support.",
            )
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    def create_user_tokens(cls, user: User) -> TokenResponse:
        """Issue access and refresh token pair for authenticated user."""
        token_payload = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
        }
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
            ),
        )

    @classmethod
    async def refresh_user_tokens(cls, refresh_token: str) -> TokenResponse:
        """Exchange valid refresh token for a new access and refresh token pair."""
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type. Expected a refresh token.",
            )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject identifier.",
            )
        user = await cls.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User associated with token no longer exists.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account has been deactivated.",
            )
        return cls.create_user_tokens(user)

    @classmethod
    async def change_password(cls, user: User, old_password: str, new_password: str) -> bool:
        """Verify old password and update to new password."""
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password provided.",
            )
        new_hashed = get_password_hash(new_password)
        now = datetime.now(timezone.utc)

        if db_manager.is_connected and db_manager.db is not None:
            await db_manager.db[cls.COLLECTION_NAME].update_one(
                {"id": user.id},
                {"$set": {"hashed_password": new_hashed, "updated_at": now}},
            )
        else:
            rec = db_manager.memory_get(cls.COLLECTION_NAME, user.id)
            if rec:
                rec["hashed_password"] = new_hashed
                rec["updated_at"] = now
                db_manager.memory_insert(cls.COLLECTION_NAME, user.id, rec)
        logger.info(f"Password successfully changed for user '{user.username}'")
        return True

    @classmethod
    async def generate_reset_token(cls, email: str) -> str:
        """Generate token for forgotten password reset."""
        email_clean = email.strip().lower()
        user = await cls.get_user_by_username_or_email(email_clean)
        if not user:
            # Mask user existence to prevent user enumeration
            logger.info(f"Password reset requested for non-existent email '{email_clean}'")
            return create_password_reset_token(email_clean)
        return create_password_reset_token(user.email)

    @classmethod
    async def reset_password_with_token(cls, token: str, new_password: str) -> bool:
        """Reset user password using verified password reset token."""
        payload = decode_token(token)
        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type. Expected password reset token.",
            )
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token missing subject email.",
            )
        user = await cls.get_user_by_username_or_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account associated with reset token was not found.",
            )
        new_hashed = get_password_hash(new_password)
        now = datetime.now(timezone.utc)

        if db_manager.is_connected and db_manager.db is not None:
            await db_manager.db[cls.COLLECTION_NAME].update_one(
                {"id": user.id},
                {"$set": {"hashed_password": new_hashed, "updated_at": now}},
            )
        else:
            rec = db_manager.memory_get(cls.COLLECTION_NAME, user.id)
            if rec:
                rec["hashed_password"] = new_hashed
                rec["updated_at"] = now
                db_manager.memory_insert(cls.COLLECTION_NAME, user.id, rec)
        logger.info(f"Password successfully reset via token for user '{user.username}'")
        return True

    @classmethod
    async def seed_default_admin_if_needed(cls) -> Optional[User]:
        """Seed default admin account if users collection is empty."""
        admin = await cls.get_user_by_username_or_email(settings.DEFAULT_ADMIN_USERNAME)
        if admin:
            return admin
        try:
            admin_create = UserCreate(
                email=settings.DEFAULT_ADMIN_EMAIL,
                username=settings.DEFAULT_ADMIN_USERNAME,
                password=settings.DEFAULT_ADMIN_PASSWORD,
                full_name="Platform Administrator",
                role=UserRole.ADMIN,
            )
            admin_resp = await cls.register_user(admin_create)
            logger.info(f"Default platform admin account seeded: {admin_resp.username}")
            return await cls.get_user_by_id(admin_resp.id)
        except Exception as e:
            logger.warning(f"Could not seed default admin: {e}")
            return None

