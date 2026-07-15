"""
AION API â€” Module 7: Self-Healing AI
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.healing_agent import SelfHealingAgent
from app.ai.algorithms.disease_classifier import run_full_disease_scan
from app.core.database import get_db
from app.core.dependencies import AuthUser, DbSession, require_perm
from app.core.security import Permission
from app.models.simulation import HealingAction
from app.repositories.graph_repository import GraphRepository

router = APIRouter(prefix="/healing", tags=["Module 7: Self-Healing AI"])


@router.get("/recommendations")
async def get_healing_recommendations(
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    *,
    current_user: AuthUser,
    db: DbSession,
):
    """
    Get all healing recommendations.
    Actions: create_sop, assign_mentor, schedule_training, merge_docs,
    archive_files, notify_managers, generate_onboarding, create_quiz,
    update_wiki, knowledge_transfer.
    Status: pending | approved | in_progress | completed | rejected
    """
    stmt = select(HealingAction).where(HealingAction.org_id == UUID(current_user.org_id))
    if status_filter:
        stmt = stmt.where(HealingAction.status == status_filter)
    if priority:
        stmt = stmt.where(HealingAction.priority == priority)

    result = await db.execute(stmt)
    actions = result.scalars().all()

    return {
        "recommendations": [
            {
                "id": str(a.id),
                "action_type": a.action_type,
                "title": a.title,
                "description": a.description,
                "priority": a.priority,
                "status": a.status,
                "estimated_impact": a.estimated_impact,
                "created_at": a.created_at.isoformat(),
            }
            for a in actions
        ],
        "total": len(actions),
    }


@router.post("/recommendations/{recommendation_id}/approve")
async def approve_recommendation(
    recommendation_id: str,
    current_user: AuthUser,
    db: DbSession,
):
    """
    Approve a healing recommendation. Human approval is ALWAYS required.
    AION prepares the plan; humans decide whether to execute.
    """
    try:
        rec_uuid = UUID(recommendation_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    stmt = select(HealingAction).where(
        HealingAction.id == rec_uuid,
        HealingAction.org_id == UUID(current_user.org_id),
    )
    result = await db.execute(stmt)
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if action.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot approve action in status: {action.status}")

    stmt = update(HealingAction).where(HealingAction.id == rec_uuid).values(
        status="approved",
        approved_by=UUID(current_user.user_id),
        approved_at=datetime.now(timezone.utc),
    )
    await db.execute(stmt)
    await db.commit()

    return {
        "status": "approved",
        "recommendation_id": recommendation_id,
        "next_step": "No automatic execution - this is a human-in-the-loop action. "
        "Carry it out, then call POST /recommendations/{id}/complete to close it out.",
    }


@router.post("/recommendations/{recommendation_id}/complete")
async def complete_recommendation(
    recommendation_id: str,
    outcome: Optional[str] = None,
    *,
    current_user: AuthUser,
    db: DbSession,
):
    """Mark an approved healing action as completed, once a human has actually carried it out."""
    try:
        rec_uuid = UUID(recommendation_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    stmt = select(HealingAction).where(
        HealingAction.id == rec_uuid,
        HealingAction.org_id == UUID(current_user.org_id),
    )
    result = await db.execute(stmt)
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if action.status not in ("approved", "in_progress"):
        raise HTTPException(status_code=400, detail=f"Cannot complete action in status: {action.status}")

    stmt = update(HealingAction).where(HealingAction.id == rec_uuid).values(
        status="completed", outcome=outcome, completed_at=datetime.now(timezone.utc)
    )
    await db.execute(stmt)
    await db.commit()
    return {"status": "completed", "recommendation_id": recommendation_id}


@router.post("/recommendations/{recommendation_id}/reject")
async def reject_recommendation(
    recommendation_id: str,
    reason: Optional[str] = None,
    *,
    current_user: AuthUser,
    db: DbSession,
):
    """Reject a healing recommendation."""
    try:
        rec_uuid = UUID(recommendation_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    stmt = select(HealingAction).where(
        HealingAction.id == rec_uuid,
        HealingAction.org_id == UUID(current_user.org_id),
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    stmt = update(HealingAction).where(HealingAction.id == rec_uuid).values(
        status="rejected", outcome=reason
    )
    await db.execute(stmt)
    await db.commit()
    return {"status": "rejected", "recommendation_id": recommendation_id}


@router.post("/generate")
async def generate_recommendations(
    current_user: AuthUser,
    db: DbSession,
):
    """
    Trigger the Self-Healing AI to generate new recommendations
    based on current disease scan and decay report.
    """
    graph_repo = GraphRepository()
    scan_inputs = await graph_repo.build_disease_scan_inputs(current_user.org_id)
    disease_report = run_full_disease_scan(**scan_inputs)

    isolated = await graph_repo.find_isolated_knowledge(current_user.org_id)

    agent = SelfHealingAgent()
    recommendations = await agent.run(
        org_id=current_user.org_id,
        disease_reports=list(disease_report["diseases"].values()),
        decay_report={"forgotten_count": len(isolated), "conflict_count": 0},
        ocsie_alerts=[],
    )

    # Store recommendations
    created = []
    for rec in recommendations:
        action = HealingAction(
            org_id=UUID(current_user.org_id),
            action_type=rec["action_type"],
            title=rec["title"],
            description=rec["description"],
            priority=rec["priority"],
            status="pending",
            parameters=rec.get("parameters", {}),
            target_entities=rec.get("target_entities", []),
        )
        db.add(action)
        created.append(rec)

    await db.commit()
    return {"generated": len(created), "recommendations": created}
