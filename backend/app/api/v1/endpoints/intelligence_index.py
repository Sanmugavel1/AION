"""
AION API â€” Module 9: Organizational Intelligence Index
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import AuthUser, DbSession, Pagination, get_current_user, require_perm
from app.core.security import Permission
from app.repositories.disease_repository import DiseaseRepository
from app.repositories.graph_repository import GraphRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.intelligence_index_service import IntelligenceIndexService

router = APIRouter(prefix="/intelligence", tags=["Module 9: Intelligence Index"])

TREND_DIMENSIONS = [
    "knowledge_velocity", "knowledge_quality", "cognitive_resilience",
    "collaboration_density", "innovation_index", "adaptability_score",
]


async def _compute_live_oii(service: IntelligenceIndexService, db: DbSession, org_id: str) -> dict:
    """Build raw_data from live Postgres + graph state and compute a fresh OII snapshot."""
    k_repo = KnowledgeRepository(db)
    d_repo = DiseaseRepository(db)
    graph_repo = GraphRepository()

    health = await k_repo.get_health_summary(UUID(org_id))
    domain_distribution = await k_repo.get_domain_distribution(UUID(org_id))
    diseases = await d_repo.get_active_diseases(UUID(org_id))
    brain_map = await graph_repo.get_org_brain_map(org_id)

    nodes = brain_map.get("nodes", [])
    persons = sum(1 for n in nodes if n["type"] == "Person")
    knowledge_nodes = sum(1 for n in nodes if n["type"] == "Knowledge")
    collaboration_links = sum(1 for e in brain_map.get("edges", []) if e["relationship"] == "COLLABORATES_WITH")

    raw_data = {
        "user_count": max(persons, 1),
        "knowledge_health": health,
        "domain_distribution": domain_distribution,
        "active_disease_count": len(diseases),
        "disease_severity_avg": (
            sum(d.severity_score for d in diseases) / len(diseases) if diseases else 0.0
        ),
        "graph_data": {
            "persons": persons,
            "knowledge_nodes": knowledge_nodes,
            "collaboration_links": collaboration_links,
        },
    }
    score = await service.compute_and_store_oii(UUID(org_id), raw_data)
    result = await service.get_latest_oii(org_id)
    return result


@router.get("/index")
async def get_organizational_intelligence_index(
    current_user: AuthUser,
    db: DbSession,
):
    """
    Get the latest Organizational Intelligence Index.
    12 dimensions + 3 proprietary AION metrics.
    Computes a fresh snapshot from live data if none exists yet.
    """
    service = IntelligenceIndexService(db)
    result = await service.get_latest_oii(current_user.org_id)
    if not result:
        result = await _compute_live_oii(service, db, current_user.org_id)
    return result


@router.get("/history")
async def get_oii_history(
    limit: int = 30,
    *,
    current_user: AuthUser,
    db: DbSession,
):
    """Get historical OII scores for trend analysis."""
    service = IntelligenceIndexService(db)
    return await service.get_oii_history(current_user.org_id, limit)


@router.get("/trends")
async def get_intelligence_trends(
    current_user: AuthUser,
    db: DbSession,
):
    """Trend analysis across key OII dimensions (direction + delta)."""
    service = IntelligenceIndexService(db)
    return await service.get_trends(current_user.org_id)
