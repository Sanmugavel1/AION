"""
AION FastAPI Dependency Injection
"""
from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.core.logging import get_logger
from app.core.security import Permission, UserRole, decode_token, require_permission

logger = get_logger(__name__)

security = HTTPBearer()


class CurrentUser:
    def __init__(
        self,
        user_id: str,
        org_id: str,
        email: str,
        role: UserRole,
        permissions: list[str],
    ) -> None:
        self.user_id = user_id
        self.org_id = org_id
        self.email = email
        self.role = role
        self.permissions = permissions


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> CurrentUser:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        return CurrentUser(
            user_id=payload["sub"],
            org_id=payload["org_id"],
            email=payload.get("email", ""),
            role=UserRole(payload["role"]),
            permissions=payload.get("permissions", []),
        )
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    return current_user


def require_roles(*roles: UserRole):
    async def _check(
        current_user: Annotated[CurrentUser, Depends(get_current_user)]
    ) -> CurrentUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {[r.value for r in roles]}",
            )
        return current_user
    return _check


def require_perm(permission: Permission):
    async def _check(
        current_user: Annotated[CurrentUser, Depends(get_current_user)]
    ) -> CurrentUser:
        if permission.value not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission.value}",
            )
        return current_user
    return _check


class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number"),
        page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size


# Type aliases for clean endpoint signatures
DbSession = Annotated[AsyncSession, Depends(get_db)]
AuthUser = Annotated[CurrentUser, Depends(get_current_active_user)]
Pagination = Annotated[PaginationParams, Depends()]
