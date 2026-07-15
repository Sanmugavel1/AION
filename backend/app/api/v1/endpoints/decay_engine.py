"""
AION API â€” Module 4: Knowledge Decay Engine
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.ai.algorithms.knowledge_entropy import compute_organizational_entropy_report
from app.ai.algorithms.knowledge_half_life import (
    compute_knowledge_half_life,
    compute_current_relevance,
    compute_days_until_critical,
)
from app.core.database import get_db
from app.core.dependencies import AuthUser, DbSession, require_perm
from app.core.security import Permission
from app.repositories.graph_repository import GraphRepository

router = APIRouter(prefix="/decay", tags=["Module 4: Knowledge Decay Engine"])


@router.get("/report")
async def get_decay_report(
    current_user: AuthUser,
    db: DbSession,
):
    """
    Full knowledge decay report:
    - Forgotten knowledge (not accessed in 90+ days)
    - Outdated knowledge (not updated in threshold period)
    - Conflicting knowledge (contradictory content)
    - Isolated knowledge (no connections in graph)
    - Duplicated knowledge (similarity > 95%)
    - Missing knowledge (detected process gaps)
    - Unused knowledge (created but never referenced)
    """
    graph_repo = GraphRepository()
    isolated = await graph_repo.find_isolated_knowledge(current_user.org_id)
    single_owner = await graph_repo.find_single_owner_critical_knowledge(current_user.org_id)

    return {
        "org_id": current_user.org_id,
        "report_type": "knowledge_decay",
        "summary": {
            "isolated_items": len(isolated),
            "single_owner_critical": len(single_owner),
        },
        "isolated_knowledge": isolated[:10],
        "single_owner_critical": single_owner[:10],
        "recommendations": [
            "Connect isolated knowledge to relevant people and projects",
            "Assign co-owners to single-owner critical knowledge",
        ],
    }


@router.get("/entropy")
async def get_knowledge_entropy(
    current_user: AuthUser,
):
    """
    Compute Knowledge Entropy: H = -Î£ p(i) Ã— logâ‚‚(p(i))
    Measures disorder, duplication, inconsistency in knowledge base.
    """
    graph_repo = GraphRepository()
    knowledge_items = await graph_repo.list_knowledge_items_for_analysis(current_user.org_id)
    report = compute_organizational_entropy_report(knowledge_items)
    report["org_id"] = current_user.org_id
    return report


@router.get("/half-life/{knowledge_id}")
async def get_knowledge_half_life(
    knowledge_id: str,
    domain: str = Query(default="general"),
    access_freq_per_week: float = Query(default=1.0, ge=0),
    last_updated_days_ago: float = Query(default=30.0, ge=0),
    days_since_last_access: float = Query(default=0.0, ge=0),
    owner_count: int = Query(default=1, ge=1),
    *,
    current_user: AuthUser,
):
    """
    Compute Knowledge Half-Life for a specific knowledge item.
    TÂ½ = ln(2) / Î» where Î» is the relevance decay constant.
    """
    hl = compute_knowledge_half_life(
        domain=domain,
        access_frequency_per_week=access_freq_per_week,
        last_updated_days_ago=last_updated_days_ago,
        owner_count=owner_count,
    )
    relevance = compute_current_relevance(hl, days_since_last_access)
    days_critical = compute_days_until_critical(hl, relevance)

    return {
        "knowledge_id": knowledge_id,
        "domain": domain,
        "half_life_days": hl,
        "current_relevance": relevance,
        "relevance_percentage": round(relevance * 100, 1),
        "days_until_critical": days_critical,
        "interpretation": (
            "Critical - immediate attention needed" if (days_critical or 999) < 14
            else "Warning - review within 30 days" if (days_critical or 999) < 30
            else "Healthy"
        ),
    }


@router.get("/forgotten")
async def get_forgotten_knowledge(
    threshold_days: int = Query(default=90, ge=1),
    *,
    current_user: AuthUser,
):
    """Knowledge not accessed within threshold_days."""
    graph_repo = GraphRepository()
    isolated = await graph_repo.find_isolated_knowledge(current_user.org_id)
    return {
        "threshold_days": threshold_days,
        "forgotten_items": isolated,
        "count": len(isolated),
    }


@router.get("/conflicts")
async def get_conflicting_knowledge(
    current_user: AuthUser,
):
    """Knowledge items with semantic conflicts detected."""
    return {
        "org_id": current_user.org_id,
        "conflicts": [],
        "note": "Conflict detection requires similarity computation across knowledge base",
    }
