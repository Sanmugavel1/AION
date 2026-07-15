"""
AION API â€” Module 13: Organizational MRI â€” The Signature Feature
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import AuthUser, DbSession, require_perm
from app.core.security import Permission
from app.repositories.graph_repository import GraphRepository
from app.services.mri_service import MRIService

router = APIRouter(prefix="/mri", tags=["Module 13: Organizational MRI"])


def get_mri_service() -> MRIService:
    return MRIService(graph_repo=GraphRepository())


@router.get("/brain-map")
async def get_brain_map(
    current_user: AuthUser,
):
    """
    THE SIGNATURE FEATURE: Full organizational brain map.
    Returns color-coded graph data for visualization:
    Green = healthy, Yellow = weakening, Red = critical.
    """
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
