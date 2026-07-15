"""
AION Celery Worker — Module 5: Organizational Disease Detection
Runs every 6 hours to scan for the 5 organizational diseases
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.core.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    name="aion.disease.detect",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    soft_time_limit=1200,
)
def detect(self) -> dict:
    """
    Every 6 hours: run full disease scan across all organizations.
    Detects: Knowledge Cancer, Memory Alzheimer's, Communication Stroke,
    Knowledge Obesity, Innovation Paralysis.
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_async_disease_detect())


async def _async_disease_detect() -> dict:
    from app.core.database import async_session_factory
    from app.core.neo4j_client import execute_query
    from app.ai.algorithms.disease_classifier import run_full_disease_scan
    from app.models.organization import Organization
    from app.models.disease import DiseaseRecord
    from sqlalchemy import select

    summary = {"orgs_scanned": 0, "diseases_found": 0, "diseases_critical": 0, "errors": []}

    async with async_session_factory() as session:
        orgs_result = await session.execute(
            select(Organization).where(Organization.is_active.is_(True))
        )
        orgs = orgs_result.scalars().all()

        for org in orgs:
            try:
                org_data = await _collect_org_data(org.id, session)
                scan_result = run_full_disease_scan(org_data)

                for disease in scan_result.get("diseases", []):
                    if disease["severity_score"] > 0.1:
                        record = DiseaseRecord(
                            org_id=org.id,
                            disease_type=disease["type"],
                            severity=disease["severity"],
                            severity_score=disease["severity_score"],
                            confidence=disease.get("confidence", 0.8),
                            evidence=disease.get("evidence", {}),
                            detected_at=datetime.now(timezone.utc),
                        )
                        session.add(record)
                        summary["diseases_found"] += 1
                        if disease["severity"] == "critical":
                            summary["diseases_critical"] += 1

                await session.commit()
                summary["orgs_scanned"] += 1
                logger.info("Disease scan completed", org_id=str(org.id))
            except Exception as e:
                logger.error("Disease scan failed", org_id=str(org.id), error=str(e))
                summary["errors"].append({"org_id": str(org.id), "error": str(e)})
                await session.rollback()

    summary["timestamp"] = datetime.now(timezone.utc).isoformat()
    return summary


async def _collect_org_data(org_id, session) -> dict:
    """Collect the raw org data needed for disease scanning."""
    from app.repositories.knowledge_repository import KnowledgeRepository
    from app.repositories.user_repository import UserRepository
    from app.core.neo4j_client import execute_query

    knowledge_repo = KnowledgeRepository(session)
    user_repo = UserRepository(session)

    health = await knowledge_repo.get_health_summary(org_id)
    users = await user_repo.get_by_org(org_id, limit=1000)
    domain_dist = await knowledge_repo.get_domain_distribution(org_id)

    # Graph metrics
    graph_stats = {}
    try:
        records = await execute_query(
            """
            MATCH (p:Person {org_id: $org_id})
            OPTIONAL MATCH (p)-[r:COLLABORATES_WITH]->()
            RETURN count(DISTINCT p) AS person_count,
                   count(r) AS collaboration_count,
                   avg(size((p)-[:KNOWS]->())) AS avg_knowledge_per_person
            """,
            {"org_id": str(org_id)},
        )
        if records:
            graph_stats = dict(records[0])
    except Exception:
        pass

    return {
        "org_id": str(org_id),
        "knowledge_health": health,
        "user_count": len(users),
        "domain_distribution": domain_dist,
        "graph_stats": graph_stats,
        "departments": [],
    }


@celery_app.task(name="aion.disease.scan_org")
def scan_single_org(org_id: str) -> dict:
    """On-demand disease scan for a single org."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_async_scan_org(org_id))


async def _async_scan_org(org_id: str) -> dict:
    from uuid import UUID
    from app.core.database import async_session_factory
    from app.ai.algorithms.disease_classifier import run_full_disease_scan

    async with async_session_factory() as session:
        data = await _collect_org_data(UUID(org_id), session)
        return run_full_disease_scan(data)
