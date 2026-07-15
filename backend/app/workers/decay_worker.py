"""
AION Celery Worker — Module 4: Knowledge Decay Engine
Runs every hour to compute half-lives and flag outdated knowledge
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.core.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    name="aion.decay.scan",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    soft_time_limit=600,
)
def scan(self) -> dict:
    """
    Hourly decay scan across all organizations.
    1. Load all active knowledge items
    2. Compute T½ using domain volatility + access patterns
    3. Update relevance scores: R(t) = R₀ × 2^(-t/T½)
    4. Flag items below threshold as is_outdated
    5. Emit decay events to Kafka
    """
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_async_decay_scan())


async def _async_decay_scan() -> dict:
    from datetime import timedelta
    from app.core.database import async_session_factory
    from app.ai.algorithms.knowledge_half_life import (
        compute_knowledge_half_life,
        compute_current_relevance,
        compute_days_until_critical,
    )
    from app.repositories.knowledge_repository import KnowledgeRepository
    from app.repositories.base_repository import BaseRepository
    from app.models.organization import Organization
    from sqlalchemy import select

    results = {"orgs_processed": 0, "items_updated": 0, "items_flagged": 0, "errors": []}

    async with async_session_factory() as session:
        orgs_result = await session.execute(
            select(Organization).where(Organization.is_active.is_(True))
        )
        orgs = orgs_result.scalars().all()

        for org in orgs:
            try:
                repo = KnowledgeRepository(session)
                # Get all active items
                items = await repo.list(filters={"org_id": org.id, "is_active": True}, limit=10000)

                updates = []
                flagged = 0
                for item in items:
                    hl_result = compute_knowledge_half_life(
                        domain=item.domain,
                        last_accessed_at=item.last_accessed_at,
                        access_count=item.access_count,
                        is_documented=bool(item.item_metadata and item.item_metadata.get("is_documented")),
                        owner_count=item.item_metadata.get("owner_count", 1) if item.item_metadata else 1,
                        content_age_days=(
                            (datetime.now(timezone.utc) - item.created_at).days
                        ),
                    )
                    new_relevance = compute_current_relevance(
                        r0=1.0,
                        half_life_days=hl_result["half_life_days"],
                        days_elapsed=(
                            (datetime.now(timezone.utc) - item.created_at).days
                        ),
                    )
                    is_outdated = new_relevance < 0.3
                    if is_outdated:
                        flagged += 1
                    updates.append({
                        "id": item.id,
                        "relevance_score": round(new_relevance, 4),
                        "decay_rate": hl_result.get("lambda"),
                        "is_outdated": is_outdated,
                    })

                updated = await repo.bulk_update_relevance(updates)
                await session.commit()

                results["orgs_processed"] += 1
                results["items_updated"] += updated
                results["items_flagged"] += flagged

                logger.info(
                    "Decay scan completed for org",
                    org_id=str(org.id),
                    items=updated,
                    flagged=flagged,
                )
            except Exception as e:
                logger.error("Decay scan failed for org", org_id=str(org.id), error=str(e))
                results["errors"].append({"org_id": str(org.id), "error": str(e)})

    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    return results


@celery_app.task(name="aion.decay.compute_item_halflife")
def compute_item_halflife(item_id: str, org_id: str) -> dict:
    """Compute and update half-life for a single knowledge item on-demand."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(
        _async_compute_item(item_id, org_id)
    )


async def _async_compute_item(item_id: str, org_id: str) -> dict:
    from uuid import UUID
    from app.core.database import async_session_factory
    from app.ai.algorithms.knowledge_half_life import compute_knowledge_half_life, compute_current_relevance
    from app.repositories.knowledge_repository import KnowledgeRepository

    async with async_session_factory() as session:
        repo = KnowledgeRepository(session)
        item = await repo.get(UUID(item_id))
        if not item:
            return {"error": "Item not found"}

        hl = compute_knowledge_half_life(
            domain=item.domain,
            last_accessed_at=item.last_accessed_at,
            access_count=item.access_count,
        )
        relevance = compute_current_relevance(
            r0=1.0,
            half_life_days=hl["half_life_days"],
            days_elapsed=(datetime.now(timezone.utc) - item.created_at).days,
        )
        await repo.update(item.id, relevance_score=relevance)
        await session.commit()
        return {"item_id": item_id, **hl, "current_relevance": relevance}
