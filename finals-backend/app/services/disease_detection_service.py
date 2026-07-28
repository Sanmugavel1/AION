"""
AION Disease Detection Service — Module 5
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.algorithms.disease_classifier import run_full_disease_scan
from app.repositories.disease_repository import DiseaseRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.core.logging import get_logger

logger = get_logger(__name__)

DISEASE_DESCRIPTIONS = {
    "knowledge_cancer": "Uncontrolled duplication and fragmentation of knowledge across silos",
    "memory_alzheimers": "Progressive loss of organizational memory as key knowledge holders leave",
    "communication_stroke": "Severed communication channels between critical knowledge nodes",
    "knowledge_obesity": "Accumulation of low-value, redundant, or irrelevant knowledge",
    "innovation_paralysis": "Inability to generate new ideas due to calcified knowledge patterns",
}


class DiseaseDetectionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.disease_repo = DiseaseRepository(session)
        self.knowledge_repo = KnowledgeRepository(session)

    async def get_scan_results(self, org_id: UUID) -> dict:
        """Return the latest disease scan results (from DB + fresh graph data)."""
        active = await self.disease_repo.get_active_diseases(org_id)
        return {
            "org_id": str(org_id),
            "scan_status": "completed",
            "diseases_detected": len(active),
            "diseases": [
                {
                    "type": d.disease_type,
                    "severity": d.severity,
                    "severity_score": d.severity_score,
                    "confidence": d.confidence,
                    "description": DISEASE_DESCRIPTIONS.get(d.disease_type, ""),
                    "detected_at": d.detected_at.isoformat(),
                    "evidence": d.evidence,
                    "predicted_critical_date": (
                        d.predicted_critical_date.isoformat()
                        if d.predicted_critical_date else None
                    ),
                }
                for d in active
            ],
        }

    async def get_disease_report(self, org_id: UUID) -> dict:
        """Full disease report with trend and recommendations."""
        active = await self.disease_repo.get_active_diseases(org_id)
        history = await self.disease_repo.get_history(org_id, limit=10)
        health = await self.knowledge_repo.get_health_summary(org_id)

        critical = [d for d in active if d.severity == "critical"]
        warning = [d for d in active if d.severity == "warning"]

        return {
            "org_id": str(org_id),
            "summary": {
                "total_active": len(active),
                "critical_count": len(critical),
                "warning_count": len(warning),
                "overall_disease_score": (
                    sum(d.severity_score for d in active) / len(active) if active else 0.0
                ),
            },
            "knowledge_context": health,
            "active_diseases": [
                {
                    "type": d.disease_type,
                    "severity": d.severity,
                    "score": d.severity_score,
                    "description": DISEASE_DESCRIPTIONS.get(d.disease_type, ""),
                }
                for d in active
            ],
            "recent_history": [
                {"type": d.disease_type, "severity": d.severity, "date": d.detected_at.isoformat()}
                for d in history[:5]
            ],
        }

    async def get_disease_by_type(self, org_id: UUID, disease_type: str) -> dict:
        disease = await self.disease_repo.get_by_type(org_id, disease_type)
        if not disease:
            return {
                "type": disease_type,
                "status": "not_detected",
                "description": DISEASE_DESCRIPTIONS.get(disease_type, ""),
            }
        return {
            "type": disease.disease_type,
            "severity": disease.severity,
            "severity_score": disease.severity_score,
            "confidence": disease.confidence,
            "evidence": disease.evidence,
            "detected_at": disease.detected_at.isoformat(),
            "description": DISEASE_DESCRIPTIONS.get(disease_type, ""),
        }

    async def get_disease_timeline(self, org_id: UUID, limit: int = 30) -> list[dict]:
        history = await self.disease_repo.get_history(org_id, limit=limit)
        return [
            {
                "date": d.detected_at.isoformat(),
                "type": d.disease_type,
                "severity": d.severity,
                "score": d.severity_score,
                "resolved": d.is_resolved,
            }
            for d in history
        ]
