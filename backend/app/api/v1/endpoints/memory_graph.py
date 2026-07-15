"""
AION API â€” Module 2: Organizational Memory Graph
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

from app.core.dependencies import AuthUser, DbSession, require_perm
from app.core.security import Permission
from app.repositories.graph_repository import GraphRepository

router = APIRouter(prefix="/graph", tags=["Module 2: Memory Graph"])


class CreatePersonRequest(BaseModel):
    user_id: str
    name: str
    email: str
    department: Optional[str] = None
    role: Optional[str] = None
    expertise: Optional[List[str]] = None


class CreateDepartmentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class BulkPersonEntry(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    department: Optional[str] = None
    role: Optional[str] = None
    expertise: Optional[List[str]] = None


class BulkCreatePersonRequest(BaseModel):
    people: List[BulkPersonEntry] = Field(..., min_length=1, max_length=500)


class BulkPolicyEntry(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    summary: Optional[str] = Field(None, max_length=4000)
    department: Optional[str] = None
    tags: Optional[List[str]] = None


class BulkCreatePolicyRequest(BaseModel):
    policies: List[BulkPolicyEntry] = Field(..., min_length=1, max_length=200)


class CreateKnowledgeRequest(BaseModel):
    knowledge_id: str
    title: str
    domain: str
    source_type: str = "document"
    summary: Optional[str] = None
    tags: Optional[List[str]] = None


class CreateRelationshipRequest(BaseModel):
    from_id: str
    to_id: str
    relationship_type: str
    properties: Optional[dict] = None


@router.get("/nodes")
async def list_graph_nodes(
    node_type: Optional[str] = Query(None, description="Person | Knowledge | Project | Department"),
    limit: int = Query(50, ge=1, le=200),
    *,
    current_user: AuthUser,
):
    """List nodes in the organizational memory graph."""
    graph_repo = GraphRepository()
    brain_map = await graph_repo.get_org_brain_map(current_user.org_id)
    nodes = brain_map.get("nodes", [])
    if node_type:
        nodes = [n for n in nodes if n.get("type") == node_type]
    return {"nodes": nodes[:limit], "total": len(nodes)}


@router.post("/nodes/person")
async def create_person_node(
    request: CreatePersonRequest,
    current_user: AuthUser,
):
    """Create or update a Person node in the knowledge graph."""
    graph_repo = GraphRepository()
    node = await graph_repo.create_person_node(
        user_id=request.user_id,
        org_id=current_user.org_id,
        name=request.name,
        email=request.email,
        department=request.department,
        role=request.role,
        expertise=request.expertise,
    )
    return {"status": "created", "node": node}


@router.post("/nodes/department")
async def create_department_node_endpoint(
    request: CreateDepartmentRequest,
    current_user: AuthUser,
):
    """Create a Department node for this organization."""
    graph_repo = GraphRepository()
    existing = await graph_repo.list_departments(current_user.org_id)
    if any(d["name"].strip().lower() == request.name.strip().lower() for d in existing):
        raise HTTPException(status_code=409, detail=f"Department '{request.name}' already exists")

    dept_id = str(uuid.uuid4())
    node = await graph_repo.create_department_node(dept_id, current_user.org_id, request.name)
    return {"status": "created", "node": node}


@router.get("/departments")
async def list_departments_endpoint(
    current_user: AuthUser,
):
    """List all departments with live headcount and knowledge-item counts."""
    graph_repo = GraphRepository()
    departments = await graph_repo.list_departments(current_user.org_id)
    return {"departments": departments, "total": len(departments)}


@router.post("/nodes/person/bulk")
async def bulk_create_person_nodes(
    request: BulkCreatePersonRequest,
    current_user: AuthUser,
):
    """Create many Person nodes at once (e.g. importing a department roster)."""
    graph_repo = GraphRepository()
    created = []
    for entry in request.people:
        node = await graph_repo.create_person_node(
            user_id=str(uuid.uuid4()),
            org_id=current_user.org_id,
            name=entry.name,
            email=entry.email,
            department=entry.department,
            role=entry.role,
            expertise=entry.expertise,
        )
        created.append(node)
    return {"status": "created", "count": len(created), "nodes": created}


@router.get("/policies")
async def list_policies_endpoint(
    department: Optional[str] = Query(None, description="Filter policies by department name"),
    *,
    current_user: AuthUser,
):
    """List organizational policies, optionally filtered by department."""
    graph_repo = GraphRepository()
    policies = await graph_repo.list_policies(current_user.org_id, department=department)
    return {"policies": policies, "total": len(policies)}


@router.post("/nodes/policy/bulk")
async def bulk_create_policy_nodes(
    request: BulkCreatePolicyRequest,
    current_user: AuthUser,
):
    """Create many organizational policy documents at once, scoped to a department."""
    graph_repo = GraphRepository()
    created = []
    for entry in request.policies:
        node = await graph_repo.create_knowledge_node(
            knowledge_id=str(uuid.uuid4()),
            org_id=current_user.org_id,
            title=entry.title,
            domain="policy",
            source_type="policy_document",
            summary=entry.summary,
            tags=entry.tags,
            department=entry.department,
        )
        created.append(node)
    return {"status": "created", "count": len(created), "nodes": created}


@router.post("/nodes/knowledge")
async def create_knowledge_node(
    request: CreateKnowledgeRequest,
    current_user: AuthUser,
):
    """Create or update a Knowledge node in the memory graph."""
    graph_repo = GraphRepository()
    node = await graph_repo.create_knowledge_node(
        knowledge_id=request.knowledge_id,
        org_id=current_user.org_id,
        title=request.title,
        domain=request.domain,
        source_type=request.source_type,
        summary=request.summary,
        tags=request.tags,
    )
    return {"status": "created", "node": node}


@router.post("/relationships")
async def create_relationship(
    request: CreateRelationshipRequest,
    current_user: AuthUser,
):
    """Create a relationship between two graph nodes."""
    graph_repo = GraphRepository()
    props = request.properties or {}

    if request.relationship_type == "KNOWS":
        result = await graph_repo.create_knows_relationship(
            request.from_id, request.to_id,
            strength=props.get("strength", 0.5),
            role=props.get("role", "contributor"),
        )
    elif request.relationship_type == "CONTRIBUTES_TO":
        result = await graph_repo.create_contributes_to_relationship(
            request.from_id, request.to_id,
            role=props.get("role", "member"),
        )
    elif request.relationship_type == "COLLABORATES_WITH":
        result = await graph_repo.create_collaborates_with_relationship(
            request.from_id, request.to_id,
            channel=props.get("channel", "unknown"),
        )
    else:
        result = False

    return {"status": "created" if result else "failed", "relationship_type": request.relationship_type}


@router.get("/traverse")
async def traverse_graph(
    from_node_id: str,
    relationship_type: Optional[str] = None,
    max_depth: int = Query(3, ge=1, le=6),
    *,
    current_user: AuthUser,
):
    """Traverse the graph from a given node."""
    graph_repo = GraphRepository()
    profile = await graph_repo.get_person_full_profile(from_node_id)
    return {"from_node": from_node_id, "depth": max_depth, "subgraph": profile}


@router.get("/search")
async def search_graph(
    q: str = Query(..., min_length=2, description="Search query"),
    domain: Optional[str] = None,
    *,
    current_user: AuthUser,
):
    """Semantic search across the organizational memory graph."""
    graph_repo = GraphRepository()
    results = await graph_repo.search_knowledge(
        org_id=current_user.org_id,
        query_text=q,
        domain=domain,
    )
    return {"query": q, "results": results, "count": len(results)}
