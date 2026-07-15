"""
AION Employee Knowledge DNA Profile Model (OCSIE Module)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from app.models.types import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class EmployeeKnowledgeProfile(BaseModel):
    __tablename__ = "employee_knowledge_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # Criticality scores
    knowledge_criticality_score: Mapped[float] = mapped_column(Float, default=0.0)
    replacement_difficulty_score: Mapped[float] = mapped_column(Float, default=0.0)
    knowledge_risk_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Work style (inferred from behavior)
    decision_style: Mapped[Optional[str]] = mapped_column(String(50))  # fast/slow/hierarchical/collaborative
    communication_style: Mapped[Optional[str]] = mapped_column(String(50))  # formal/informal/mixed
    work_style: Mapped[Optional[str]] = mapped_column(String(50))  # analytical/intuitive/mixed
    problem_solving_approach: Mapped[Optional[str]] = mapped_column(Text)

    # Knowledge areas
    primary_domains: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)  # ["cloud", "security"]
    technical_expertise: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    business_expertise: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    # Responsibilities
    critical_responsibilities: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    hidden_knowledge: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)

    # Projects
    active_projects: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    unfinished_tasks: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)

    # Reasoning trace (how this person thinks)
    reasoning_patterns: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    decision_history_summary: Mapped[Optional[str]] = mapped_column(Text)

    # Collaboration network
    collaboration_network: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)  # [{user_id, strength}]
    customer_contacts: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    vendor_contacts: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    stakeholders: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)

    # Successor info
    recommended_successors: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)

    # Profile freshness
    last_computed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_departure_initiated: Mapped[bool] = mapped_column(Boolean, default=False)
    departure_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    departure_reason: Mapped[Optional[str]] = mapped_column(String(100))

    user: Mapped["User"] = relationship("User", back_populates="employee_profile")
