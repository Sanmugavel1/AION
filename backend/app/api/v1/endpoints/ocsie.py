"""
AION API â€” Module 11: OCSIE (Organizational Continuity & Successor Intelligence Engine)
THE MOST IMPORTANT MODULE
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.core.dependencies import AuthUser, DbSession, require_perm
from app.core.security import Permission
from app.repositories.graph_repository import GraphRepository
from app.services.ocsie_service import OCSIEService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ocsie", tags=["Module 11: OCSIE"])


def get_ocsie_service(db: DbSession) -> OCSIEService:
    return OCSIEService(db=db, graph_repo=GraphRepository())


@router.get("/employee/{employee_id}/profile")
async def get_employee_knowledge_profile(
    employee_id: str,
    current_user: AuthUser,
    db: DbSession,
):
    """
    Get the complete Employee Knowledge DNA Profile.
    Continuously updated â€” never reactive.
    Includes work responsibilities, decision history, work style, technical expertise,
    hidden knowledge, and collaboration network.
    """
    service = get_ocsie_service(db)
    profile = await service.get_employee_knowledge_profile(employee_id, current_user.org_id)
    if "error" in profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=profile["error"])
    return profile


@router.get("/continuity-report/{employee_id}")
async def get_continuity_report(
    employee_id: str,
    current_user: AuthUser,
    db: DbSession,
):
    """
    Generate the full 10-section Continuity Intelligence Report.
    Sections: Employee Knowledge DNA, Active Projects, Unfinished Work,
    How This Person Thinks, Hidden Knowledge, Successor Roadmap,
    AI Mentor Mode, Knowledge Gap Analysis, Business Impact, Continuous Backup.
    """
    service = get_ocsie_service(db)
    report = await service.generate_continuity_report(employee_id, current_user.org_id)
    return report


@router.post("/transition/{employee_id}")
async def initiate_departure(
    employee_id: str,
    departure_date: Optional[datetime] = None,
    reason: str = "resignation",
    *,
    current_user: AuthUser,
    db: DbSession,
):
    """
    Initiate departure protocol for an employee.
    Triggers full OCSIE emergency protocol:
    - Generates Continuity Intelligence Report
    - Activates Knowledge Inheritance Engine
    - Notifies relevant managers
    - Creates successor learning roadmap
    """
    service = get_ocsie_service(db)
    result = await service.initiate_departure(
        employee_id, current_user.org_id, departure_date, reason
    )
    return result


@router.get("/unfinished-work/{employee_id}")
async def get_unfinished_work(
    employee_id: str,
    current_user: AuthUser,
    db: DbSession,
):
    """
    Get all unfinished work: pending approvals, open PRs, unanswered emails,
    waiting customer requests, draft documents, incomplete analyses, blocked workflows.
    """
    service = get_ocsie_service(db)
    result = await service._detect_unfinished_work(employee_id)
    return result


@router.get("/successor-roadmap/{employee_id}")
async def get_successor_roadmap(
    employee_id: str,
    current_user: AuthUser,
    db: DbSession,
):
    """
    Get structured week-by-week successor learning roadmap.
    Week 1: Read docs, meet teammates. Week 2: Guided tasks. Week 3: Independent.
    """
    service = get_ocsie_service(db)
    profile = await service.get_employee_knowledge_profile(employee_id, current_user.org_id)
    return service._generate_successor_roadmap(profile)


@router.get("/knowledge-gap/{from_employee_id}/{to_employee_id}")
async def get_knowledge_gap(
    from_employee_id: str,
    to_employee_id: str,
    current_user: AuthUser,
    db: DbSession,
):
    """
    Analyze knowledge gap between outgoing and incoming employee.
    Identifies missing: technical skills, domain knowledge, customer knowledge,
    certifications, responsibilities.
    """
    service = get_ocsie_service(db)
    gaps = await service._analyze_knowledge_gaps(from_employee_id, current_user.org_id)
    return {
        "from_employee_id": from_employee_id,
        "to_employee_id": to_employee_id,
        "gap_analysis": gaps,
    }


@router.get("/business-impact/{employee_id}")
async def get_business_impact(
    employee_id: str,
    current_user: AuthUser,
    db: DbSession,
):
    """
    Estimate business impact if this employee becomes unavailable.
    Returns: project delays, revenue risk, customer impact, team workload,
    knowledge loss severity, expected recovery time.
    """
    graph_repo = GraphRepository()
    impact = await graph_repo.simulate_person_departure(employee_id, current_user.org_id)
    orphaned = impact.get("orphaned_knowledge_count", 0)
    return {
        "employee_id": employee_id,
        "orphaned_knowledge_items": orphaned,
        "affected_projects": impact.get("affected_projects", []),
        "revenue_risk_estimate_usd": orphaned * 5000,
        "recovery_time_days": orphaned * 5,
        "knowledge_loss_severity": (
            "critical" if orphaned >= 20 else "high" if orphaned >= 10 else "medium" if orphaned >= 5 else "low"
        ),
        "immediate_actions": [
            "Activate Knowledge Inheritance Engine",
            "Generate Continuity Intelligence Report",
            "Begin successor learning roadmap",
        ],
    }
