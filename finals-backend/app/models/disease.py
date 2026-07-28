"""
AION Organizational Disease Models
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from app.models.types import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class DiseaseRecord(BaseModel):
    __tablename__ = "disease_records"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    disease_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # knowledge_cancer | memory_alzheimers | communication_stroke | knowledge_obesity | innovation_paralysis

    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # critical | warning | healthy
    severity_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 – 1.0
    confidence: Mapped[float] = mapped_column(Float, default=0.8)  # 0.0 – 1.0

    evidence: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    affected_entities: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    predicted_critical_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    days_until_critical: Mapped[Optional[int]] = mapped_column(Integer)

    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class IntelligenceSnapshot(BaseModel):
    """Stores the complete OII score for an organization at a point in time."""
    __tablename__ = "intelligence_snapshots"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Composite
    overall_health: Mapped[float] = mapped_column(Float, default=0.0)

    # 12 OII Dimensions (0.0 – 1.0)
    knowledge_velocity: Mapped[float] = mapped_column(Float, default=0.0)
    knowledge_coverage: Mapped[float] = mapped_column(Float, default=0.0)
    knowledge_quality: Mapped[float] = mapped_column(Float, default=0.0)
    learning_agility: Mapped[float] = mapped_column(Float, default=0.0)
    collaboration_density: Mapped[float] = mapped_column(Float, default=0.0)
    innovation_index: Mapped[float] = mapped_column(Float, default=0.0)
    decision_intelligence: Mapped[float] = mapped_column(Float, default=0.0)
    cognitive_resilience: Mapped[float] = mapped_column(Float, default=0.0)
    knowledge_accessibility: Mapped[float] = mapped_column(Float, default=0.0)
    expertise_depth: Mapped[float] = mapped_column(Float, default=0.0)
    knowledge_retention: Mapped[float] = mapped_column(Float, default=0.0)
    adaptability_score: Mapped[float] = mapped_column(Float, default=0.0)

    # 3 Proprietary Metrics
    knowledge_half_life: Mapped[Optional[float]] = mapped_column(Float)
    knowledge_entropy: Mapped[Optional[float]] = mapped_column(Float)
    memory_compression: Mapped[Optional[float]] = mapped_column(Float)

    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
