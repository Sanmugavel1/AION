"""
AION API â€” Module 5: Organizational Disease Detection
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.ai.algorithms.disease_classifier import (
    detect_knowledge_cancer,
    detect_memory_alzheimers,
    detect_communication_stroke,
    detect_knowledge_obesity,
    detect_innovation_paralysis,
    run_full_disease_scan,
)
from app.core.database import get_db
from app.core.dependencies import AuthUser, DbSession, require_perm
from app.core.security import Permission
from app.repositories.graph_repository import GraphRepository

router = APIRouter(prefix="/diseases", tags=["Module 5: Disease Detection"])


@router.get("/scan")
async def run_disease_scan(
    current_user: AuthUser,
    db: DbSession,
):
    """
    Run a full organizational disease scan.
    Detects all 5 diseases: Knowledge Cancer, Memory Alzheimer's,
    Communication Stroke, Knowledge Obesity, Innovation Paralysis.
    Returns severity scores and timeline predictions for each.

    Knowledge Obesity and Communication Stroke are computed from real graph
    data. Knowledge Cancer (needs embedding similarity), Memory Alzheimer's
    (needs departure history), and Innovation Paralysis (needs idea tracking)
    have no data source in the current graph schema yet, so they correctly
    report "insufficient data" rather than a fabricated score.
    """
    graph_repo = GraphRepository()
    inputs = await graph_repo.build_disease_scan_inputs(current_user.org_id)
    report = run_full_disease_scan(**inputs)
    report["org_id"] = current_user.org_id
    return report


@router.get("/report")
async def get_disease_report(
    current_user: AuthUser,
    db: DbSession,
):
    """Get the latest disease detection report with all 5 diseases."""
    return await run_disease_scan(current_user=current_user, db=db)


@router.get("/timeline")
async def get_disease_timeline(
    current_user: AuthUser,
):
    """Get timeline prediction for when each disease will become critical."""
    return {
        "org_id": current_user.org_id,
        "predictions": {
            "knowledge_cancer": {"days_until_critical": None, "status": "scan_required"},
            "memory_alzheimers": {"days_until_critical": None, "status": "scan_required"},
            "communication_stroke": {"days_until_critical": None, "status": "scan_required"},
            "knowledge_obesity": {"days_until_critical": None, "status": "scan_required"},
            "innovation_paralysis": {"days_until_critical": None, "status": "scan_required"},
        },
        "note": "Run disease scan to populate timeline predictions",
    }

@router.get("/{disease_type}")
async def get_specific_disease(
    disease_type: str,
    current_user: AuthUser,
):
    """
    Get details for a specific disease.
    disease_type: knowledge_cancer | memory_alzheimers | communication_stroke | knowledge_obesity | innovation_paralysis
    """
    valid_types = [
        "knowledge_cancer", "memory_alzheimers", "communication_stroke",
        "knowledge_obesity", "innovation_paralysis"
    ]
    if disease_type not in valid_types:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Invalid disease type. Valid: {valid_types}",
        )
    return {
        "disease_type": disease_type,
        "org_id": current_user.org_id,
        "description": {
            "knowledge_cancer": "Duplicate SOPs across teams, hundreds of near-identical documents, version confusion",
            "memory_alzheimers": "Senior employees leaving with no documentation of how work was actually done",
            "communication_stroke": "Departments stop sharing information with each other",
            "knowledge_obesity": "Too much information accumulated over time, nobody can find what they need",
            "innovation_paralysis": "Same ideas repeated across teams and time, no genuinely new solutions emerging",
        }[disease_type],
        "status": "scan_required",
        "note": "Run POST /api/v1/diseases/scan to get current severity data",
    }
