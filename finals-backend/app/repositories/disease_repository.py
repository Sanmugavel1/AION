"""
AION Disease Repository — DiseaseRecord & IntelligenceSnapshot persistence
"""
from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.disease import DiseaseRecord, IntelligenceSnapshot
from app.repositories.base_repository import BaseRepository


class DiseaseRepository(BaseRepository[DiseaseRecord]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DiseaseRecord, session)

    async def get_active_diseases(self, org_id: UUID) -> Sequence[DiseaseRecord]:
        result = await self.session.execute(
            select(DiseaseRecord)
            .where(
                and_(
                    DiseaseRecord.org_id == org_id,
                    DiseaseRecord.is_resolved.is_(False),
                )
            )
            .order_by(DiseaseRecord.severity_score.desc())
        )
        return result.scalars().all()

    async def get_by_type(self, org_id: UUID, disease_type: str) -> Optional[DiseaseRecord]:
        result = await self.session.execute(
            select(DiseaseRecord)
            .where(
                and_(
                    DiseaseRecord.org_id == org_id,
                    DiseaseRecord.disease_type == disease_type,
                    DiseaseRecord.is_resolved.is_(False),
                )
            )
            .order_by(DiseaseRecord.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self, org_id: UUID, limit: int = 50
    ) -> Sequence[DiseaseRecord]:
        result = await self.session.execute(
            select(DiseaseRecord)
            .where(DiseaseRecord.org_id == org_id)
            .order_by(DiseaseRecord.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


class IntelligenceSnapshotRepository(BaseRepository[IntelligenceSnapshot]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(IntelligenceSnapshot, session)

    async def get_latest(self, org_id: UUID) -> Optional[IntelligenceSnapshot]:
        result = await self.session.execute(
            select(IntelligenceSnapshot)
            .where(IntelligenceSnapshot.org_id == org_id)
            .order_by(IntelligenceSnapshot.computed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self, org_id: UUID, limit: int = 30
    ) -> Sequence[IntelligenceSnapshot]:
        result = await self.session.execute(
            select(IntelligenceSnapshot)
            .where(IntelligenceSnapshot.org_id == org_id)
            .order_by(IntelligenceSnapshot.computed_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
