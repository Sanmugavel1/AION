"""
AION Enterprise Models — SRS v2.0 (Sections 12-13, 15, 30-35, 39)

These tables carry the enterprise scaffolding: the approval chain, the cross-department
marketplace, notifications, the organizational memory timeline, learning records, and
the audit trail. None of them duplicate the intelligence engines — they record workflow
and provenance around knowledge that the existing engines already score.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.types import JSONB, UUID


class WorkflowStatus:
    """Document lifecycle states (SRS Section 12).

    Employee submits -> Manager first-pass -> Department Head final -> repository.
    RETURNED is distinct from REJECTED: returned work is expected back after revision,
    rejected work is not.
    """

    DRAFT = "draft"
    PENDING_MANAGER = "pending_manager"
    PENDING_HEAD = "pending_head"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"

    OPEN = (PENDING_MANAGER, PENDING_HEAD, RETURNED)
    ALL = (DRAFT, PENDING_MANAGER, PENDING_HEAD, APPROVED, REJECTED, RETURNED)


class ApprovalLog(BaseModel):
    """Immutable record of every approval-chain transition (SRS Appendix B)."""

    __tablename__ = "approval_logs"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    dept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id")
    )
    knowledge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_items.id"), nullable=False
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    actor_role: Mapped[Optional[str]] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # submit/approve/reject/return
    from_status: Mapped[Optional[str]] = mapped_column(String(50))
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)


class MarketplaceItem(BaseModel):
    """Knowledge explicitly published for cross-department reuse (SRS Section 30).

    Departments stay isolated by default; publishing here is the controlled opt-in
    that lets other departments see and reuse an item.
    """

    __tablename__ = "marketplace_items"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    source_dept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id")
    )
    knowledge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_items.id"), nullable=False
    )
    publisher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default="sop")  # sop/best_practice/template
    rating_sum: Mapped[int] = mapped_column(Integer, default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    reuse_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    @property
    def average_rating(self) -> Optional[float]:
        if not self.rating_count:
            return None
        return round(self.rating_sum / self.rating_count, 2)


class MarketplaceReuse(BaseModel):
    """One department adopting another's published item — the Section 30 reuse event.

    Kept separate from the counter on MarketplaceItem so 'time to reuse' and the
    per-department collaboration metrics can be computed from real timestamps.
    """

    __tablename__ = "marketplace_reuses"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplace_items.id"), nullable=False
    )
    target_dept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id")
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    rating: Mapped[Optional[int]] = mapped_column(Integer)
    comment: Mapped[Optional[str]] = mapped_column(Text)


class Notification(BaseModel):
    """Workflow and AI events routed to a specific user (SRS Section 35)."""

    __tablename__ = "notifications"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), default="workflow")
    severity: Mapped[str] = mapped_column(String(20), default="info")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text)
    link_type: Mapped[Optional[str]] = mapped_column(String(50))
    link_id: Mapped[Optional[str]] = mapped_column(String(100))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class TimelineEvent(BaseModel):
    """Organizational memory timeline entry (SRS Section 31).

    Every entry keeps source_type/source_id so the UI can link back to the record
    that produced it rather than showing an orphaned headline.
    """

    __tablename__ = "timeline_events"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    dept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id")
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    source_id: Mapped[Optional[str]] = mapped_column(String(100))
    event_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)


class LearningRecord(BaseModel):
    """Learning assigned or completed against a detected gap (SRS Section 34).

    knowledge_score_before/after exist so learning effectiveness can be measured as a
    real delta rather than assumed from completion alone.
    """

    __tablename__ = "learning_records"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    dept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    resource_type: Mapped[str] = mapped_column(String(50), default="document")
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    skill_area: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="assigned")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    knowledge_score_before: Mapped[Optional[float]] = mapped_column(Float)
    knowledge_score_after: Mapped[Optional[float]] = mapped_column(Float)


class AuditLog(BaseModel):
    """Immutable security/compliance trail (SRS Sections 15, 39)."""

    __tablename__ = "audit_logs"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    actor_role: Mapped[Optional[str]] = mapped_column(String(50))
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(50))
    target_id: Mapped[Optional[str]] = mapped_column(String(100))
    outcome: Mapped[str] = mapped_column(String(20), default="success")
    detail: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
