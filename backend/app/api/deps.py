"""FastAPI authentication, authorization, and tenancy dependencies."""

from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.core.security import decode_token
from backend.app.domain.auth.models import User, UserRole
from backend.app.services.auth_service import AuthService

# HTTP Bearer scheme allowing optional or strict token extraction
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> User:
    """
    Strict dependency: enforces presence of valid Bearer access token.
    Raises 401 Unauthorized if missing, expired, or malformed.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload missing user identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await AuthService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[User]:
    """
    Optional dependency: returns User if valid Bearer token provided, None otherwise.
    Never raises 401 if token is absent, but will raise if a malformed token is provided.
    """
    if not credentials or not credentials.credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_role(allowed_roles: List[UserRole]) -> Callable:
    """Factory creating an authorization dependency enforcing specific RBAC roles."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role in {[r.value for r in allowed_roles]}, but user has role '{current_user.role.value}'.",
            )
        return current_user
    return role_checker


def verify_resource_ownership(
    resource_owner_id: Optional[str],
    current_user: User,
    resource_name: str = "resource",
) -> None:
    """
    Enforce resource tenancy.
    Administrators have global bypass; regular users can only access/modify their own resources.
    """
    if current_user.role == UserRole.ADMIN:
        return
    if not resource_owner_id:
        # Unowned resource or legacy default
        return
    if resource_owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to modify or delete this {resource_name}.",
        )

