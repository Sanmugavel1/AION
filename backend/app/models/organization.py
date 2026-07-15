"""
AION Organization & Department Models
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from app.models.types import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    size: Mapped[Optional[int]] = mapped_column(Integer)
    website: Mapped[Optional[str]] = mapped_column(String(500))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    departments: Mapped[List["Department"]] = relationship(
        "Department", back_populates="organization", cascade="all, delete-orphan"
    )
    users: Mapped[List["User"]] = relationship("User", back_populates="organization")


class Department(BaseModel):
    __tablename__ = "departments"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    head_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="departments")
    children: Mapped[List["Department"]] = relationship("Department", back_populates="parent")
    parent: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="children", remote_side="Department.id"
    )
    users: Mapped[List["User"]] = relationship("User", back_populates="department")
