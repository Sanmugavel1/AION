"""
AION Organizational Intelligence Index Service
Computes and stores the 12-dimension OII health report
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.algorithms.intelligence_scorer import OIIScore, compute_oii_score
from app.core.logging import get_logger
from app.models.disease import IntelligenceSnapshot
from app.repositories.disease_repository import IntelligenceSnapshotRepository

logger = get_logger(__name__)


class IntelligenceIndexService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = IntelligenceSnapshotRepository(db)

    async def compute_and_store_oii(self, org_id: UUID, raw_data: dict) -> OIIScore:
        """Compute OII from raw org data and persist a snapshot."""
        from datetime import datetime, timezone

        score = compute_oii_score(raw_data)

        snapshot = IntelligenceSnapshot(
            org_id=org_id,
            computed_at=datetime.now(timezone.utc),
            overall_health=score.overall,
            knowledge_velocity=score.knowledge_velocity,
            knowledge_coverage=score.knowledge_coverage,
            knowledge_quality=score.knowledge_quality,
            learning_agility=score.learning_agility,
            collaboration_density=score.collaboration_density,
            innovation_index=score.innovation_index,
            decision_intelligence=score.decision_intelligence,
            cognitive_resilience=score.cognitive_resilience,
            knowledge_accessibility=score.knowledge_accessibility,
            expertise_depth=score.expertise_depth,
            knowledge_retention=score.knowledge_retention,
            adaptability_score=score.adaptability_score,
            knowledge_half_life=score.knowledge_half_life,
            knowledge_entropy=score.knowledge_entropy,
            memory_compression=score.memory_compression,
            raw_data=raw_data,
        )
        self._db.add(snapshot)
        await self._db.commit()
        await self._db.refresh(snapshot)

        logger.info("OII computed and stored", org_id=str(org_id), overall=score.overall)
        return score

    async def get_latest_oii(self, org_id: UUID) -> Optional[dict]:
        snap = await self._repo.get_latest(org_id)
        if not snap:
            return None
        return _snapshot_dict(snap)

    async def get_oii_history(self, org_id: UUID, limit: int = 30) -> list[dict]:
        history = await self._repo.get_history(org_id, limit=limit)
        return [_snapshot_dict(s) for s in history]

    async def get_trends(self, org_id: UUID) -> dict:
        history = await self._repo.get_history(org_id, limit=12)
        if not history:
            return {"trend": "insufficient_data"}
        overalls = [s.overall_health for s in history]
        trend = "stable"
        if len(overalls) >= 2:
            delta = overalls[0] - overalls[-1]
            trend = "improving" if delta > 0.05 else "declining" if delta < -0.05 else "stable"
        return {
            "trend": trend,
            "current": overalls[0] if overalls else 0,
            "delta_30d": round(overalls[0] - overalls[min(3, len(overalls) - 1)], 4),
            "history": [{"date": s.computed_at.isoformat(), "score": s.overall_health} for s in history],
        }


def _snapshot_dict(snap: IntelligenceSnapshot) -> dict:
    # Derived from the persisted raw_data rather than a dedicated column —
    # avoids a schema migration for what's really just a display hint: has
    # this org uploaded any knowledge yet, or is `overall_health` computed
    # from nothing?
    knowledge_total = (snap.raw_data or {}).get("knowledge_health", {}).get("total", 0)
    has_sufficient_data = knowledge_total > 0
    return {
        "id": str(snap.id),
        "org_id": str(snap.org_id),
        "computed_at": snap.computed_at.isoformat(),
        "overall_health": snap.overall_health,
        "has_sufficient_data": has_sufficient_data,
        "dimensions": {
            "knowledge_velocity": snap.knowledge_velocity,
            "knowledge_coverage": snap.knowledge_coverage,
            "knowledge_quality": snap.knowledge_quality,
            "learning_agility": snap.learning_agility,
            "collaboration_density": snap.collaboration_density,
            "innovation_index": snap.innovation_index,
            "decision_intelligence": snap.decision_intelligence,
            "cognitive_resilience": snap.cognitive_resilience,
            "knowledge_accessibility": snap.knowledge_accessibility,
            "expertise_depth": snap.expertise_depth,
            "knowledge_retention": snap.knowledge_retention,
            "adaptability_score": snap.adaptability_score,
        },
        "proprietary_metrics": {
            "knowledge_half_life_days": snap.knowledge_half_life,
            "knowledge_entropy_bits": snap.knowledge_entropy,
            "memory_compression_ratio": snap.memory_compression,
        },
    }
