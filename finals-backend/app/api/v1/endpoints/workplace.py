"""
AION Workplace API — the day-to-day management layer from the handwritten notes.

Employee: profile, department detail, leave (30 days a year), sending a project or
policy up for approval, and their notifications.
Head: their people, the queue of what is waiting on them, approving with feedback,
messaging the department or one person, and raising a fund request.
Finance: the first stage of the fund chain, plus salary, funding and profit.
Admin: the second stage of the fund chain, and the intimation back to the department.

Nothing here duplicates the document approval chain in `workflow.py`; that governs
uploaded knowledge files and is untouched.
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.core.dependencies import AuthUser, DbSession
from app.core.security import Permission
from app.models.enterprise import Notification
from app.models.knowledge import KnowledgeItem
from app.models.organization import Department
from app.models.user import User
from app.models.workplace import (
    ANNUAL_LEAVE_DAYS,
    ApprovalRequest,
    Attachment,
    CompanyFinance,
    DepartmentMessage,
    EmployeeProfileDetail,
    FundRequest,
    LeaveRequest,
    RequestStatus,
    SalaryRecord,
)

#: Where attachment bytes live — one store shared by every communication flow.
_ATTACH_DIR = Path(__file__).resolve().parents[4] / "data" / "attachments"
_MAX_ATTACH_BYTES = 8 * 1024 * 1024  # 8 MB, same ceiling as document ingestion.

router = APIRouter(prefix="/workplace", tags=["Workplace"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _manages(user: AuthUser) -> bool:
    return Permission.REVIEW_DOCUMENT.value in user.permissions


async def _notify(db, org_id, user_id, title: str, body: str, kind: str = "info") -> None:
    """Drop a row in the existing notification table rather than a new one."""
    # Field names read from the model, not assumed: `body` and `category`.
    db.add(
        Notification(
            org_id=org_id,
            user_id=user_id,
            title=title,
            body=body,
            category=kind,
            is_read=False,
        )
    )


async def _display_name(db, user_id: str) -> str:
    """The person's real name for a notification.

    `CurrentUser` carries the JWT claims only — user_id, org_id, email, role,
    permissions, dept_id — and has no `full_name`, so it must be read from the row.
    """
    row = (
        await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    ).scalar_one_or_none()
    return (row.full_name if row and row.full_name else "A colleague")


async def _head_of(db, dept_id) -> Optional[User]:
    if not dept_id:
        return None
    return (
        await db.execute(
            select(User).where(
                User.dept_id == dept_id,
                User.role == "dept_head",
                User.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()


#: Roles that sit at the top of the tree — they approve, they do not ask.
_TOP_ROLES = ("org_admin", "super_admin", "executive")


async def _org_admin(db, org_id) -> Optional[User]:
    """The organisation's administrator — the approver above a department head."""
    return (
        await db.execute(
            select(User)
            .where(
                User.org_id == org_id,
                User.role == "org_admin",
                User.is_active.is_(True),
            )
            .order_by(User.created_at)
        )
    ).scalars().first()


async def _approver_for(db, requester: User) -> Optional[User]:
    """Who signs off this person's leave or project/policy request.

    The hierarchy from the notes, taken literally:
      • an employee or manager  → their department head
      • a department head        → the organisation admin (a head cannot approve
                                    their own leave, so it escalates one level)
      • an admin / executive     → nobody; they approve, they do not request
    """
    if requester.role == "dept_head":
        return await _org_admin(db, requester.org_id)
    if requester.role in ("employee", "manager"):
        return await _head_of(db, requester.dept_id)
    return None


async def _attachment_info(db, attachment_id) -> Optional[dict]:
    """Small metadata block a recipient sees; the bytes are fetched via /attachments/{id}."""
    if not attachment_id:
        return None
    row = (
        await db.execute(select(Attachment).where(Attachment.id == attachment_id))
    ).scalar_one_or_none()
    if not row:
        return None
    return {"id": str(row.id), "filename": row.filename, "size_bytes": row.size_bytes}


async def _attachments_map(db, ids) -> dict:
    """Resolve many attachment ids at once for a list response."""
    ids = [i for i in ids if i]
    if not ids:
        return {}
    rows = (
        await db.execute(select(Attachment).where(Attachment.id.in_(ids)))
    ).scalars().all()
    return {
        r.id: {"id": str(r.id), "filename": r.filename, "size_bytes": r.size_bytes}
        for r in rows
    }


async def _resolve_attachment(db, org_id, attachment_id: Optional[str]):
    """Validate an attachment id belongs to this org before linking it to a message."""
    if not attachment_id:
        return None
    row = (
        await db.execute(
            select(Attachment).where(
                Attachment.id == uuid.UUID(attachment_id), Attachment.org_id == org_id
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="That attachment does not exist.")
    return row.id


# ─────────────────────────────── Attachments ───────────────────────────────


@router.post("/attachments", status_code=201)
async def upload_attachment(
    current_user: AuthUser, db: DbSession, file: UploadFile = File(...)
):
    """Store a file so it can be attached to a message or a request.

    Text and files are independent everywhere: a person can send text only, a file
    only, or both. The frontend uploads here first, then sends the returned id with
    the message or request.
    """
    raw = await file.read()
    if len(raw) > _MAX_ATTACH_BYTES:
        raise HTTPException(status_code=413, detail="File too large — 8MB max.")
    if not raw:
        raise HTTPException(status_code=422, detail="That file is empty.")
    _ATTACH_DIR.mkdir(parents=True, exist_ok=True)
    att_id = uuid.uuid4()
    safe_name = os.path.basename(file.filename or "upload")
    ext = os.path.splitext(safe_name)[1][:12]
    path = _ATTACH_DIR / (str(att_id) + ext)
    path.write_bytes(raw)

    row = Attachment(
        id=att_id,
        org_id=uuid.UUID(current_user.org_id),
        uploader_id=uuid.UUID(current_user.user_id),
        filename=safe_name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(raw),
        storage_path=str(path),
    )
    db.add(row)
    await db.commit()
    return {"id": str(att_id), "filename": safe_name, "size_bytes": len(raw)}


@router.get("/attachments/{attachment_id}")
async def download_attachment(attachment_id: str, current_user: AuthUser, db: DbSession):
    """Return a file's bytes to anyone in the same organisation (recipients included)."""
    row = (
        await db.execute(
            select(Attachment).where(
                Attachment.id == uuid.UUID(attachment_id),
                Attachment.org_id == uuid.UUID(current_user.org_id),
            )
        )
    ).scalar_one_or_none()
    if row is None or not os.path.exists(row.storage_path):
        raise HTTPException(status_code=404, detail="No such file.")
    return FileResponse(row.storage_path, filename=row.filename, media_type=row.content_type)


# ─────────────────────────── Profile & department ───────────────────────────


@router.get("/me/profile")
async def my_profile(*, current_user: AuthUser, db: DbSession):
    """Employee (i): projects, recently completed, currently working, trainee status."""
    uid = uuid.UUID(current_user.user_id)
    user = (await db.execute(select(User).where(User.id == uid))).scalar_one()
    detail = (
        await db.execute(
            select(EmployeeProfileDetail).where(EmployeeProfileDetail.user_id == uid)
        )
    ).scalar_one_or_none()
    dept = (
        (await db.execute(select(Department).where(Department.id == user.dept_id))).scalar_one_or_none()
        if user.dept_id
        else None
    )
    head = await _head_of(db, user.dept_id)
    reporting = None
    if detail and detail.reporting_head_id:
        reporting = (
            await db.execute(select(User).where(User.id == detail.reporting_head_id))
        ).scalar_one_or_none()

    mine = (
        await db.execute(
            select(KnowledgeItem).where(KnowledgeItem.submitted_by_id == uid)
        )
    ).scalars().all()

    return {
        "name": user.full_name,
        "email": user.email,
        "role": user.role,
        "job_title": user.job_title,
        "department": dept.name if dept else None,
        "department_code": dept.code if dept else None,
        "head_of_department": head.full_name if head else None,
        "head_of_department_id": str(head.id) if head else None,
        "employee_code": detail.employee_code if detail else None,
        "designation": detail.designation if detail else user.job_title,
        "joining_date": detail.joining_date.isoformat() if detail and detail.joining_date else None,
        "reporting_head": reporting.full_name if reporting else (head.full_name if head else None),
        "is_trainee": bool(detail.is_trainee) if detail else False,
        "skills": (detail.skills or {}).get("primary", []) if detail else [],
        "currently_working_on": (detail.current_projects or {}).get("names", []) if detail else [],
        "recently_completed": (detail.completed_projects or {}).get("names", []) if detail else [],
        "documents_written": len(mine),
        "documents_awaiting_review": sum(
            1 for i in mine if i.workflow_status not in ("approved", "rejected")
        ),
    }


@router.get("/department")
async def my_department(
    *, current_user: AuthUser, db: DbSession, dept_id: Optional[str] = Query(default=None)
):
    """Employee (ii)-(iii): who is in the department, doing what, and its policies.

    An admin (READ_CROSS_DEPARTMENT) may pass `dept_id` to inspect any department in
    detail — its people and their work. Everyone else is pinned to their own department.
    """
    org_id = uuid.UUID(current_user.org_id)
    cross = Permission.READ_CROSS_DEPARTMENT.value in current_user.permissions
    if dept_id and cross:
        target = uuid.UUID(dept_id)
    elif dept_id and not cross:
        raise HTTPException(status_code=403, detail="You can only see your own department.")
    else:
        target = uuid.UUID(current_user.dept_id) if current_user.dept_id else None
    dept_id = target
    if dept_id is None:
        return {"department": None, "people": [], "projects": [], "policies": []}

    dept = (await db.execute(select(Department).where(Department.id == dept_id))).scalar_one()
    people = (
        await db.execute(
            select(User).where(User.dept_id == dept_id, User.is_active.is_(True))
        )
    ).scalars().all()
    details = {
        d.user_id: d
        for d in (
            await db.execute(
                select(EmployeeProfileDetail).where(
                    EmployeeProfileDetail.user_id.in_([p.id for p in people])
                )
            )
        ).scalars().all()
    }
    items = (
        await db.execute(
            select(KnowledgeItem).where(
                KnowledgeItem.org_id == org_id, KnowledgeItem.dept_id == dept_id
            )
        )
    ).scalars().all()

    projects: dict[str, list[str]] = {}
    roster = []
    for p in people:
        d = details.get(p.id)
        working = (d.current_projects or {}).get("names", []) if d else []
        roster.append(
            {
                "name": p.full_name,
                "role": p.role,
                "designation": (d.designation if d else p.job_title),
                "employee_code": d.employee_code if d else None,
                "working_on": working,
            }
        )
        for proj in working:
            projects.setdefault(proj, []).append(p.full_name)

    return {
        "department": dept.name,
        "code": dept.code,
        "head": next((p.full_name for p in people if p.role == "dept_head"), None),
        "employee_count": len(people),
        "people": sorted(roster, key=lambda r: r["name"]),
        # "who are doing what projects in the dept"
        "projects": [{"name": k, "people": v} for k, v in sorted(projects.items())],
        # "current policies and regulation in his department"
        "policies": [
            {"title": i.title, "domain": i.domain, "status": i.workflow_status}
            for i in items
            if (i.domain or "").lower() in ("policy", "hr", "legal")
            or "policy" in (i.title or "").lower()
            or "procedure" in (i.title or "").lower()
            or "standard" in (i.title or "").lower()
        ][:25],
        "documents_held": len(items),
    }


# ─────────────────────────────── Leave ───────────────────────────────


class LeaveCreate(BaseModel):
    start_date: date
    end_date: date
    reason: Optional[str] = Field(default=None, max_length=1000)
    leave_type: str = Field(default="annual", max_length=40)
    attachment_id: Optional[str] = None


@router.get("/leave/me")
async def my_leave(*, current_user: AuthUser, db: DbSession):
    """Balance out of 30 for the current year, plus this person's history."""
    uid = uuid.UUID(current_user.user_id)
    year = _now().year
    rows = (
        await db.execute(
            select(LeaveRequest).where(
                LeaveRequest.requester_id == uid, LeaveRequest.leave_year == year
            ).order_by(LeaveRequest.created_at.desc())
        )
    ).scalars().all()

    taken = sum(r.days for r in rows if r.status == RequestStatus.APPROVED)
    pending = sum(r.days for r in rows if r.status == RequestStatus.PENDING)
    requester = (await db.execute(select(User).where(User.id == uid))).scalar_one()
    approver = await _approver_for(db, requester)
    amap = await _attachments_map(db, [r.attachment_id for r in rows])
    return {
        "year": year,
        "entitlement_days": ANNUAL_LEAVE_DAYS,
        "taken_days": taken,
        "pending_days": pending,
        "remaining_days": max(0, ANNUAL_LEAVE_DAYS - taken - pending),
        # Admins and executives do not take leave; the dashboard hides the panel.
        "takes_leave": requester.role not in _TOP_ROLES,
        "approver": approver.full_name if approver else None,
        "requests": [
            {
                "id": str(r.id),
                "start_date": r.start_date.isoformat(),
                "end_date": r.end_date.isoformat(),
                "days": r.days,
                "type": r.leave_type,
                "reason": r.reason,
                "status": r.status,
                "decision_note": r.decision_note,
                "attachment": amap.get(r.attachment_id),
            }
            for r in rows
        ],
    }


@router.post("/leave", status_code=201)
async def request_leave(payload: LeaveCreate, current_user: AuthUser, db: DbSession):
    """Employee (vii): ask the head for leave; 30 days a year."""
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="The end date is before the start date.")
    days = (payload.end_date - payload.start_date).days + 1
    if days <= 0:
        raise HTTPException(status_code=400, detail="That request covers no days.")

    if current_user.role.value in _TOP_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Administrators do not request leave; they approve it.",
        )
    uid = uuid.UUID(current_user.user_id)
    org_id = uuid.UUID(current_user.org_id)
    dept_id = uuid.UUID(current_user.dept_id) if current_user.dept_id else None
    year = payload.start_date.year

    existing = (
        await db.execute(
            select(LeaveRequest).where(
                LeaveRequest.requester_id == uid, LeaveRequest.leave_year == year
            )
        )
    ).scalars().all()
    used = sum(
        r.days for r in existing if r.status in (RequestStatus.APPROVED, RequestStatus.PENDING)
    )
    if used + days > ANNUAL_LEAVE_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"That would take you to {used + days} days in {year}. "
                   f"The allowance is {ANNUAL_LEAVE_DAYS}, and you have {ANNUAL_LEAVE_DAYS - used} left.",
        )

    requester = (await db.execute(select(User).where(User.id == uid))).scalar_one()
    approver = await _approver_for(db, requester)
    who = await _display_name(db, current_user.user_id)
    att = await _resolve_attachment(db, org_id, payload.attachment_id)
    row = LeaveRequest(
        org_id=org_id,
        dept_id=dept_id,
        requester_id=uid,
        approver_id=approver.id if approver else None,
        start_date=payload.start_date,
        end_date=payload.end_date,
        days=days,
        leave_type=payload.leave_type,
        reason=payload.reason,
        status=RequestStatus.PENDING,
        leave_year=year,
        attachment_id=att,
    )
    db.add(row)
    if approver:
        await _notify(
            db, org_id, approver.id,
            "Leave request",
            f"{who} asked for {days} day(s) "
            f"from {payload.start_date.isoformat()}.",
            "approval",
        )
    await db.commit()
    await db.refresh(row)
    return {
        "id": str(row.id),
        "days": days,
        "status": row.status,
        "sent_to": approver.full_name if approver else None,
        "remaining_after_approval": ANNUAL_LEAVE_DAYS - used - days,
    }


class Decision(BaseModel):
    approve: bool
    note: Optional[str] = Field(default=None, max_length=1000)


@router.get("/leave/queue")
async def leave_queue(*, current_user: AuthUser, db: DbSession):
    """What is waiting on this head."""
    if not _manages(current_user):
        raise HTTPException(status_code=403, detail="Only managers and heads review leave.")
    # The queue is whatever is assigned to *me*: a head sees their team's leave,
    # the admin sees the heads' leave. No one sees their own.
    stmt = select(LeaveRequest).where(
        LeaveRequest.status == RequestStatus.PENDING,
        LeaveRequest.approver_id == uuid.UUID(current_user.user_id),
    )
    rows = (await db.execute(stmt.order_by(LeaveRequest.created_at))).scalars().all()

    names = {
        u.id: u.full_name
        for u in (
            await db.execute(
                select(User).where(User.id.in_([r.requester_id for r in rows] or [uuid.uuid4()]))
            )
        ).scalars().all()
    }
    amap = await _attachments_map(db, [r.attachment_id for r in rows])
    return {
        "count": len(rows),
        "requests": [
            {
                "id": str(r.id),
                "who": names.get(r.requester_id, "Unknown"),
                "start_date": r.start_date.isoformat(),
                "end_date": r.end_date.isoformat(),
                "days": r.days,
                "reason": r.reason,
                "attachment": amap.get(r.attachment_id),
            }
            for r in rows
        ],
    }


@router.post("/leave/{leave_id}/decide")
async def decide_leave(
    leave_id: str, payload: Decision, current_user: AuthUser, db: DbSession
):
    """Head approves or refuses; the employee is told either way."""
    if not _manages(current_user):
        raise HTTPException(status_code=403, detail="Only managers and heads review leave.")
    row = (
        await db.execute(select(LeaveRequest).where(LeaveRequest.id == uuid.UUID(leave_id)))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No such leave request")
    if row.approver_id and str(row.approver_id) != current_user.user_id:
        raise HTTPException(status_code=403, detail="This leave request is not assigned to you.")
    if row.status != RequestStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"Already {row.status}.")

    row.status = RequestStatus.APPROVED if payload.approve else RequestStatus.REJECTED
    row.decided_at = _now()
    row.decision_note = payload.note
    await _notify(
        db, row.org_id, row.requester_id,
        "Leave " + ("approved" if payload.approve else "not approved"),
        (payload.note or
         (f"Your {row.days} day(s) from {row.start_date.isoformat()} were approved."
          if payload.approve else
          f"Your request for {row.days} day(s) was not approved.")),
        "decision",
    )
    await db.commit()
    return {"id": str(row.id), "status": row.status}


# ───────────────────── Project / policy approval requests ─────────────────────


class ApprovalCreate(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    detail: Optional[str] = Field(default=None, max_length=4000)
    request_type: str = Field(default="project", pattern="^(project|policy)$")
    attachment_id: Optional[str] = None


@router.post("/requests", status_code=201)
async def send_request(payload: ApprovalCreate, current_user: AuthUser, db: DbSession):
    """Employee (v): send a project or a new policy to the head for approval."""
    org_id = uuid.UUID(current_user.org_id)
    dept_id = uuid.UUID(current_user.dept_id) if current_user.dept_id else None
    requester = (
        await db.execute(select(User).where(User.id == uuid.UUID(current_user.user_id)))
    ).scalar_one()
    # Employee/manager → their head; a head sends up to the admin (notes: "admin
    # can approve the projects, details, policies sent by the Head").
    approver = await _approver_for(db, requester)
    who = await _display_name(db, current_user.user_id)
    att = await _resolve_attachment(db, org_id, payload.attachment_id)
    row = ApprovalRequest(
        org_id=org_id,
        dept_id=dept_id,
        requester_id=uuid.UUID(current_user.user_id),
        approver_id=approver.id if approver else None,
        request_type=payload.request_type,
        title=payload.title,
        detail=payload.detail,
        status=RequestStatus.PENDING,
        attachment_id=att,
    )
    db.add(row)
    if approver:
        await _notify(
            db, org_id, approver.id, f"New {payload.request_type} for approval",
            f"{who} sent “{payload.title}”.",
            "approval",
        )
    await db.commit()
    await db.refresh(row)
    return {"id": str(row.id), "status": row.status, "sent_to": approver.full_name if approver else None}


@router.get("/requests/me")
async def my_requests(*, current_user: AuthUser, db: DbSession):
    rows = (
        await db.execute(
            select(ApprovalRequest)
            .where(ApprovalRequest.requester_id == uuid.UUID(current_user.user_id))
            .order_by(ApprovalRequest.created_at.desc())
        )
    ).scalars().all()
    amap = await _attachments_map(db, [r.attachment_id for r in rows])
    return {
        "count": len(rows),
        "requests": [
            {
                "id": str(r.id), "title": r.title, "type": r.request_type,
                "status": r.status, "feedback": r.feedback,
                "sent_at": r.created_at.isoformat() if r.created_at else None,
                "attachment": amap.get(r.attachment_id),
            }
            for r in rows
        ],
    }


@router.get("/requests/queue")
async def request_queue(*, current_user: AuthUser, db: DbSession):
    if not _manages(current_user):
        raise HTTPException(status_code=403, detail="Only managers and heads review these.")
    # Assigned to me: a head sees their team's requests, the admin sees the heads'.
    stmt = select(ApprovalRequest).where(
        ApprovalRequest.status == RequestStatus.PENDING,
        ApprovalRequest.approver_id == uuid.UUID(current_user.user_id),
    )
    rows = (await db.execute(stmt.order_by(ApprovalRequest.created_at))).scalars().all()
    names = {
        u.id: u.full_name
        for u in (
            await db.execute(
                select(User).where(User.id.in_([r.requester_id for r in rows] or [uuid.uuid4()]))
            )
        ).scalars().all()
    }
    amap = await _attachments_map(db, [r.attachment_id for r in rows])
    return {
        "count": len(rows),
        "requests": [
            {
                "id": str(r.id), "who": names.get(r.requester_id, "Unknown"),
                "title": r.title, "type": r.request_type, "detail": r.detail,
                "attachment": amap.get(r.attachment_id),
            }
            for r in rows
        ],
    }


@router.post("/requests/{request_id}/decide")
async def decide_request(
    request_id: str, payload: Decision, current_user: AuthUser, db: DbSession
):
    """Head approves or returns with feedback; the employee sees the outcome."""
    if not _manages(current_user):
        raise HTTPException(status_code=403, detail="Only managers and heads review these.")
    row = (
        await db.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == uuid.UUID(request_id))
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No such request")
    if row.approver_id and str(row.approver_id) != current_user.user_id:
        raise HTTPException(status_code=403, detail="This request is not assigned to you.")
    if row.status != RequestStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"Already {row.status}.")

    row.status = RequestStatus.APPROVED if payload.approve else RequestStatus.RETURNED
    row.decided_at = _now()
    row.feedback = payload.note
    await _notify(
        db, row.org_id, row.requester_id,
        f"“{row.title}” " + ("approved" if payload.approve else "returned"),
        payload.note or ("Approved." if payload.approve else "Returned for changes."),
        "decision",
    )
    await db.commit()
    return {"id": str(row.id), "status": row.status}


# ───────────────────────────── Fund chain ─────────────────────────────


class FundCreate(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    amount: float = Field(gt=0)
    purpose: Optional[str] = Field(default=None, max_length=2000)


@router.post("/funds", status_code=201)
async def raise_fund_request(payload: FundCreate, current_user: AuthUser, db: DbSession):
    """A department raising a fund request. Goes to Finance first."""
    if not _manages(current_user):
        raise HTTPException(status_code=403, detail="Heads and managers raise fund requests.")
    if not current_user.dept_id:
        raise HTTPException(status_code=400, detail="You are not attached to a department.")
    org_id = uuid.UUID(current_user.org_id)
    row = FundRequest(
        org_id=org_id,
        dept_id=uuid.UUID(current_user.dept_id),
        requester_id=uuid.UUID(current_user.user_id),
        title=payload.title,
        amount=payload.amount,
        purpose=payload.purpose,
        stage=FundRequest.STAGE_FINANCE,
        status=RequestStatus.PENDING,
    )
    db.add(row)
    fin = (
        await db.execute(
            select(Department).where(Department.org_id == org_id, Department.code == "FIN")
        )
    ).scalar_one_or_none()
    fin_head = await _head_of(db, fin.id) if fin else None
    if fin_head:
        await _notify(
            db, org_id, fin_head.id, "Fund request",
            f"“{payload.title}” for {payload.amount:,.0f} needs Finance.",
            "approval",
        )
    await db.commit()
    await db.refresh(row)
    return {"id": str(row.id), "stage": row.stage, "status": row.status}


@router.get("/funds")
async def list_fund_requests(*, current_user: AuthUser, db: DbSession):
    """Requests this person can act on or has raised."""
    org_id = uuid.UUID(current_user.org_id)
    cross = Permission.READ_CROSS_DEPARTMENT.value in current_user.permissions
    is_finance = False
    if current_user.dept_id:
        d = (
            await db.execute(select(Department).where(Department.id == uuid.UUID(current_user.dept_id)))
        ).scalar_one_or_none()
        is_finance = bool(d and d.code == "FIN")

    stmt = select(FundRequest).where(FundRequest.org_id == org_id)
    if not cross and not is_finance:
        stmt = stmt.where(FundRequest.dept_id == uuid.UUID(current_user.dept_id or str(uuid.uuid4())))
    rows = (await db.execute(stmt.order_by(FundRequest.created_at.desc()))).scalars().all()

    depts = {
        str(d.id): d.name
        for d in (
            await db.execute(select(Department).where(Department.org_id == org_id))
        ).scalars().all()
    }
    return {
        "count": len(rows),
        "can_decide_finance": is_finance or cross,
        "can_decide_admin": cross,
        "requests": [
            {
                "id": str(r.id),
                "title": r.title,
                "amount": r.amount,
                "currency": r.currency,
                "purpose": r.purpose,
                "raised_by_department": depts.get(str(r.dept_id), "Unknown"),
                "stage": r.stage,
                "status": r.status,
                "finance_note": r.finance_note,
                "admin_note": r.admin_note,
                "intimated": r.intimated_at is not None,
            }
            for r in rows
        ],
    }


@router.post("/funds/{fund_id}/decide")
async def decide_fund(
    fund_id: str, payload: Decision, current_user: AuthUser, db: DbSession
):
    """Finance approves and passes to Admin; Admin approves and the department is told."""
    org_id = uuid.UUID(current_user.org_id)
    row = (
        await db.execute(select(FundRequest).where(FundRequest.id == uuid.UUID(fund_id)))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No such fund request")
    if row.status != RequestStatus.PENDING:
        raise HTTPException(status_code=409, detail=f"Already {row.status}.")

    cross = Permission.READ_CROSS_DEPARTMENT.value in current_user.permissions
    me = uuid.UUID(current_user.user_id)

    if row.stage == FundRequest.STAGE_FINANCE:
        fin = (
            await db.execute(
                select(Department).where(Department.org_id == org_id, Department.code == "FIN")
            )
        ).scalar_one_or_none()
        in_finance = bool(fin and current_user.dept_id and str(fin.id) == current_user.dept_id)
        if not (in_finance and _manages(current_user)) and not cross:
            raise HTTPException(status_code=403, detail="Finance reviews this stage.")
        row.finance_decided_by, row.finance_decided_at, row.finance_note = me, _now(), payload.note
        if payload.approve:
            row.stage = FundRequest.STAGE_ADMIN
            admins = (
                await db.execute(
                    select(User).where(
                        User.org_id == org_id, User.role == "org_admin", User.is_active.is_(True)
                    )
                )
            ).scalars().all()
            for a in admins:
                await _notify(
                    db, org_id, a.id, "Fund request passed by Finance",
                    f"“{row.title}” for {row.amount:,.0f} needs your approval.", "approval",
                )
        else:
            row.status = RequestStatus.REJECTED
            await _notify(
                db, org_id, row.requester_id, "Fund request declined by Finance",
                payload.note or f"“{row.title}” was not approved.", "decision",
            )
        await db.commit()
        return {"id": str(row.id), "stage": row.stage, "status": row.status}

    if row.stage == FundRequest.STAGE_ADMIN:
        if not cross:
            raise HTTPException(status_code=403, detail="The administrator approves this stage.")
        row.admin_decided_by, row.admin_decided_at, row.admin_note = me, _now(), payload.note
        row.status = RequestStatus.APPROVED if payload.approve else RequestStatus.REJECTED
        if payload.approve:
            row.stage = FundRequest.STAGE_INTIMATED
            row.intimated_at = _now()
        # The intimation back to the department that raised it.
        await _notify(
            db, org_id, row.requester_id,
            "Fund request " + ("approved" if payload.approve else "declined"),
            payload.note or (
                f"“{row.title}” for {row.amount:,.0f} was approved and your department has been notified."
                if payload.approve else f"“{row.title}” was declined."
            ),
            "decision",
        )
        await db.commit()
        return {"id": str(row.id), "stage": row.stage, "status": row.status}

    raise HTTPException(status_code=409, detail="Nothing left to decide on this request.")


# ─────────────────────────── Department messages ───────────────────────────
#
# Full permission matrix (two-way — whoever can be messaged can also reply):
#   Admin / executive  -> any individual department head, or broadcast to all heads
#   Department head    -> any individual employee in their own department, their
#                          department broadcast, any other head individually, and
#                          the admin
#   Employee           -> their own department head, the admin, or any individual
#                          colleague in their own department (no broadcasting)


class MessageCreate(BaseModel):
    #: Text is optional when a file is attached, so a person can send either or both.
    body: str = Field(default="", max_length=4000)
    subject: Optional[str] = Field(default=None, max_length=300)
    #: Omit to broadcast — to the sender's department, or (for admin/executives, who
    #: have no home department) to every department head.
    recipient_id: Optional[str] = None
    attachment_id: Optional[str] = None


@router.get("/contacts")
async def message_contacts(*, current_user: AuthUser, db: DbSession):
    """Who this person is allowed to message, and any broadcast options — drives the
    recipient picker in the Messages hub. Mirrors the permission matrix enforced by
    `POST /messages` exactly, so anything listed here is guaranteed to send.
    """
    org_id = uuid.UUID(current_user.org_id)
    dept_id = uuid.UUID(current_user.dept_id) if current_user.dept_id else None
    uid = current_user.user_id

    people: list[dict] = []
    broadcasts: list[dict] = []

    if _manages(current_user):
        if dept_id is not None:
            broadcasts.append({"key": "broadcast", "label": "Everyone in your department"})
            dept_people = (
                await db.execute(
                    select(User).where(User.dept_id == dept_id, User.is_active.is_(True))
                )
            ).scalars().all()
            for u in dept_people:
                if str(u.id) != uid:
                    people.append({
                        "id": str(u.id), "name": u.full_name, "role": u.role,
                        "group": "Your department",
                    })
        else:
            broadcasts.append({"key": "broadcast", "label": "All department heads"})

        depts = {
            str(d.id): d.name
            for d in (await db.execute(select(Department).where(Department.org_id == org_id))).scalars().all()
        }
        heads = (
            await db.execute(
                select(User).where(User.org_id == org_id, User.role == "dept_head", User.is_active.is_(True))
            )
        ).scalars().all()
        for h in heads:
            if str(h.id) != uid:
                people.append({
                    "id": str(h.id), "name": h.full_name, "role": "dept_head",
                    "group": "Department heads", "department": depts.get(str(h.dept_id)),
                })

        admin = await _org_admin(db, org_id)
        if admin and str(admin.id) != uid:
            people.append({"id": str(admin.id), "name": admin.full_name, "role": "org_admin", "group": "Administrator"})
    else:
        head = await _head_of(db, dept_id)
        if head:
            people.append({"id": str(head.id), "name": head.full_name, "role": "dept_head", "group": "Your department head"})
        admin = await _org_admin(db, org_id)
        if admin:
            people.append({"id": str(admin.id), "name": admin.full_name, "role": "org_admin", "group": "Administrator"})
        if dept_id is not None:
            peers = (
                await db.execute(
                    select(User).where(User.dept_id == dept_id, User.is_active.is_(True))
                )
            ).scalars().all()
            for u in peers:
                if str(u.id) != uid and u.role != "dept_head":
                    people.append({"id": str(u.id), "name": u.full_name, "role": u.role, "group": "Your colleagues"})

    return {"people": people, "broadcasts": broadcasts}


@router.post("/messages", status_code=201)
async def send_message(payload: MessageCreate, current_user: AuthUser, db: DbSession):
    """Send a message — text, a file, or both. See the permission matrix above."""
    org_id = uuid.UUID(current_user.org_id)
    dept_id = uuid.UUID(current_user.dept_id) if current_user.dept_id else None
    rid = uuid.UUID(payload.recipient_id) if payload.recipient_id else None
    uid = uuid.UUID(current_user.user_id)

    recipient: Optional[User] = None
    if rid is not None:
        recipient = (
            await db.execute(
                select(User).where(User.id == rid, User.org_id == org_id, User.is_active.is_(True))
            )
        ).scalar_one_or_none()
        if recipient is None:
            raise HTTPException(status_code=404, detail="No such person to message.")

    manages = _manages(current_user)
    if not manages:
        if rid is None:
            raise HTTPException(
                status_code=403,
                detail="Only heads broadcast to a department; you can message your head, "
                       "the admin, or a colleague directly.",
            )
        head = await _head_of(db, dept_id)
        admin = await _org_admin(db, org_id)
        allowed = {str(u.id) for u in (head, admin) if u}
        if dept_id is not None and recipient.dept_id is not None and str(recipient.dept_id) == str(dept_id):
            allowed.add(str(rid))
        if str(rid) not in allowed:
            raise HTTPException(
                status_code=403,
                detail="You can message your own department head, the admin, or a colleague in your department.",
            )

    att = await _resolve_attachment(db, org_id, payload.attachment_id)
    body = (payload.body or "").strip()
    if not body and not att:
        raise HTTPException(status_code=422, detail="Send some text or a file (or both).")
    if not body and att:
        body = "(file attached)"

    sender_name = await _display_name(db, current_user.user_id)
    title = payload.subject or f"Message from {sender_name}"
    notify_body = body + (" [file attached]" if att else "")

    if rid:
        db.add(
            DepartmentMessage(
                org_id=org_id, dept_id=dept_id, sender_id=uid,
                recipient_id=rid, subject=payload.subject, body=body,
                kind="direct", attachment_id=att,
            )
        )
        targets = [rid]
    elif dept_id is not None:
        # Broadcast to the sender's own department: one row, matched by dept_id for
        # every member (efficient — see GET /messages).
        db.add(
            DepartmentMessage(
                org_id=org_id, dept_id=dept_id, sender_id=uid,
                recipient_id=None, subject=payload.subject, body=body,
                kind="announcement", attachment_id=att,
            )
        )
        targets = [
            u.id
            for u in (
                await db.execute(select(User).where(User.dept_id == dept_id, User.is_active.is_(True)))
            ).scalars().all()
            if u.id != uid
        ]
    else:
        # Admin/executive broadcasting with no home department: reaches every
        # department head. No single dept_id to match on, so each head gets their
        # own row (still shows as a normal message in their inbox).
        heads = (
            await db.execute(
                select(User).where(User.org_id == org_id, User.role == "dept_head", User.is_active.is_(True))
            )
        ).scalars().all()
        targets = [h.id for h in heads]
        for h in heads:
            db.add(
                DepartmentMessage(
                    org_id=org_id, dept_id=None, sender_id=uid,
                    recipient_id=h.id, subject=payload.subject, body=body,
                    kind="direct", attachment_id=att,
                )
            )

    for t in targets:
        await _notify(db, org_id, t, title, notify_body, "message")
    await db.commit()
    return {"sent_to": len(targets), "kind": "direct" if rid else "announcement"}


@router.get("/messages")
async def list_messages(*, current_user: AuthUser, db: DbSession, limit: int = 20):
    """Messages addressed to this person or broadcast to their department."""
    dept_id = uuid.UUID(current_user.dept_id) if current_user.dept_id else None
    uid = uuid.UUID(current_user.user_id)
    rows = (
        await db.execute(
            select(DepartmentMessage)
            .where(
                (DepartmentMessage.recipient_id == uid)
                | (
                    (DepartmentMessage.recipient_id.is_(None))
                    & (DepartmentMessage.dept_id == dept_id)
                )
            )
            .order_by(DepartmentMessage.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    senders = {
        u.id: u.full_name
        for u in (
            await db.execute(
                select(User).where(User.id.in_([r.sender_id for r in rows] or [uuid.uuid4()]))
            )
        ).scalars().all()
    }
    amap = await _attachments_map(db, [r.attachment_id for r in rows])
    return {
        "count": len(rows),
        "messages": [
            {
                "id": str(r.id), "from": senders.get(r.sender_id, "Unknown"),
                "subject": r.subject, "body": r.body, "kind": r.kind,
                "sent_at": r.created_at.isoformat() if r.created_at else None,
                "attachment": amap.get(r.attachment_id),
            }
            for r in rows
        ],
    }


@router.get("/heads")
async def department_heads(*, current_user: AuthUser, db: DbSession):
    """The other department heads — so a head (or the admin) can message across
    departments when one department needs another. Uses the direct-message path
    (`POST /messages` with `recipient_id`), which already notifies the recipient.
    """
    if not _manages(current_user):
        raise HTTPException(
            status_code=403, detail="Heads, managers and the admin message across departments."
        )
    org_id = uuid.UUID(current_user.org_id)
    rows = (
        await db.execute(
            select(User).where(
                User.org_id == org_id,
                User.role == "dept_head",
                User.is_active.is_(True),
            )
        )
    ).scalars().all()
    depts = {
        str(d.id): d.name
        for d in (
            await db.execute(select(Department).where(Department.org_id == org_id))
        ).scalars().all()
    }
    return {
        "heads": [
            {
                "id": str(u.id),
                "name": u.full_name,
                "department": depts.get(str(u.dept_id), "—"),
            }
            for u in rows
            if str(u.id) != current_user.user_id
        ]
    }


class InterDeptRequest(BaseModel):
    to_head_id: str
    title: str = Field(min_length=2, max_length=300)
    detail: Optional[str] = Field(default=None, max_length=4000)
    attachment_id: Optional[str] = None


@router.post("/interdept-request", status_code=201)
async def interdept_request(payload: InterDeptRequest, current_user: AuthUser, db: DbSession):
    """One department formally asks another for something and awaits its head's approval.

    Reuses the approval-request machinery: the target department's head becomes the
    approver, so it lands in *their* queue (`/requests/queue`) and the asking head
    tracks the outcome in `/requests/me`. The decision notifies the requester.
    """
    if not _manages(current_user):
        raise HTTPException(status_code=403, detail="Heads, managers and the admin raise these.")
    org_id = uuid.UUID(current_user.org_id)
    target = (
        await db.execute(
            select(User).where(
                User.id == uuid.UUID(payload.to_head_id),
                User.org_id == org_id,
                User.role == "dept_head",
                User.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="No such department head.")
    if str(target.id) == current_user.user_id:
        raise HTTPException(status_code=400, detail="That is your own department.")

    who = await _display_name(db, current_user.user_id)
    att = await _resolve_attachment(db, org_id, payload.attachment_id)
    row = ApprovalRequest(
        org_id=org_id,
        dept_id=uuid.UUID(current_user.dept_id) if current_user.dept_id else None,
        requester_id=uuid.UUID(current_user.user_id),
        approver_id=target.id,
        request_type="interdept",
        title=payload.title,
        detail=payload.detail,
        status=RequestStatus.PENDING,
        attachment_id=att,
    )
    db.add(row)
    await _notify(
        db, org_id, target.id, "A department needs something",
        f"{who} asked: “{payload.title}”.",
        "approval",
    )
    await db.commit()
    await db.refresh(row)
    return {"id": str(row.id), "status": row.status, "sent_to": target.full_name}


# ───────────────────────────── Finance extras ─────────────────────────────


@router.get("/finance/overview")
async def finance_overview(*, current_user: AuthUser, db: DbSession):
    """Salary, funding and profit. Finance and the administrator only."""
    org_id = uuid.UUID(current_user.org_id)
    cross = Permission.READ_CROSS_DEPARTMENT.value in current_user.permissions
    is_finance = False
    if current_user.dept_id:
        d = (
            await db.execute(select(Department).where(Department.id == uuid.UUID(current_user.dept_id)))
        ).scalar_one_or_none()
        is_finance = bool(d and d.code == "FIN")
    if not (cross or (is_finance and _manages(current_user))):
        raise HTTPException(
            status_code=403,
            detail="Salary and funding are visible to Finance and the administrator.",
        )

    salaries = (
        await db.execute(select(SalaryRecord).where(SalaryRecord.org_id == org_id))
    ).scalars().all()
    finance = (
        await db.execute(select(CompanyFinance).where(CompanyFinance.org_id == org_id))
    ).scalars().all()
    depts = {
        str(d.id): d.name
        for d in (
            await db.execute(select(Department).where(Department.org_id == org_id))
        ).scalars().all()
    }

    by_dept: dict[str, float] = {}
    for s in salaries:
        by_dept[depts.get(str(s.dept_id), "Unassigned")] = (
            by_dept.get(depts.get(str(s.dept_id), "Unassigned"), 0.0) + s.annual_amount
        )
    funding = [f for f in finance if f.entry_type == "funding"]
    profit = [f for f in finance if f.entry_type == "profit"]

    return {
        "payroll": {
            "people_on_payroll": len(salaries),
            "annual_total": round(sum(s.annual_amount for s in salaries), 2),
            "by_department": [
                {"department": k, "annual_total": round(v, 2)}
                for k, v in sorted(by_dept.items(), key=lambda x: -x[1])
            ],
        },
        "funding": [
            {"label": f.label, "amount": f.amount, "period": f.period, "note": f.note}
            for f in sorted(funding, key=lambda x: x.period)
        ],
        "profit": [
            {"label": f.label, "amount": f.amount, "period": f.period}
            for f in sorted(profit, key=lambda x: x.period)
        ],
        "funding_total": round(sum(f.amount for f in funding), 2),
        "profit_total": round(sum(f.amount for f in profit), 2),
    }
