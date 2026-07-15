"""
AION Self-Healing Service — Module 7
Generates and manages AI-driven healing recommendations
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.healing_agent import SelfHealingAgent
from app.models.simulation import HealingAction
from app.core.logging import get_logger
from sqlalchemy import select

logger = get_logger(__name__)


class SelfHealingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._agent = SelfHealingAgent()

    async def get_recommendations(self, org_id: UUID) -> list[dict]:
        result = await self.session.execute(
            select(HealingAction)
            .where(HealingAction.org_id == org_id, HealingAction.status == "pending")
            .order_by(HealingAction.created_at.desc())
            .limit(20)
        )
        actions = result.scalars().all()
        return [_action_dict(a) for a in actions]

    async def generate_recommendations(self, org_id: UUID) -> dict:
        """Run the SelfHealingAgent and persist new recommendations."""
        from app.repositories.disease_repository import DiseaseRepository, IntelligenceSnapshotRepository

        d_repo = DiseaseRepository(self.session)
        i_repo = IntelligenceSnapshotRepository(self.session)

        diseases = await d_repo.get_active_diseases(org_id)
        oii = await i_repo.get_latest(org_id)

        context = {
            "org_id": str(org_id),
            "diseases": [
                {"type": d.disease_type, "severity": d.severity, "score": d.severity_score}
                for d in diseases
            ],
            "oii": {"overall": oii.overall_health if oii else 0.5},
        }

        result = await self._agent.run(context)

        # Persist recommendations
        created = []
        for rec in result.get("recommendations", []):
            action = HealingAction(
                org_id=org_id,
                action_type=rec.get("action_type", "general"),
                title=rec.get("title", "Healing Action"),
                description=rec.get("description", ""),
                priority=rec.get("priority", "medium"),
                status="pending",
                estimated_impact=rec.get("estimated_impact", "medium"),
                parameters=rec.get("metadata", {}),
            )
            self.session.add(action)
            created.append(rec)

        await self.session.commit()
        return {"generated": len(created), "recommendations": created}

    async def approve(self, org_id: UUID, action_id: UUID, approver_id: UUID) -> dict:
        from datetime import datetime, timezone
        action = await self.session.get(HealingAction, action_id)
        if not action or action.org_id != org_id:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Healing action not found")
        action.status = "approved"
        action.approved_by = approver_id
        action.approved_at = datetime.now(timezone.utc)
        await self.session.commit()
        return _action_dict(action)

    async def reject(self, org_id: UUID, action_id: UUID, reason: str) -> dict:
        action = await self.session.get(HealingAction, action_id)
        if not action or action.org_id != org_id:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Healing action not found")
        action.status = "rejected"
        action.outcome = f"Rejected: {reason}"
        await self.session.commit()
        return _action_dict(action)


def _action_dict(a: HealingAction) -> dict:
    return {
        "id": str(a.id),
        "action_type": a.action_type,
        "title": a.title,
        "description": a.description,
        "priority": a.priority,
        "status": a.status,
        "estimated_impact": a.estimated_impact,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }
