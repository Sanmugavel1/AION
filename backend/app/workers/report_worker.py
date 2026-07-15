"""
AION Celery Worker — Module 10: Board Advisor Report Generator
Runs every Monday at 08:00 UTC to produce executive intelligence briefings
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.core.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    name="aion.advisor.weekly_report",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    soft_time_limit=1800,
)
def weekly_report(self) -> dict:
    """
    Monday 8am UTC: generate weekly board intelligence briefings for all orgs.
    Stores report as JSON in MinIO and records metadata in DB.
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_async_weekly_report())


async def _async_weekly_report() -> dict:
    from app.core.database import async_session_factory
    from app.models.organization import Organization
    from sqlalchemy import select

    results = {"orgs_reported": 0, "errors": []}

    async with async_session_factory() as session:
        orgs_result = await session.execute(
            select(Organization).where(Organization.is_active.is_(True))
        )
        orgs = orgs_result.scalars().all()

        for org in orgs:
            try:
                report = await _generate_org_report(org.id, org.name, session)
                await _store_report(org.id, report)
                results["orgs_reported"] += 1
                logger.info("Weekly report generated", org_id=str(org.id))
            except Exception as e:
                logger.error("Report generation failed", org_id=str(org.id), error=str(e))
                results["errors"].append({"org_id": str(org.id), "error": str(e)})

    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    return results


async def _generate_org_report(org_id, org_name: str, session) -> dict:
    """Generate the full 10-section board report for an organization."""
    from app.repositories.knowledge_repository import KnowledgeRepository
    from app.repositories.disease_repository import (
        DiseaseRepository, IntelligenceSnapshotRepository
    )
    from app.ai.llm.llm_client import generate_board_narrative

    k_repo = KnowledgeRepository(session)
    d_repo = DiseaseRepository(session)
    i_repo = IntelligenceSnapshotRepository(session)

    health = await k_repo.get_health_summary(org_id)
    diseases = await d_repo.get_active_diseases(org_id)
    latest_oii = await i_repo.get_latest(org_id)
    oii_history = await i_repo.get_history(org_id, limit=4)

    diseases_data = [
        {
            "type": d.disease_type,
            "severity": d.severity,
            "score": d.severity_score,
        }
        for d in diseases
    ]

    metrics = {
        "overall_health": latest_oii.overall_health if latest_oii else 0.5,
        "knowledge_health_ratio": health.get("health_ratio", 0.5),
        "total_knowledge_items": health.get("total", 0),
        "active_diseases": len(diseases),
    }

    risks = [
        f"{d['type']} at {d['severity']} severity ({d['score']:.0%})"
        for d in diseases_data
        if d["score"] > 0.3
    ][:5]

    opportunities = _derive_opportunities(health, latest_oii)

    narrative = await generate_board_narrative(metrics, risks, opportunities)

    # OII trend
    trend = "stable"
    if len(oii_history) >= 2:
        delta = oii_history[0].overall_health - oii_history[-1].overall_health
        trend = "improving" if delta > 0.05 else "declining" if delta < -0.05 else "stable"

    return {
        "org_id": str(org_id),
        "org_name": org_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report_type": "weekly_board_briefing",
        "sections": {
            "executive_summary": narrative,
            "oii_score": metrics["overall_health"],
            "oii_trend": trend,
            "knowledge_health": health,
            "active_diseases": diseases_data,
            "top_risks": risks,
            "top_opportunities": opportunities,
            "dimensions": {
                "cognitive_resilience": getattr(latest_oii, "cognitive_resilience", 0) if latest_oii else 0,
                "collaboration_density": getattr(latest_oii, "collaboration_density", 0) if latest_oii else 0,
                "innovation_index": getattr(latest_oii, "innovation_index", 0) if latest_oii else 0,
            },
        },
    }


def _derive_opportunities(health: dict, oii) -> list[str]:
    opportunities = []
    if health.get("isolated", 0) > 10:
        opportunities.append(
            f"Connect {health['isolated']} isolated knowledge nodes to improve coverage"
        )
    if health.get("avg_relevance_score", 1.0) < 0.6:
        opportunities.append("Knowledge refresh program could boost OII by 10-15 points")
    if oii and getattr(oii, "collaboration_density", 1.0) < 0.5:
        opportunities.append("Cross-departmental collaboration initiatives show high ROI potential")
    return opportunities[:5]


async def _store_report(org_id, report: dict) -> None:
    """Store report JSON in MinIO."""
    import json
    from app.core.minio_client import upload_file
    key = f"{org_id}/reports/{report['generated_at'][:10]}_weekly.json"
    try:
        await upload_file(
            "reports", key, json.dumps(report).encode(), content_type="application/json"
        )
    except Exception as e:
        logger.warning("Failed to store report in MinIO", error=str(e))


@celery_app.task(name="aion.advisor.generate_org_report")
def generate_org_report(org_id: str) -> dict:
    """On-demand report generation for a single org."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_async_on_demand_report(org_id))


async def _async_on_demand_report(org_id: str) -> dict:
    from uuid import UUID
    from app.core.database import async_session_factory
    from app.models.organization import Organization
    from sqlalchemy import select

    async with async_session_factory() as session:
        result = await session.execute(select(Organization).where(Organization.id == UUID(org_id)))
        org = result.scalar_one_or_none()
        if not org:
            return {"error": "Organization not found"}
        return await _generate_org_report(UUID(org_id), org.name, session)
