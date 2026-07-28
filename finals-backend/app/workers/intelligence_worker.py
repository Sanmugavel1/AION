"""
AION Celery Worker — Module 9: Organizational Intelligence Index (OII)
Runs daily at midnight UTC to compute the 12-dimension intelligence score
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.core.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    name="aion.intelligence.compute",
    bind=True,
    max_retries=2,
    default_retry_delay=600,
    soft_time_limit=1800,
)
def compute(self) -> dict:
    """
    Daily OII computation for all organizations.
    Computes all 12 intelligence dimensions + 3 proprietary metrics.
    Stores snapshot in IntelligenceSnapshot table.
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_async_compute_intelligence())


async def _async_compute_intelligence() -> dict:
    from app.core.database import async_session_factory
    from app.ai.algorithms.intelligence_scorer import compute_oii_score
    from app.ai.algorithms.cognitive_resilience import compute_cognitive_resilience_score
    from app.ai.algorithms.knowledge_entropy import compute_organizational_entropy_report
    from app.models.organization import Organization
    from app.models.disease import IntelligenceSnapshot
    from sqlalchemy import select

    results = {"orgs_computed": 0, "errors": []}

    async with async_session_factory() as session:
        orgs_result = await session.execute(
            select(Organization).where(Organization.is_active.is_(True))
        )
        orgs = orgs_result.scalars().all()

        for org in orgs:
            try:
                raw_data = await _collect_oii_data(org.id, session)

                oii = compute_oii_score(raw_data)

                snapshot = IntelligenceSnapshot(
                    org_id=org.id,
                    computed_at=datetime.now(timezone.utc),
                    overall_health=oii.overall,
                    knowledge_velocity=oii.knowledge_velocity,
                    knowledge_coverage=oii.knowledge_coverage,
                    knowledge_quality=oii.knowledge_quality,
                    learning_agility=oii.learning_agility,
                    collaboration_density=oii.collaboration_density,
                    innovation_index=oii.innovation_index,
                    decision_intelligence=oii.decision_intelligence,
                    cognitive_resilience=oii.cognitive_resilience,
                    knowledge_accessibility=oii.knowledge_accessibility,
                    expertise_depth=oii.expertise_depth,
                    knowledge_retention=oii.knowledge_retention,
                    adaptability_score=oii.adaptability_score,
                    knowledge_half_life=oii.knowledge_half_life,
                    knowledge_entropy=oii.knowledge_entropy,
                    memory_compression=oii.memory_compression,
                    raw_data=raw_data,
                )
                session.add(snapshot)
                await session.commit()

                results["orgs_computed"] += 1
                logger.info(
                    "OII computed",
                    org_id=str(org.id),
                    overall=oii.overall,
                )
            except Exception as e:
                logger.error("OII computation failed", org_id=str(org.id), error=str(e))
                results["errors"].append({"org_id": str(org.id), "error": str(e)})
                await session.rollback()

    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    return results


async def _collect_oii_data(org_id, session) -> dict:
    """Collect all raw data needed to compute OII."""
    from app.repositories.knowledge_repository import KnowledgeRepository
    from app.repositories.user_repository import UserRepository
    from app.repositories.disease_repository import DiseaseRepository
    from app.core.neo4j_client import execute_query

    k_repo = KnowledgeRepository(session)
    u_repo = UserRepository(session)
    d_repo = DiseaseRepository(session)

    health = await k_repo.get_health_summary(org_id)
    domain_dist = await k_repo.get_domain_distribution(org_id)
    users = await u_repo.get_by_org(org_id, limit=500)
    diseases = await d_repo.get_active_diseases(org_id)

    # Graph connectivity metrics
    graph_data = {}
    try:
        records = await execute_query(
            """
            MATCH (p:Person {org_id: $org_id})
            OPTIONAL MATCH (p)-[:KNOWS]->(k:Knowledge)
            OPTIONAL MATCH (p)-[:COLLABORATES_WITH]->(p2:Person)
            RETURN
                count(DISTINCT p) AS persons,
                count(DISTINCT k) AS knowledge_nodes,
                count(DISTINCT p2) AS collaboration_links,
                avg(size((p)-[:KNOWS]->())) AS avg_knowledge_per_person
            """,
            {"org_id": str(org_id)},
        )
        if records:
            graph_data = dict(records[0])
    except Exception:
        pass

    return {
        "org_id": str(org_id),
        "user_count": len(users),
        "knowledge_health": health,
        "domain_distribution": domain_dist,
        "active_disease_count": len(diseases),
        "disease_severity_avg": (
            sum(d.severity_score for d in diseases) / len(diseases)
            if diseases else 0.0
        ),
        "graph_data": graph_data,
    }


@celery_app.task(name="aion.intelligence.compute_org")
def compute_org(org_id: str) -> dict:
    """On-demand OII computation for a single org."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_async_compute_org(org_id))


async def _async_compute_org(org_id: str) -> dict:
    from uuid import UUID
    from app.core.database import async_session_factory
    from app.ai.algorithms.intelligence_scorer import compute_oii_score

    async with async_session_factory() as session:
        raw = await _collect_oii_data(UUID(org_id), session)
        oii = compute_oii_score(raw)
        return {
            "org_id": org_id,
            "overall_health": oii.overall,
            "dimensions": {
                "knowledge_velocity": oii.knowledge_velocity,
                "knowledge_coverage": oii.knowledge_coverage,
                "knowledge_quality": oii.knowledge_quality,
                "learning_agility": oii.learning_agility,
                "collaboration_density": oii.collaboration_density,
                "innovation_index": oii.innovation_index,
                "decision_intelligence": oii.decision_intelligence,
                "cognitive_resilience": oii.cognitive_resilience,
                "knowledge_accessibility": oii.knowledge_accessibility,
                "expertise_depth": oii.expertise_depth,
                "knowledge_retention": oii.knowledge_retention,
                "adaptability_score": oii.adaptability_score,
            },
            "proprietary": {
                "knowledge_half_life": oii.knowledge_half_life,
                "knowledge_entropy": oii.knowledge_entropy,
                "memory_compression": oii.memory_compression,
            },
        }
