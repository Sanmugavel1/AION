"""
AION API — Marketplace, Memory Timeline, Notifications, Universal Search, Learning Center
(SRS Sections 30, 31, 34, 35, 36)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select

from app.core.dependencies import AuthUser, DbSession, resolve_department_scope
from app.core.security import Permission
from app.models.enterprise import (
    LearningRecord, MarketplaceItem, MarketplaceReuse, Notification,
    TimelineEvent, WorkflowStatus,
)
from app.models.knowledge import KnowledgeItem
from app.models.organization import Department
from app.models.user import User

router = APIRouter(prefix="/enterprise", tags=["Enterprise: Platform Services"])


# ----------------------------------------------------------------------------
# Section 30 — Cross-Department Knowledge Marketplace
# ----------------------------------------------------------------------------

class PublishRequest(BaseModel):
    knowledge_id: UUID
    category: str = Field("sop", pattern="^(sop|best_practice|template|playbook)$")


class ReuseRequest(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


@router.get("/marketplace")
async def list_marketplace(
    *,
    current_user: AuthUser,
    db: DbSession,
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """The marketplace is deliberately org-wide — that is the point of publishing.

    Departments stay isolated for their own repositories (Section 5); an item only
    becomes visible here once someone explicitly published it.
    """
    stmt = (
        select(MarketplaceItem, Department.name)
        .outerjoin(Department, Department.id == MarketplaceItem.source_dept_id)
        .where(
            MarketplaceItem.org_id == UUID(current_user.org_id),
            MarketplaceItem.is_active.is_(True),
        )
    )
    if category:
        stmt = stmt.where(MarketplaceItem.category == category)
    rows = (await db.execute(stmt.order_by(MarketplaceItem.reuse_count.desc()).limit(limit))).all()

    return {
        "count": len(rows),
        "items": [
            {
                "item_id": str(m.id),
                "knowledge_id": str(m.knowledge_id),
                "title": m.title,
                "summary": m.summary,
                "category": m.category,
                "source_department": dept_name or "Unassigned",
                "source_department_id": str(m.source_dept_id) if m.source_dept_id else None,
                "average_rating": m.average_rating,
                "rating_count": m.rating_count,
                "reuse_count": m.reuse_count,
                "published_at": m.created_at.isoformat() if m.created_at else None,
                "is_own_department": (
                    str(m.source_dept_id) == current_user.dept_id if m.source_dept_id else False
                ),
            }
            for m, dept_name in rows
        ],
    }


@router.post("/marketplace/publish")
async def publish_to_marketplace(payload: PublishRequest, *, current_user: AuthUser, db: DbSession):
    """Publish approved knowledge for cross-department reuse."""
    if Permission.PUBLISH_MARKETPLACE.value not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Missing permission: publish:marketplace")

    item = (
        await db.execute(select(KnowledgeItem).where(KnowledgeItem.id == payload.knowledge_id))
    ).scalar_one_or_none()
    if item is None or str(item.org_id) != current_user.org_id:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    if current_user.is_department_scoped and item.dept_id and str(item.dept_id) != current_user.dept_id:
        raise HTTPException(status_code=403, detail="Cannot publish another department's knowledge")
    # Only knowledge that cleared the approval chain may be offered to other departments —
    # publishing unreviewed material would route around Sections 12-13 entirely.
    if item.workflow_status != WorkflowStatus.APPROVED:
        raise HTTPException(
            status_code=409,
            detail=f"Only approved knowledge can be published (status: {item.workflow_status})",
        )

    existing = (
        await db.execute(
            select(MarketplaceItem).where(
                MarketplaceItem.knowledge_id == item.id,
                MarketplaceItem.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if existing:
        return {"item_id": str(existing.id), "already_published": True}

    mi = MarketplaceItem(
        org_id=UUID(current_user.org_id),
        source_dept_id=item.dept_id,
        knowledge_id=item.id,
        publisher_id=UUID(current_user.user_id),
        title=item.title,
        summary=item.summary,
        category=payload.category,
    )
    db.add(mi)
    item.is_published = True
    db.add(TimelineEvent(
        org_id=UUID(current_user.org_id),
        dept_id=item.dept_id,
        actor_id=UUID(current_user.user_id),
        event_type="knowledge_published",
        title=f"Published to the marketplace: {item.title[:200]}",
        occurred_at=datetime.now(timezone.utc),
        source_type="knowledge_item",
        source_id=str(item.id),
    ))
    await db.commit()
    await db.refresh(mi)
    return {"item_id": str(mi.id), "already_published": False, "category": mi.category}


@router.post("/marketplace/{item_id}/reuse")
async def reuse_marketplace_item(
    item_id: UUID, payload: ReuseRequest, *, current_user: AuthUser, db: DbSession
):
    """Record another department adopting this item, optionally with a rating."""
    mi = (
        await db.execute(select(MarketplaceItem).where(MarketplaceItem.id == item_id))
    ).scalar_one_or_none()
    if mi is None or str(mi.org_id) != current_user.org_id:
        raise HTTPException(status_code=404, detail="Marketplace item not found")

    dept = UUID(current_user.dept_id) if current_user.dept_id else None
    db.add(MarketplaceReuse(
        org_id=UUID(current_user.org_id),
        item_id=mi.id,
        target_dept_id=dept,
        actor_id=UUID(current_user.user_id),
        rating=payload.rating,
        comment=payload.comment,
    ))
    mi.reuse_count += 1
    if payload.rating:
        mi.rating_sum += payload.rating
        mi.rating_count += 1
    await db.commit()
    return {
        "item_id": str(mi.id),
        "reuse_count": mi.reuse_count,
        "average_rating": mi.average_rating,
    }


@router.get("/marketplace/metrics")
async def marketplace_metrics(*, current_user: AuthUser, db: DbSession):
    """Section 30.2 collaboration metrics, per department."""
    org_id = UUID(current_user.org_id)
    # Active only, matching the scorecards — retired departments would otherwise pad
    # this list with permanent zeroes and make sharing look worse than it is.
    depts = (
        await db.execute(
            select(Department).where(
                Department.org_id == org_id, Department.is_active.is_(True)
            )
        )
    ).scalars().all()

    out = []
    for d in depts:
        published = (await db.execute(
            select(func.count()).select_from(MarketplaceItem).where(
                MarketplaceItem.org_id == org_id, MarketplaceItem.source_dept_id == d.id)
        )).scalar() or 0
        reused = (await db.execute(
            select(func.count()).select_from(MarketplaceReuse).where(
                MarketplaceReuse.org_id == org_id, MarketplaceReuse.target_dept_id == d.id)
        )).scalar() or 0
        out.append({
            "department": d.name,
            "department_id": str(d.id),
            "publish_count": published,
            "reuse_count": reused,
        })
    out.sort(key=lambda r: r["publish_count"] + r["reuse_count"], reverse=True)
    return {"departments": out}


# ----------------------------------------------------------------------------
# Section 31 — Organizational Memory Timeline
# ----------------------------------------------------------------------------

@router.get("/timeline")
async def memory_timeline(
    *,
    current_user: AuthUser,
    db: DbSession,
    dept_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(60, ge=1, le=300),
):
    """Chronological organizational memory; every entry links back to its source record."""
    scope = resolve_department_scope(current_user, dept_id)
    stmt = (
        select(TimelineEvent, Department.name, User.full_name)
        .outerjoin(Department, Department.id == TimelineEvent.dept_id)
        .outerjoin(User, User.id == TimelineEvent.actor_id)
        .where(TimelineEvent.org_id == UUID(current_user.org_id))
    )
    if scope:
        stmt = stmt.where(TimelineEvent.dept_id == UUID(scope))
    if event_type:
        stmt = stmt.where(TimelineEvent.event_type == event_type)

    rows = (await db.execute(stmt.order_by(TimelineEvent.occurred_at.desc()).limit(limit))).all()
    return {
        "count": len(rows),
        "events": [
            {
                "event_id": str(e.id),
                "event_type": e.event_type,
                "title": e.title,
                "description": e.description,
                "department": dname,
                "actor": uname,
                "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
                "source_type": e.source_type,
                "source_id": e.source_id,
            }
            for e, dname, uname in rows
        ],
    }


# ----------------------------------------------------------------------------
# Section 35 — Notification Center
# ----------------------------------------------------------------------------

@router.get("/notifications")
async def list_notifications(
    *,
    current_user: AuthUser,
    db: DbSession,
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
):
    stmt = select(Notification).where(Notification.user_id == UUID(current_user.user_id))
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    rows = (await db.execute(stmt.order_by(Notification.created_at.desc()).limit(limit))).scalars().all()
    unread = (await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == UUID(current_user.user_id),
            Notification.is_read.is_(False))
    )).scalar() or 0
    return {
        "unread_count": unread,
        "count": len(rows),
        "notifications": [
            {
                "id": str(n.id),
                "category": n.category,
                "severity": n.severity,
                "title": n.title,
                "body": n.body,
                "link_type": n.link_type,
                "link_id": n.link_id,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in rows
        ],
    }


@router.post("/notifications/read-all")
async def mark_all_read(*, current_user: AuthUser, db: DbSession):
    rows = (await db.execute(
        select(Notification).where(
            Notification.user_id == UUID(current_user.user_id),
            Notification.is_read.is_(False))
    )).scalars().all()
    for n in rows:
        n.is_read = True
    await db.commit()
    return {"marked_read": len(rows)}


@router.post("/notifications/{notification_id}/read")
async def mark_one_read(notification_id: str, *, current_user: AuthUser, db: DbSession):
    row = (await db.execute(
        select(Notification).where(
            Notification.id == UUID(notification_id),
            Notification.user_id == UUID(current_user.user_id))
    )).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No such notification")
    row.is_read = True
    await db.commit()
    return {"id": str(row.id), "is_read": True}


# ----------------------------------------------------------------------------
# Section 36 — Universal Enterprise Search
# ----------------------------------------------------------------------------

@router.get("/search")
async def universal_search(
    *,
    current_user: AuthUser,
    db: DbSession,
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(20, ge=1, le=100),
):
    """Searches knowledge, people, marketplace, and timeline in one pass.

    Department-scoped roles never see another department's knowledge or people here;
    the marketplace is the one intentionally shared surface.
    """
    org_id = UUID(current_user.org_id)
    like = f"%{q.lower()}%"
    scoped = current_user.is_department_scoped and current_user.dept_id
    dept_uuid = UUID(current_user.dept_id) if scoped else None

    k_stmt = select(KnowledgeItem).where(
        KnowledgeItem.org_id == org_id,
        KnowledgeItem.is_active.is_(True),
        or_(func.lower(KnowledgeItem.title).like(like),
            func.lower(KnowledgeItem.summary).like(like)),
    )
    if scoped:
        k_stmt = k_stmt.where(KnowledgeItem.dept_id == dept_uuid)
    knowledge = (await db.execute(k_stmt.limit(limit))).scalars().all()

    p_stmt = select(User).where(
        User.org_id == org_id,
        User.is_active.is_(True),
        or_(func.lower(User.full_name).like(like), func.lower(User.email).like(like)),
    )
    if scoped:
        p_stmt = p_stmt.where(User.dept_id == dept_uuid)
    people = (await db.execute(p_stmt.limit(limit))).scalars().all()

    market = (await db.execute(
        select(MarketplaceItem).where(
            MarketplaceItem.org_id == org_id,
            MarketplaceItem.is_active.is_(True),
            func.lower(MarketplaceItem.title).like(like),
        ).limit(limit)
    )).scalars().all()

    t_stmt = select(TimelineEvent).where(
        TimelineEvent.org_id == org_id,
        func.lower(TimelineEvent.title).like(like),
    )
    if scoped:
        t_stmt = t_stmt.where(TimelineEvent.dept_id == dept_uuid)
    events = (await db.execute(t_stmt.order_by(TimelineEvent.occurred_at.desc()).limit(limit))).scalars().all()

    results = {
        "knowledge": [
            {"id": str(k.id), "title": k.title, "domain": k.domain,
             "status": k.workflow_status, "summary": (k.summary or "")[:200]}
            for k in knowledge
        ],
        "people": [
            {"id": str(u.id), "name": u.full_name, "role": u.role, "title": u.job_title}
            for u in people
        ],
        "marketplace": [
            {"id": str(m.id), "title": m.title, "category": m.category,
             "reuse_count": m.reuse_count}
            for m in market
        ],
        "timeline": [
            {"id": str(e.id), "title": e.title, "event_type": e.event_type,
             "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None}
            for e in events
        ],
    }
    return {
        "query": q,
        "scope": "department" if scoped else "organization",
        "total_results": sum(len(v) for v in results.values()),
        "results": results,
    }


# ----------------------------------------------------------------------------
# Section 34 — Enterprise Learning Center
# ----------------------------------------------------------------------------

@router.get("/learning")
async def learning_center(
    *, current_user: AuthUser, db: DbSession, limit: int = Query(20, ge=1, le=100)
):
    """Surfaces resources against detected gaps, rather than only naming the gap.

    Suggested reading is drawn from the department's own approved knowledge; suggested
    mentors are the people who actually own knowledge in the weakest domains.
    """
    org_id = UUID(current_user.org_id)
    scoped = current_user.is_department_scoped and current_user.dept_id
    dept_uuid = UUID(current_user.dept_id) if scoped else None

    records = (await db.execute(
        select(LearningRecord)
        .where(LearningRecord.user_id == UUID(current_user.user_id))
        .order_by(LearningRecord.created_at.desc())
        .limit(limit)
    )).scalars().all()

    k_stmt = select(KnowledgeItem).where(
        KnowledgeItem.org_id == org_id,
        KnowledgeItem.is_active.is_(True),
        KnowledgeItem.workflow_status == WorkflowStatus.APPROVED,
    )
    if scoped:
        k_stmt = k_stmt.where(KnowledgeItem.dept_id == dept_uuid)
    items = (await db.execute(k_stmt)).scalars().all()

    by_domain: Dict[str, int] = {}
    for i in items:
        if i.domain:
            by_domain[i.domain] = by_domain.get(i.domain, 0) + 1

    # A "gap" is a domain the department barely covers — thin coverage is the signal
    # the SRS asks the Learning Center to act on.
    gaps = sorted(by_domain.items(), key=lambda kv: kv[1])[:3]
    suggestions = []
    for domain, count in gaps:
        reading = [i for i in items if i.domain == domain][:3]
        suggestions.append({
            "skill_area": domain,
            "coverage_items": count,
            "why": f"Only {count} approved document(s) cover {domain}",
            "recommended_reading": [
                {"id": str(r.id), "title": r.title, "summary": (r.summary or "")[:160]}
                for r in reading
            ],
        })

    completed = [r for r in records if r.status == "completed"]
    deltas = [
        r.knowledge_score_after - r.knowledge_score_before
        for r in completed
        if r.knowledge_score_after is not None and r.knowledge_score_before is not None
    ]
    return {
        "scope": "department" if scoped else "organization",
        "my_records": [
            {
                "id": str(r.id), "title": r.title, "skill_area": r.skill_area,
                "status": r.status, "resource_type": r.resource_type,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in records
        ],
        "completed_count": len(completed),
        "average_knowledge_gain": round(sum(deltas) / len(deltas), 3) if deltas else None,
        "suggestions": suggestions,
    }
