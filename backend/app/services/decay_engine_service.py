"""
AION Decay Engine Service — Module 4
Exposes decay analytics to the API layer
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.algorithms.knowledge_entropy import compute_organizational_entropy_report
from app.ai.algorithms.knowledge_half_life import (
    compute_current_relevance,
    compute_days_until_critical,
    compute_knowledge_half_life,
)
from app.repositories.knowledge_repository import KnowledgeRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class DecayEngineService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = KnowledgeRepository(session)

    async def get_decay_report(self, org_id: UUID) -> dict:
        health = await self.repo.get_health_summary(org_id)
        stale_items = await self.repo.get_stale_items(org_id, days_since_access=90, limit=20)
        decayed_items = await self.repo.get_decayed_items(org_id, relevance_threshold=0.3, limit=20)

        return {
            "org_id": str(org_id),
            "summary": health,
            "most_decayed": [
                {
                    "id": str(i.id),
                    "title": i.title,
                    "domain": i.domain,
                    "relevance_score": i.relevance_score,
                    "last_accessed_at": i.last_accessed_at.isoformat() if i.last_accessed_at else None,
                }
                for i in decayed_items
            ],
            "stale_items": [
                {
                    "id": str(i.id),
                    "title": i.title,
                    "domain": i.domain,
                    "last_accessed_at": i.last_accessed_at.isoformat() if i.last_accessed_at else None,
                }
                for i in stale_items
            ],
        }

    async def get_entropy_report(self, org_id: UUID) -> dict:
        domain_dist = await self.repo.get_domain_distribution(org_id)
        health = await self.repo.get_health_summary(org_id)

        raw_data = {
            "domain_distribution": domain_dist,
            "total_items": health.get("total", 0),
            "isolated_count": health.get("isolated", 0),
            "duplicate_count": health.get("duplicated", 0),
        }
        return compute_organizational_entropy_report(raw_data)

    async def get_item_half_life(self, org_id: UUID, item_id: UUID) -> dict:
        from datetime import datetime, timezone
        item = await self.repo.get_or_raise(item_id)

        hl = compute_knowledge_half_life(
            domain=item.domain,
            last_accessed_at=item.last_accessed_at,
            access_count=item.access_count,
            is_documented=item.item_metadata.get("is_documented", False) if item.item_metadata else False,
            owner_count=item.item_metadata.get("owner_count", 1) if item.item_metadata else 1,
            content_age_days=(datetime.now(timezone.utc) - item.created_at).days,
        )
        days_elapsed = (datetime.now(timezone.utc) - item.created_at).days
        relevance = compute_current_relevance(
            r0=1.0,
            half_life_days=hl["half_life_days"],
            days_elapsed=days_elapsed,
        )
        days_to_critical = compute_days_until_critical(
            hl["half_life_days"], current_relevance=relevance, critical_threshold=0.2
        )

        return {
            "item_id": str(item_id),
            "title": item.title,
            "domain": item.domain,
            **hl,
            "current_relevance": round(relevance, 4),
            "days_elapsed": days_elapsed,
            "days_until_critical": days_to_critical,
            "status": "critical" if relevance < 0.2 else "warning" if relevance < 0.4 else "healthy",
        }

    async def get_forgotten_knowledge(self, org_id: UUID, limit: int = 50) -> list[dict]:
        items = await self.repo.get_stale_items(org_id, days_since_access=180, limit=limit)
        return [
            {
                "id": str(i.id),
                "title": i.title,
                "domain": i.domain,
                "relevance_score": i.relevance_score,
                "access_count": i.access_count,
                "last_accessed_at": i.last_accessed_at.isoformat() if i.last_accessed_at else None,
            }
            for i in items
        ]

    async def get_conflicted_knowledge(self, org_id: UUID) -> list[dict]:
        items = await self.repo.get_conflicted_items(org_id)
        return [
            {"id": str(i.id), "title": i.title, "domain": i.domain}
            for i in items
        ]
