"""
AION API — Document Approval Workflow (SRS Sections 12-13)

Employee submits -> Manager first-pass -> Department Head final -> repository.
Transitions are validated server-side against the actor's role; the UI never decides
who may approve what.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.core.dependencies import AuthUser, DbSession, resolve_department_scope
from app.core.security import Permission, UserRole
from app.models.enterprise import ApprovalLog, AuditLog, Notification, TimelineEvent, WorkflowStatus
from app.models.knowledge import KnowledgeItem
from app.models.user import User

router = APIRouter(prefix="/workflow", tags=["Enterprise: Approval Workflow"])


class ReviewAction(BaseModel):
    comment: Optional[str] = Field(None, max_length=2000)


#: Which role may move a document out of which state (SRS Sections 9, 10).
_REVIEWERS = {
    WorkflowStatus.PENDING_MANAGER: {
        UserRole.MANAGER, UserRole.DEPT_HEAD, UserRole.DEPT_ADMIN,
        UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN,
    },
    WorkflowStatus.PENDING_HEAD: {
        UserRole.DEPT_HEAD, UserRole.DEPT_ADMIN,
        UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN,
    },
}


async def _load_item(db, item_id: UUID, current_user: AuthUser) -> KnowledgeItem:
    item = (
        await db.execute(select(KnowledgeItem).where(KnowledgeItem.id == item_id))
    ).scalar_one_or_none()
    if item is None or str(item.org_id) != current_user.org_id:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.is_department_scoped and item.dept_id:
        if str(item.dept_id) != current_user.dept_id:
            raise HTTPException(status_code=403, detail="Cross-department access denied")
    return item


async def _record(
    db, *, item: KnowledgeItem, current_user: AuthUser, action: str,
    from_status: str, to_status: str, comment: Optional[str],
) -> None:
    """Write the approval log, audit trail, and notify the submitter.

    All three are written in the same transaction as the status change so an approval
    can never exist without its trail.
    """
    db.add(ApprovalLog(
        org_id=UUID(current_user.org_id),
        dept_id=item.dept_id,
        knowledge_id=item.id,
        actor_id=UUID(current_user.user_id),
        actor_role=current_user.role.value,
        action=action,
        from_status=from_status,
        to_status=to_status,
        comment=comment,
    ))
    db.add(AuditLog(
        org_id=UUID(current_user.org_id),
        actor_id=UUID(current_user.user_id),
        actor_role=current_user.role.value,
        action_type=f"document.{action}",
        target_type="knowledge_item",
        target_id=str(item.id),
        detail={"from": from_status, "to": to_status},
    ))
    if item.submitted_by_id and str(item.submitted_by_id) != current_user.user_id:
        db.add(Notification(
            org_id=UUID(current_user.org_id),
            user_id=item.submitted_by_id,
            category="workflow",
            severity="warning" if to_status in (WorkflowStatus.REJECTED, WorkflowStatus.RETURNED) else "info",
            title=f"'{item.title[:80]}' was {action}ed",
            body=comment,
            link_type="knowledge_item",
            link_id=str(item.id),
        ))


@router.get("/queue")
async def review_queue(
    *,
    current_user: AuthUser,
    db: DbSession,
    dept_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """Documents awaiting *this* user's decision, per their position in the chain."""
    states = [s for s, roles in _REVIEWERS.items() if current_user.role in roles]
    if not states:
        return {"queue": [], "count": 0, "reviewable_states": []}

    scope = resolve_department_scope(current_user, dept_id)
    stmt = select(KnowledgeItem).where(
        KnowledgeItem.org_id == UUID(current_user.org_id),
        KnowledgeItem.workflow_status.in_(states),
    )
    if scope:
        stmt = stmt.where(KnowledgeItem.dept_id == UUID(scope))

    items = (await db.execute(stmt.order_by(KnowledgeItem.created_at).limit(limit))).scalars().all()
    now = datetime.now(timezone.utc)

    def waiting_days(created):
        if not created:
            return None
        # SQLite hands back naive datetimes; treat them as the UTC they were written as.
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return (now - created).days

    return {
        "queue": [
            {
                "knowledge_id": str(i.id),
                "title": i.title,
                "domain": i.domain,
                "status": i.workflow_status,
                "submitted_at": i.created_at.isoformat() if i.created_at else None,
                "waiting_days": waiting_days(i.created_at),
            }
            for i in items
        ],
        "count": len(items),
        "reviewable_states": states,
    }


@router.post("/{item_id}/submit")
async def submit_for_review(item_id: UUID, payload: ReviewAction, *, current_user: AuthUser, db: DbSession):
    """Employee submits a draft into the approval chain."""
    if Permission.SUBMIT_DOCUMENT.value not in current_user.permissions:
        raise HTTPException(status_code=403, detail="Missing permission: submit:document")
    item = await _load_item(db, item_id, current_user)
    if item.workflow_status not in (WorkflowStatus.DRAFT, WorkflowStatus.RETURNED):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot submit from status '{item.workflow_status}'",
        )
    prev = item.workflow_status
    item.workflow_status = WorkflowStatus.PENDING_MANAGER
    item.submitted_by_id = UUID(current_user.user_id)
    await _record(db, item=item, current_user=current_user, action="submit",
                  from_status=prev, to_status=item.workflow_status, comment=payload.comment)
    await db.commit()
    return {"knowledge_id": str(item.id), "status": item.workflow_status, "previous_status": prev}


@router.post("/{item_id}/approve")
async def approve(item_id: UUID, payload: ReviewAction, *, current_user: AuthUser, db: DbSession):
    """Advance one step: manager approval escalates, head approval publishes."""
    item = await _load_item(db, item_id, current_user)
    allowed = _REVIEWERS.get(item.workflow_status, set())
    if not allowed:
        raise HTTPException(status_code=409, detail=f"Nothing to approve in status '{item.workflow_status}'")
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{current_user.role.value}' cannot approve at stage '{item.workflow_status}'",
        )

    prev = item.workflow_status
    if prev == WorkflowStatus.PENDING_MANAGER:
        # A Department Head approving at the manager stage clears both gates at once;
        # forcing them through their own subordinate's step would be pure ceremony.
        if current_user.role == UserRole.MANAGER:
            item.workflow_status = WorkflowStatus.PENDING_HEAD
            item.reviewed_by_id = UUID(current_user.user_id)
        else:
            item.workflow_status = WorkflowStatus.APPROVED
            item.reviewed_by_id = UUID(current_user.user_id)
            item.approved_by_id = UUID(current_user.user_id)
            item.approved_at = datetime.now(timezone.utc)
    else:
        item.workflow_status = WorkflowStatus.APPROVED
        item.approved_by_id = UUID(current_user.user_id)
        item.approved_at = datetime.now(timezone.utc)

    await _record(db, item=item, current_user=current_user, action="approve",
                  from_status=prev, to_status=item.workflow_status, comment=payload.comment)

    if item.workflow_status == WorkflowStatus.APPROVED:
        db.add(TimelineEvent(
            org_id=UUID(current_user.org_id),
            dept_id=item.dept_id,
            actor_id=UUID(current_user.user_id),
            event_type="knowledge_contribution",
            title=f"Approved into the knowledge repository: {item.title[:200]}",
            description=item.summary,
            occurred_at=datetime.now(timezone.utc),
            source_type="knowledge_item",
            source_id=str(item.id),
        ))
    await db.commit()
    return {
        "knowledge_id": str(item.id),
        "status": item.workflow_status,
        "previous_status": prev,
        "fully_approved": item.workflow_status == WorkflowStatus.APPROVED,
    }


@router.post("/{item_id}/return")
async def return_for_revision(item_id: UUID, payload: ReviewAction, *, current_user: AuthUser, db: DbSession):
    """Send back for rework — the author is expected to resubmit."""
    item = await _load_item(db, item_id, current_user)
    allowed = _REVIEWERS.get(item.workflow_status, set())
    if current_user.role not in allowed:
        raise HTTPException(status_code=403, detail="Not a reviewer at this stage")
    prev = item.workflow_status
    item.workflow_status = WorkflowStatus.RETURNED
    await _record(db, item=item, current_user=current_user, action="return",
                  from_status=prev, to_status=item.workflow_status, comment=payload.comment)
    await db.commit()
    return {"knowledge_id": str(item.id), "status": item.workflow_status, "previous_status": prev}


@router.post("/{item_id}/reject")
async def reject(item_id: UUID, payload: ReviewAction, *, current_user: AuthUser, db: DbSession):
    """Terminal rejection — the item stays out of the repository."""
    item = await _load_item(db, item_id, current_user)
    allowed = _REVIEWERS.get(item.workflow_status, set())
    if current_user.role not in allowed:
        raise HTTPException(status_code=403, detail="Not a reviewer at this stage")
    prev = item.workflow_status
    item.workflow_status = WorkflowStatus.REJECTED
    item.is_active = False
    await _record(db, item=item, current_user=current_user, action="reject",
                  from_status=prev, to_status=item.workflow_status, comment=payload.comment)
    await db.commit()
    return {"knowledge_id": str(item.id), "status": item.workflow_status, "previous_status": prev}


@router.get("/{item_id}/history")
async def approval_history(item_id: UUID, *, current_user: AuthUser, db: DbSession):
    """Full chain of custody for one document."""
    item = await _load_item(db, item_id, current_user)
    rows = (
        await db.execute(
            select(ApprovalLog, User.full_name)
            .outerjoin(User, User.id == ApprovalLog.actor_id)
            .where(ApprovalLog.knowledge_id == item.id)
            .order_by(ApprovalLog.created_at)
        )
    ).all()
    return {
        "knowledge_id": str(item.id),
        "title": item.title,
        "current_status": item.workflow_status,
        "history": [
            {
                "action": log.action,
                "from_status": log.from_status,
                "to_status": log.to_status,
                "actor": name or "Unknown",
                "actor_role": log.actor_role,
                "comment": log.comment,
                "at": log.created_at.isoformat() if log.created_at else None,
            }
            for log, name in rows
        ],
    }


@router.get("/stats")
async def workflow_stats(
    *, current_user: AuthUser, db: DbSession, dept_id: Optional[str] = Query(None)
):
    """Counts per workflow state — feeds the department scorecard's pending-approvals metric."""
    scope = resolve_department_scope(current_user, dept_id)
    stmt = select(KnowledgeItem.workflow_status, func.count()).where(
        KnowledgeItem.org_id == UUID(current_user.org_id)
    )
    if scope:
        stmt = stmt.where(KnowledgeItem.dept_id == UUID(scope))
    rows = (await db.execute(stmt.group_by(KnowledgeItem.workflow_status))).all()
    counts = {s: 0 for s in WorkflowStatus.ALL}
    counts.update({s: c for s, c in rows})
    return {
        "department_id": scope,
        "counts": counts,
        "pending_total": sum(counts[s] for s in WorkflowStatus.OPEN),
    }
