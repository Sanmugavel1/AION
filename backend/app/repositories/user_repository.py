"""
AION User Repository
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_org(self, org_id: UUID, skip: int = 0, limit: int = 50) -> list[User]:
        result = await self.session.execute(
            select(User)
            .where(User.org_id == org_id, User.is_active.is_(True))
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_department(self, dept_id: UUID) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.dept_id == dept_id, User.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        result = await self.session.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None
