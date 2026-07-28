"""
AION Workplace Models — the day-to-day management layer from the handwritten notes.

These carry what an organization actually runs on between knowledge events: leave
requests and balances, approval requests raised by an employee to their head, the
inter-department fund chain (department -> Finance -> Admin -> intimation back), and
department messages. They sit alongside the existing enterprise tables and duplicate
none of them — the document approval chain in `enterprise.py` stays exactly as it is.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.types import JSONB, UUID


class RequestStatus:
    """States shared by leave, approval and fund requests."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    # Sent back for changes rather than refused outright.
    RETURNED = "returned"

    OPEN = (PENDING,)
    CLOSED = (APPROVED, REJECTED)


#: Annual leave entitlement, stated in the notes: "They can take 30 days leave per year".
ANNUAL_LEAVE_DAYS = 30


class LeaveRequest(BaseModel):
    """An employee asking their department head for leave.

    The balance shown on a dashboard is derived from these rows rather than stored as
    a counter, so an approval or a reversal cannot leave the two disagreeing.
    """

    __tablename__ = "leave_requests"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    dept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), index=True
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    #: The head the request was routed to, resolved at submission time.
    approver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )

    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    leave_type: Mapped[str] = mapped_column(String(40), default="annual")
    reason: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), default=RequestStatus.PENDING, index=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    decision_note: Mapped[Optional[str]] = mapped_column(Text)
    #: Calendar year the days count against, so a balance query never spans years.
    leave_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    #: Optional supporting file (e.g. a medical note) sent with the request.
    attachment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attachments.id"), nullable=True
    )


class ApprovalRequest(BaseModel):
    """A project or policy an employee sends up for approval.

    Notes, Employee (v): "Ability to send his project, any new policy to his head for
    the approval". Distinct from the document workflow in `enterprise.py`, which
    governs uploaded knowledge files; this is the person-to-person ask.
    """

    __tablename__ = "approval_requests"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    dept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), index=True
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    approver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )

    #: "project" | "policy" — the two kinds named in the notes.
    request_type: Mapped[str] = mapped_column(String(40), default="project", index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), default=RequestStatus.PENDING, index=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    #: The head's feedback, which the notes require flow back to the employee.
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    #: Optional file sent with the project/policy or cross-department request.
    attachment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attachments.id"), nullable=True
    )


class FundRequest(BaseModel):
    """The inter-department fund chain described in the notes.

    "if a dept. wants to raise a fund, they will send a mail to finance dept. & they
    will send approve & pass to admin, again they will send an intimation to the called
    department." Modelled as an explicit two-stage chain so the current owner of the
    request is always answerable from one column.
    """

    __tablename__ = "fund_requests"

    #: Stage the request is sitting at.
    STAGE_FINANCE = "with_finance"
    STAGE_ADMIN = "with_admin"
    STAGE_INTIMATED = "intimated"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    #: Department raising the request.
    dept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    purpose: Mapped[Optional[str]] = mapped_column(Text)

    stage: Mapped[str] = mapped_column(String(24), default=STAGE_FINANCE, index=True)
    status: Mapped[str] = mapped_column(String(20), default=RequestStatus.PENDING, index=True)

    finance_decided_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    finance_decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finance_note: Mapped[Optional[str]] = mapped_column(Text)

    admin_decided_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    admin_decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    admin_note: Mapped[Optional[str]] = mapped_column(Text)

    #: Set when the intimation has gone back to the requesting department.
    intimated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class DepartmentMessage(BaseModel):
    """A head messaging their department, or one person in it.

    Notes: "able to send a message to all the employee at a single time & also able to
    send a msg to single employee." A null `recipient_id` means the whole department.
    """

    __tablename__ = "department_messages"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    dept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    #: Null = broadcast to the whole department.
    recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )

    subject: Mapped[Optional[str]] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    #: "announcement" | "direct" | "update"
    kind: Mapped[str] = mapped_column(String(30), default="announcement")
    #: Optional file shared with the message.
    attachment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attachments.id"), nullable=True
    )


class Attachment(BaseModel):
    """A file attached to any communication — a message, a request, or a leave note.

    Stored once and referenced by id, so the same upload machinery serves every flow
    in the hierarchy (employee↔head, head↔head, head↔admin). The bytes live on disk
    under data/attachments; this row is the metadata the recipient sees.
    """

    __tablename__ = "attachments"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    content_type: Mapped[str] = mapped_column(String(150), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)


class SalaryRecord(BaseModel):
    """Finance-only: what each person is paid.

    Notes, additional feature for finance: "They should able maintain all the salary
    details, company's fundings, profit management."
    """

    __tablename__ = "salary_records"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    dept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), index=True
    )

    annual_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    effective_from: Mapped[datetime] = mapped_column(Date, nullable=False)
    band: Mapped[Optional[str]] = mapped_column(String(40))


class CompanyFinance(BaseModel):
    """Funding and profit lines the finance department maintains."""

    __tablename__ = "company_finance"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    #: "funding" | "profit" | "cost"
    entry_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "2026-Q2"
    note: Mapped[Optional[str]] = mapped_column(Text)


class EmployeeProfileDetail(BaseModel):
    """The employee record fields named in the notes and SRS Section 7.

    Kept separate from `users` so the auth table stays small and this can grow with
    whatever HR needs next.
    """

    __tablename__ = "employee_profile_details"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    #: SRS Section 7 format: EMP1001, EMP1002, sequential across the organization.
    employee_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    designation: Mapped[Optional[str]] = mapped_column(String(150))
    joining_date: Mapped[Optional[datetime]] = mapped_column(Date)
    reporting_head_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    #: Skill matrix and current/past project assignments, per Employee (i)-(ii).
    skills: Mapped[Optional[dict]] = mapped_column(JSONB)
    current_projects: Mapped[Optional[dict]] = mapped_column(JSONB)
    completed_projects: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_trainee: Mapped[bool] = mapped_column(Boolean, default=False)
