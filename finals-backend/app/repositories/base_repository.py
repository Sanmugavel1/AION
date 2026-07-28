"""
AION Base Repository — Generic CRUD with SQLAlchemy 2 Async
All domain repositories extend this class.
"""
from __future__ import annotations

from typing import Any, Generic, Optional, Sequence, Type, TypeVar
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    """
    Generic repository providing standard CRUD operations.
    All domain repositories inherit and extend this.
    """

    def __init__(self, model: Type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> Optional[ModelT]:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_or_raise(self, id: UUID) -> ModelT:
        obj = await self.get(id)
        if obj is None:
            from app.core.exceptions import NotFoundError
            raise NotFoundError(f"{self.model.__name__} {id} not found")
        return obj

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> Sequence[ModelT]:
        stmt = select(self.model)
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)
        if order_by and hasattr(self.model, order_by):
            stmt = stmt.order_by(getattr(self.model, order_by))
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(self.model)
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, **kwargs: Any) -> ModelT:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: UUID, **kwargs: Any) -> Optional[ModelT]:
        obj = await self.get(id)
        if obj is None:
            return None
        for field, value in kwargs.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0

    async def bulk_create(self, items: list[dict[str, Any]]) -> list[ModelT]:
        objects = [self.model(**item) for item in items]
        self.session.add_all(objects)
        await self.session.flush()
        return objects
