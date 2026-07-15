"""
AION Knowledge Repository — PostgreSQL operations for KnowledgeItem
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeItem
from app.repositories.base_repository import BaseRepository


class KnowledgeRepository(BaseRepository[KnowledgeItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(KnowledgeItem, session)

    async def get_recent(self, org_id: UUID, limit: int = 20) -> Sequence[KnowledgeItem]:
        """Most recently created knowledge items for an org, newest first."""
        result = await self.session.execute(
            select(KnowledgeItem)
            .where(KnowledgeItem.org_id == org_id)
            .order_by(KnowledgeItem.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    # ── Decay-specific queries ──────────────────────────────────────────────

    async def get_decayed_items(
        self,
        org_id: UUID,
        relevance_threshold: float = 0.3,
        limit: int = 200,
    ) -> Sequence[KnowledgeItem]:
        """Items whose relevance score has dropped below threshold."""
        result = await self.session.execute(
            select(KnowledgeItem)
            .where(
                and_(
                    KnowledgeItem.org_id == org_id,
                    KnowledgeItem.relevance_score < relevance_threshold,
                    KnowledgeItem.is_active.is_(True),
                )
            )
            .order_by(KnowledgeItem.relevance_score.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_stale_items(
        self,
        org_id: UUID,
        days_since_access: int = 90,
        limit: int = 500,
    ) -> Sequence[KnowledgeItem]:
        """Items not accessed for more than N days."""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_since_access)
        result = await self.session.execute(
            select(KnowledgeItem)
            .where(
                and_(
                    KnowledgeItem.org_id == org_id,
                    KnowledgeItem.last_accessed_at < cutoff,
                    KnowledgeItem.is_active.is_(True),
                )
            )
            .order_by(KnowledgeItem.last_accessed_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_items_by_domain(
        self, org_id: UUID, domain: str, limit: int = 100
    ) -> Sequence[KnowledgeItem]:
        result = await self.session.execute(
            select(KnowledgeItem)
            .where(
                and_(
                    KnowledgeItem.org_id == org_id,
                    KnowledgeItem.domain == domain,
                )
            )
            .order_by(KnowledgeItem.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_isolated_items(
        self, org_id: UUID, limit: int = 100
    ) -> Sequence[KnowledgeItem]:
        """Items flagged as isolated (no connections in the graph)."""
        result = await self.session.execute(
            select(KnowledgeItem)
            .where(
                and_(
                    KnowledgeItem.org_id == org_id,
                    KnowledgeItem.is_isolated.is_(True),
                )
            )
            .limit(limit)
        )
        return result.scalars().all()

    async def get_conflicted_items(
        self, org_id: UUID, limit: int = 100
    ) -> Sequence[KnowledgeItem]:
        result = await self.session.execute(
            select(KnowledgeItem)
            .where(
                and_(
                    KnowledgeItem.org_id == org_id,
                    KnowledgeItem.is_conflicted.is_(True),
                )
            )
            .limit(limit)
        )
        return result.scalars().all()

    async def get_duplicate_items(
        self, org_id: UUID, limit: int = 100
    ) -> Sequence[KnowledgeItem]:
        result = await self.session.execute(
            select(KnowledgeItem)
            .where(
                and_(
                    KnowledgeItem.org_id == org_id,
                    KnowledgeItem.is_duplicate.is_(True),
                )
            )
            .limit(limit)
        )
        return result.scalars().all()

    # ── Bulk updates ────────────────────────────────────────────────────────

    async def bulk_update_relevance(
        self, updates: list[dict]
    ) -> int:
        """Bulk update relevance scores. Each dict: {id, relevance_score, decay_rate}"""
        count = 0
        for upd in updates:
            result = await self.session.execute(
                update(KnowledgeItem)
                .where(KnowledgeItem.id == upd["id"])
                .values(
                    relevance_score=upd["relevance_score"],
                    decay_rate=upd.get("decay_rate"),
                    is_outdated=upd.get("is_outdated", False),
                )
            )
            count += result.rowcount
        return count

    async def record_access(self, item_id: UUID) -> None:
        """Increment access count and update last_accessed_at."""
        await self.session.execute(
            update(KnowledgeItem)
            .where(KnowledgeItem.id == item_id)
            .values(
                access_count=KnowledgeItem.access_count + 1,
                last_accessed_at=datetime.now(timezone.utc),
            )
        )

    # ── Statistics ──────────────────────────────────────────────────────────

    async def _count_bool(self, org_id: UUID, field: str) -> int:
        """Count items where a boolean field is True."""
        from sqlalchemy import func
        col = getattr(KnowledgeItem, field)
        result = await self.session.execute(
            select(func.count()).select_from(KnowledgeItem).where(
                and_(KnowledgeItem.org_id == org_id, col.is_(True))
            )
        )
        return result.scalar_one()

    async def get_domain_distribution(self, org_id: UUID) -> list[dict]:
        result = await self.session.execute(
            select(KnowledgeItem.domain, func.count(KnowledgeItem.id).label("count"))
            .where(KnowledgeItem.org_id == org_id)
            .group_by(KnowledgeItem.domain)
            .order_by(func.count(KnowledgeItem.id).desc())
        )
        return [{"domain": row.domain, "count": row.count} for row in result]

    async def get_health_summary(self, org_id: UUID) -> dict:
        """Aggregate knowledge health stats for an org."""
        total = await self.count({"org_id": org_id})
        outdated = await self._count_bool(org_id, "is_outdated")
        isolated = await self._count_bool(org_id, "is_isolated")
        conflicted = await self._count_bool(org_id, "is_conflicted")
        duplicated = await self._count_bool(org_id, "is_duplicate")

        avg_result = await self.session.execute(
            select(func.avg(KnowledgeItem.relevance_score)).where(
                KnowledgeItem.org_id == org_id
            )
        )
        avg_relevance = float(avg_result.scalar_one() or 0.0)

        return {
            "total": total,
            "outdated": outdated,
            "isolated": isolated,
            "conflicted": conflicted,
            "duplicated": duplicated,
            "avg_relevance_score": round(avg_relevance, 3),
            "health_ratio": round(1 - (outdated + isolated) / max(total, 1), 3),
        }
