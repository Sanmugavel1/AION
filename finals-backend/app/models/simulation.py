"""
AION Simulation & Healing Action Models
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from app.models.types import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SimulationRecord(BaseModel):
    __tablename__ = "simulation_records"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    initiated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    scenario_type: Mapped[str] = mapped_column(String(100), nullable=False)
    scenario_description: Mapped[str] = mapped_column(Text, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)

    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending | running | completed | failed
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Results
    cascade_chain: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    affected_projects: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    affected_customers: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    revenue_risk_usd: Mapped[Optional[float]] = mapped_column(Float)
    recovery_time_days: Mapped[Optional[int]] = mapped_column(Integer)
    knowledge_loss_percentage: Mapped[Optional[float]] = mapped_column(Float)
    business_impact_summary: Mapped[Optional[str]] = mapped_column(Text)
    full_results: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)


class HealingAction(BaseModel):
    __tablename__ = "healing_actions"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    triggered_by_disease_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("disease_records.id"))
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # create_sop | assign_mentor | schedule_training | merge_docs | archive_files
    # notify_managers | generate_onboarding | create_quiz | update_wiki | knowledge_transfer

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # critical | high | medium | low
    estimated_impact: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(50), default="pending")
    # pending | approved | in_progress | completed | rejected | cancelled

    parameters: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    target_entities: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    outcome: Mapped[Optional[str]] = mapped_column(Text)

    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
