"""
AION Board Advisor Service — Module 10
Generates executive intelligence briefings
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.disease_repository import (
    DiseaseRepository,
    IntelligenceSnapshotRepository,
)
from app.repositories.knowledge_repository import KnowledgeRepository
from app.ai.llm.llm_client import generate_board_narrative
from app.core.logging import get_logger

logger = get_logger(__name__)


class BoardAdvisorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.i_repo = IntelligenceSnapshotRepository(session)
        self.d_repo = DiseaseRepository(session)
        self.k_repo = KnowledgeRepository(session)

    async def get_latest_briefing(self, org_id: UUID) -> dict:
        oii = await self.i_repo.get_latest(org_id)
        diseases = await self.d_repo.get_active_diseases(org_id)
        health = await self.k_repo.get_health_summary(org_id)

        risks = _extract_risks(diseases, health)
        opportunities = _extract_opportunities(oii, health)

        metrics = {
            "overall_health": oii.overall_health if oii else 0.5,
            "knowledge_quality": getattr(oii, "knowledge_quality", 0.5) if oii else 0.5,
            "cognitive_resilience": getattr(oii, "cognitive_resilience", 0.5) if oii else 0.5,
            "innovation_index": getattr(oii, "innovation_index", 0.5) if oii else 0.5,
            "collaboration_density": getattr(oii, "collaboration_density", 0.5) if oii else 0.5,
            "total_knowledge_items": health.get("total", 0),
            "knowledge_health_ratio": health.get("health_ratio", 0.5),
        }

        try:
            narrative = await generate_board_narrative(metrics, risks, opportunities)
        except Exception:
            narrative = _fallback_narrative(metrics, risks, opportunities)

        history = await self.i_repo.get_history(org_id, limit=4)
        trend = _compute_trend(history)

        return {
            "org_id": str(org_id),
            "report_type": "board_intelligence_briefing",
            "oii_score": metrics["overall_health"],
            "oii_trend": trend,
            "executive_summary": narrative,
            "key_metrics": metrics,
            "top_risks": risks[:5],
            "top_opportunities": opportunities[:5],
            "disease_alerts": [
                {"type": d.disease_type, "severity": d.severity, "score": d.severity_score}
                for d in diseases
                if d.severity_score > 0.3
            ],
            "knowledge_snapshot": health,
            "oii_dimensions": {
                "knowledge_velocity": getattr(oii, "knowledge_velocity", 0) if oii else 0,
                "learning_agility": getattr(oii, "learning_agility", 0) if oii else 0,
                "decision_intelligence": getattr(oii, "decision_intelligence", 0) if oii else 0,
                "knowledge_accessibility": getattr(oii, "knowledge_accessibility", 0) if oii else 0,
            },
        }

    async def get_briefing_history(self, org_id: UUID, limit: int = 10) -> list[dict]:
        history = await self.i_repo.get_history(org_id, limit=limit)
        return [
            {
                "computed_at": s.computed_at.isoformat(),
                "overall_health": s.overall_health,
                "knowledge_entropy": s.knowledge_entropy,
                "cognitive_resilience": s.cognitive_resilience,
            }
            for s in history
        ]

    async def get_strategic_risks(self, org_id: UUID) -> list[dict]:
        diseases = await self.d_repo.get_active_diseases(org_id)
        health = await self.k_repo.get_health_summary(org_id)
        return _extract_risks(diseases, health)

    async def get_opportunities(self, org_id: UUID) -> list[dict]:
        oii = await self.i_repo.get_latest(org_id)
        health = await self.k_repo.get_health_summary(org_id)
        return _extract_opportunities(oii, health)


def _extract_risks(diseases, health) -> list[dict]:
    risks = []
    for d in diseases:
        if d.severity_score > 0.2:
            risks.append({
                "category": "organizational_disease",
                "title": d.disease_type.replace("_", " ").title(),
                "severity": d.severity,
                "score": d.severity_score,
                "description": f"Active {d.disease_type} requires immediate intervention",
            })
    if health.get("isolated", 0) > 20:
        risks.append({
            "category": "knowledge_isolation",
            "title": "High Knowledge Isolation",
            "severity": "warning",
            "score": min(health["isolated"] / 100, 1.0),
            "description": f"{health['isolated']} isolated knowledge items risk permanent loss",
        })
    return sorted(risks, key=lambda x: x["score"], reverse=True)


def _extract_opportunities(oii, health) -> list[dict]:
    opps = []
    if oii and getattr(oii, "collaboration_density", 1.0) < 0.4:
        opps.append({
            "category": "collaboration",
            "title": "Cross-team Knowledge Sharing Program",
            "potential_impact": "high",
            "description": "Low collaboration density indicates untapped cross-functional synergies",
        })
    if health.get("avg_relevance_score", 1.0) < 0.5:
        opps.append({
            "category": "knowledge_refresh",
            "title": "Targeted Knowledge Modernization",
            "potential_impact": "medium",
            "description": "Refreshing low-relevance content could improve OII by 8-12 points",
        })
    if oii and getattr(oii, "innovation_index", 1.0) < 0.5:
        opps.append({
            "category": "innovation",
            "title": "Innovation Lab / Hackathon Initiative",
            "potential_impact": "high",
            "description": "Innovation index below 50% signals opportunity for structured creativity programs",
        })
    return opps


def _compute_trend(history) -> str:
    if len(history) < 2:
        return "stable"
    delta = history[0].overall_health - history[-1].overall_health
    return "improving" if delta > 0.05 else "declining" if delta < -0.05 else "stable"


def _fallback_narrative(metrics, risks, opportunities) -> str:
    score = metrics.get("overall_health", 0.5)
    risk_count = len(risks)
    health_label = "strong" if score > 0.7 else "moderate" if score > 0.4 else "concerning"
    return (
        f"The organization's Organizational Intelligence Index stands at {score:.0%}, "
        f"indicating a {health_label} knowledge health posture. "
        f"There are currently {risk_count} active risk areas requiring board attention. "
        f"{len(opportunities)} strategic opportunities have been identified to improve intelligence capacity."
    )
