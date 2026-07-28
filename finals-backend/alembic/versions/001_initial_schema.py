"""Initial AION schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── organizations ────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("industry", sa.String(100)),
        sa.Column("size", sa.String(50)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("subscription_tier", sa.String(50), default="free"),
        sa.Column("metadata", postgresql.JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ── departments ──────────────────────────────────────────────────────────
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(50)),
        sa.Column("head_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200)),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), default="viewer"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── knowledge_items ──────────────────────────────────────────────────────
    op.create_table(
        "knowledge_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text),
        sa.Column("domain", sa.String(100), nullable=False),
        sa.Column("source_type", sa.String(100)),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("status", sa.String(50), default="active"),
        sa.Column("relevance_score", sa.Float, default=1.0),
        sa.Column("half_life_days", sa.Float),
        sa.Column("decay_rate", sa.Float),
        sa.Column("access_count", sa.Integer, default=0),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True)),
        sa.Column("is_outdated", sa.Boolean, default=False),
        sa.Column("is_conflicted", sa.Boolean, default=False),
        sa.Column("is_duplicate", sa.Boolean, default=False),
        sa.Column("is_isolated", sa.Boolean, default=False),
        sa.Column("graph_node_id", sa.String(200)),
        sa.Column("vector_id", sa.String(200)),
        sa.Column("tags", postgresql.JSONB, default=[]),
        sa.Column("metadata", postgresql.JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── documents ────────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("knowledge_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_items.id"), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50)),
        sa.Column("file_size_bytes", sa.Integer),
        sa.Column("storage_path", sa.String(1000)),
        sa.Column("processing_status", sa.String(50), default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── employee_knowledge_profiles ──────────────────────────────────────────
    op.create_table(
        "employee_knowledge_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("knowledge_criticality_score", sa.Float, default=0.0),
        sa.Column("replacement_difficulty_score", sa.Float, default=0.0),
        sa.Column("knowledge_risk_score", sa.Float, default=0.0),
        sa.Column("primary_domains", postgresql.JSONB, default=[]),
        sa.Column("technical_expertise", postgresql.JSONB, default=[]),
        sa.Column("hidden_knowledge", postgresql.JSONB, default=[]),
        sa.Column("active_projects", postgresql.JSONB, default=[]),
        sa.Column("unfinished_tasks", postgresql.JSONB, default=[]),
        sa.Column("reasoning_patterns", postgresql.JSONB, default={}),
        sa.Column("collaboration_network", postgresql.JSONB, default=[]),
        sa.Column("recommended_successors", postgresql.JSONB, default=[]),
        sa.Column("is_departure_initiated", sa.Boolean, default=False),
        sa.Column("departure_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_style", sa.String(50)),
        sa.Column("work_style", sa.String(50)),
        sa.Column("communication_style", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── disease_records ──────────────────────────────────────────────────────
    op.create_table(
        "disease_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("disease_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("severity_score", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, default=0.8),
        sa.Column("evidence", postgresql.JSONB, default={}),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_resolved", sa.Boolean, default=False),
        sa.Column("predicted_critical_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("days_until_critical", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── intelligence_snapshots ───────────────────────────────────────────────
    op.create_table(
        "intelligence_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("overall_health", sa.Float),
        sa.Column("knowledge_velocity", sa.Float),
        sa.Column("knowledge_coverage", sa.Float),
        sa.Column("knowledge_quality", sa.Float),
        sa.Column("learning_agility", sa.Float),
        sa.Column("collaboration_density", sa.Float),
        sa.Column("innovation_index", sa.Float),
        sa.Column("decision_intelligence", sa.Float),
        sa.Column("cognitive_resilience", sa.Float),
        sa.Column("knowledge_accessibility", sa.Float),
        sa.Column("expertise_depth", sa.Float),
        sa.Column("knowledge_retention", sa.Float),
        sa.Column("adaptability_score", sa.Float),
        sa.Column("knowledge_half_life", sa.Float),
        sa.Column("knowledge_entropy", sa.Float),
        sa.Column("memory_compression", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── simulation_records ───────────────────────────────────────────────────
    op.create_table(
        "simulation_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("initiated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scenario_type", sa.String(100), nullable=False),
        sa.Column("scenario_description", sa.Text),
        sa.Column("parameters", postgresql.JSONB, default={}),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cascade_chain", postgresql.JSONB, default=[]),
        sa.Column("affected_projects", postgresql.JSONB, default=[]),
        sa.Column("affected_customers", postgresql.JSONB, default=[]),
        sa.Column("revenue_risk_usd", sa.Float, nullable=True),
        sa.Column("recovery_time_days", sa.Integer, nullable=True),
        sa.Column("knowledge_loss_percentage", sa.Float, nullable=True),
        sa.Column("business_impact_summary", sa.Text, nullable=True),
        sa.Column("full_results", postgresql.JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── healing_actions ──────────────────────────────────────────────────────
    op.create_table(
        "healing_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("triggered_by_disease_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("disease_records.id"), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("priority", sa.String(20), default="medium"),
        sa.Column("estimated_impact", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("parameters", postgresql.JSONB, default={}),
        sa.Column("target_entities", postgresql.JSONB, default=[]),
        sa.Column("outcome", sa.Text, nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── indexes ──────────────────────────────────────────────────────────────
    op.create_index("ix_users_org_id", "users", ["org_id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_knowledge_org_id", "knowledge_items", ["org_id"])
    op.create_index("ix_knowledge_domain", "knowledge_items", ["domain"])
    op.create_index("ix_knowledge_status", "knowledge_items", ["status"])
    op.create_index("ix_knowledge_relevance", "knowledge_items", ["relevance_score"])
    op.create_index("ix_disease_org_type", "disease_records", ["org_id", "disease_type"])
    op.create_index("ix_disease_detected_at", "disease_records", ["detected_at"])
    op.create_index("ix_intel_org_computed", "intelligence_snapshots", ["org_id", "computed_at"])
    op.create_index("ix_healing_org_status", "healing_actions", ["org_id", "status"])


def downgrade() -> None:
    op.drop_table("healing_actions")
    op.drop_table("simulation_records")
    op.drop_table("intelligence_snapshots")
    op.drop_table("disease_records")
    op.drop_table("employee_knowledge_profiles")
    op.drop_table("documents")
    op.drop_table("knowledge_items")
    op.drop_table("users")
    op.drop_table("departments")
    op.drop_table("organizations")
