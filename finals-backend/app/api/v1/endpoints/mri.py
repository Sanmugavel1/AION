"""
AION API â€” Module 13: Organizational MRI â€” The Signature Feature
"""
from __future__ import annotations

import uuid
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.dependencies import AuthUser, DbSession, require_perm
from app.core.security import Permission
from app.models.knowledge import KnowledgeItem
from app.models.user import User
from app.models.workplace import EmployeeProfileDetail
from app.repositories.graph_repository import GraphRepository
from app.services.mri_service import MRIService

router = APIRouter(prefix="/mri", tags=["Module 13: Organizational MRI"])


def get_mri_service() -> MRIService:
    return MRIService(graph_repo=GraphRepository())


async def _department_brain_map(db, org_id: str, dept_id: str) -> dict:
    """A department head's brain map — only their own people and their work.

    Built from live records (this department's members, the documents they wrote,
    and the projects they are on), so a head sees their team, not the whole company.
    Same node/edge shape the org-wide map uses, so it renders identically.
    """
    org = uuid.UUID(org_id)
    dep = uuid.UUID(dept_id)
    people = (
        await db.execute(
            select(User).where(User.dept_id == dep, User.is_active.is_(True))
        )
    ).scalars().all()
    pids = {str(p.id) for p in people}
    details = {
        str(d.user_id): d
        for d in (
            await db.execute(
                select(EmployeeProfileDetail).where(
                    EmployeeProfileDetail.user_id.in_([p.id for p in people] or [uuid.uuid4()])
                )
            )
        ).scalars().all()
    }
    items = (
        await db.execute(
            select(KnowledgeItem).where(
                KnowledgeItem.org_id == org, KnowledgeItem.dept_id == dep
            )
        )
    ).scalars().all()

    nodes = [
        {"id": str(p.id), "type": "Person", "label": p.full_name or p.email,
         "health_color": "green", "connection_count": 0}
        for p in people
    ]
    edges = []

    # Documents this department owns, tied to whoever wrote them.
    for it in items:
        owner = str(it.submitted_by_id) if it.submitted_by_id and str(it.submitted_by_id) in pids else None
        nodes.append({
            "id": str(it.id), "type": "Knowledge", "label": it.title,
            "health_color": "yellow" if owner else "red",
            "connection_count": 1 if owner else 0,
        })
        if owner:
            edges.append({"source": owner, "target": str(it.id)})

    # Projects — who is doing what, from each member's profile.
    projects: dict[str, set] = {}
    for p in people:
        d = details.get(str(p.id))
        names = []
        if d:
            names += (d.current_projects or {}).get("names", [])
            names += (d.completed_projects or {}).get("names", [])
        for nm in names:
            projects.setdefault(nm, set()).add(str(p.id))
    for nm, owners in projects.items():
        nid = "proj:" + nm
        nodes.append({
            "id": nid, "type": "Project", "label": nm,
            "health_color": "green" if len(owners) > 1 else "yellow",
            "connection_count": len(owners),
        })
        for o in owners:
            edges.append({"source": o, "target": nid})

    cc = Counter(e["source"] for e in edges)
    for n in nodes:
        if n["type"] == "Person":
            n["connection_count"] = cc.get(n["id"], 0)

    reds = sum(1 for n in nodes if n["health_color"] == "red")
    yellows = sum(1 for n in nodes if n["health_color"] == "yellow")
    greens = sum(1 for n in nodes if n["health_color"] == "green")
    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "total_nodes": len(nodes),
            "total_connections": len(edges),
            "green_nodes": greens, "yellow_nodes": yellows, "red_nodes": reds,
            "scope": "department",
        },
    }


@router.get("/brain-map")
async def get_brain_map(current_user: AuthUser, db: DbSession):
    """
    THE SIGNATURE FEATURE: the organizational brain map.
    A department head (department-scoped) sees only their own team and its work;
    the admin and executives see the whole organization.
    Green = healthy, Yellow = weakening, Red = critical.
    """
    if current_user.is_department_scoped and current_user.dept_id:
        return await _department_brain_map(db, current_user.org_id, current_user.dept_id)
    service = get_mri_service()
    return await service.get_brain_map(current_user.org_id)


@router.get("/knowledge-flow")
async def get_knowledge_flow(
    current_user: AuthUser,
):
    """Knowledge flow between departments â€” who shares with whom."""
    service = get_mri_service()
    return await service.get_knowledge_flow(current_user.org_id)


@router.get("/bottlenecks")
async def get_knowledge_bottlenecks(
    current_user: AuthUser,
):
    """Single-person knowledge dependencies â€” critical organizational risk."""
    service = get_mri_service()
    return await service.get_knowledge_bottlenecks(current_user.org_id)


@router.get("/dependencies")
async def get_single_person_dependencies(
    current_user: AuthUser,
):
    """All employees where departure would cause critical knowledge loss."""
    graph_repo = GraphRepository()
    return await graph_repo.find_single_owner_critical_knowledge(current_user.org_id)


@router.get("/innovation-centers")
async def get_innovation_centers(
    current_user: AuthUser,
):
    """Where ideas cluster â€” the innovation hotspots of the organization."""
    service = get_mri_service()
    return await service.get_innovation_centers(current_user.org_id)


@router.get("/black-holes")
async def get_knowledge_black_holes(
    current_user: AuthUser,
):
    """Knowledge that is stored but never referenced or shared."""
    service = get_mri_service()
    return await service.get_knowledge_black_holes(current_user.org_id)


@router.get("/timeline-forecast")
async def get_timeline_forecast(
    current_user: AuthUser,
    db: DbSession,
):
    """3, 6, and 12-month organizational brain health forecast."""
    service = get_mri_service()
    return await service.get_timeline_forecast(current_user.org_id, db=db)
