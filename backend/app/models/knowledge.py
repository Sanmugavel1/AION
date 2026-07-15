"""
AION Knowledge & Document Models
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from app.models.types import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class KnowledgeItem(BaseModel):
    __tablename__ = "knowledge_items"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    dept_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"))
    creator_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    domain: Mapped[Optional[str]] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50), default="document")  # document, email, chat, meeting, code
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))
    source_id: Mapped[Optional[str]] = mapped_column(String(255))
    file_path: Mapped[Optional[str]] = mapped_column(String(1000))
    file_type: Mapped[Optional[str]] = mapped_column(String(50))

    # Decay tracking
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    half_life_days: Mapped[Optional[float]] = mapped_column(Float)
    decay_rate: Mapped[float] = mapped_column(Float, default=0.01)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_outdated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_conflicted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    is_isolated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Neo4j node ID for graph linkage
    graph_node_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Qdrant vector ID
    vector_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Metadata
    tags: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    item_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)


class Document(BaseModel):
    __tablename__ = "documents"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    knowledge_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_items.id"))
    uploader_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    minio_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_extracted: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    page_count: Mapped[Optional[int]] = mapped_column(Integer)
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    language: Mapped[Optional[str]] = mapped_column(String(10))
