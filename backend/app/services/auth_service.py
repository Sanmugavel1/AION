"""
AION Auth Service — Registration, Login, Token Management
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    UserRole,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.organization import Organization
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(
        self,
        org_name: str,
        industry: str,
        email: str,
        username: str,
        password: str,
        full_name: str,
    ) -> dict:
        """Create org + first admin user. Returns token pair."""
        if await self.user_repo.email_exists(email):
            raise ConflictError(f"Email {email} is already registered")

        slug = org_name.lower().replace(" ", "-")[:50]
        org = Organization(id=uuid4(), name=org_name, slug=slug, industry=industry)
        self.session.add(org)
        await self.session.flush()

        user = User(
            id=uuid4(),
            org_id=org.id,
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=UserRole.ORG_ADMIN.value,
            is_active=True,
            is_verified=True,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        logger.info("New org registered", org_id=str(org.id), user_id=str(user.id))
        return {**_token_pair(user), "user": _user_dict(user), "org_id": str(org.id)}

    async def login(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        user.last_login_at = datetime.now(timezone.utc)
        await self.session.commit()
        logger.info("User logged in", user_id=str(user.id))
        return {**_token_pair(user), "user": _user_dict(user)}

    async def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")
        user = await self.user_repo.get(UUID(payload["sub"]))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        return _token_pair(user)

    async def get_me(self, user_id: UUID) -> dict:
        user = await self.user_repo.get_or_raise(user_id)
        return _user_dict(user)


def _token_pair(user: User) -> dict:
    role = UserRole(user.role)
    return {
        "access_token": create_access_token(
            subject=str(user.id),
            org_id=str(user.org_id),
            role=role,
            additional_claims={"email": user.email},
        ),
        "refresh_token": create_refresh_token(str(user.id), str(user.org_id)),
        "token_type": "bearer",
    }


def _user_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "org_id": str(user.org_id),
    }
