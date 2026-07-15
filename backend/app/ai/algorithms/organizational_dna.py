"""
AION Organizational DNA Engine
Automatically infer organization's behavioral signature from observed data
"""
from __future__ import annotations

import statistics
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


class OrganizationalDNAProfile:
    """Represents the inferred DNA of an organization."""

    def __init__(
        self,
        decision_style: str,
        knowledge_style: str,
        innovation_style: str,
        risk_behaviour: str,
        communication_style: str,
        learning_behaviour: str,
        knowledge_behaviour: str,
        confidence_scores: Dict[str, float],
        raw_indicators: Dict,
    ) -> None:
        self.decision_style = decision_style
        self.knowledge_style = knowledge_style
        self.innovation_style = innovation_style
        self.risk_behaviour = risk_behaviour
        self.communication_style = communication_style
        self.learning_behaviour = learning_behaviour
        self.knowledge_behaviour = knowledge_behaviour
        self.confidence_scores = confidence_scores
        self.raw_indicators = raw_indicators

    def to_dict(self) -> Dict:
        return {
            "decision_style": self.decision_style,
            "knowledge_style": self.knowledge_style,
            "innovation_style": self.innovation_style,
            "risk_behaviour": self.risk_behaviour,
            "communication_style": self.communication_style,
            "learning_behaviour": self.learning_behaviour,
            "knowledge_behaviour": self.knowledge_behaviour,
            "confidence_scores": self.confidence_scores,
            "raw_indicators": self.raw_indicators,
        }


def infer_decision_style(decisions: List[Dict]) -> Tuple[str, float]:
    """
    Infer decision style from decision history.
    decisions: [{id, created_at, participants, approvers, time_to_decision_hours}]
    """
    if not decisions:
        return "unknown", 0.0

    avg_time = statistics.mean(
        d.get("time_to_decision_hours", 48) for d in decisions
    )
    avg_participants = statistics.mean(
        len(d.get("participants", [])) for d in decisions
    )
    avg_approvers = statistics.mean(
        len(d.get("approvers", [])) for d in decisions
    )

    if avg_time < 24 and avg_participants <= 2:
        style, confidence = "fast", 0.85
    elif avg_approvers >= 3 and avg_time > 72:
        style, confidence = "hierarchical", 0.80
    elif avg_participants >= 4:
        style, confidence = "collaborative", 0.82
    else:
        style, confidence = "slow", 0.70

    return style, confidence


def infer_knowledge_style(knowledge_items: List[Dict]) -> Tuple[str, float]:
    """
    Infer how the organization captures knowledge.
    knowledge_items: [{source_type: document|meeting|chat|code|email}]
    """
    if not knowledge_items:
        return "unknown", 0.0

    source_counts = Counter(item.get("source_type", "document") for item in knowledge_items)
    total = sum(source_counts.values())

    doc_ratio = (source_counts.get("document", 0) + source_counts.get("code", 0)) / total
    meeting_ratio = source_counts.get("meeting", 0) / total
    chat_ratio = (source_counts.get("chat", 0) + source_counts.get("email", 0)) / total

    if doc_ratio >= 0.5:
        return "document_heavy", min(0.95, 0.5 + doc_ratio * 0.5)
    elif meeting_ratio >= 0.4:
        return "meeting_heavy", min(0.95, 0.5 + meeting_ratio * 0.5)
    elif chat_ratio >= 0.4:
        return "chat_heavy", min(0.95, 0.5 + chat_ratio * 0.5)
    else:
        return "mixed", 0.65


def infer_innovation_style(
    projects: List[Dict],
    window_days: int = 90,
) -> Tuple[str, float]:
    """
    Infer innovation style from new project/initiative creation rate.
    projects: [{id, created_at, type}]
    """
    if not projects:
        return "low", 0.5

    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    recent_projects = [
        p for p in projects
        if _parse_dt(p.get("created_at")) > cutoff
    ]
    new_initiative_count = len([
        p for p in recent_projects
        if p.get("type") in ("initiative", "innovation", "r&d", "experiment")
    ])

    rate_per_month = (len(recent_projects) / window_days) * 30

    if rate_per_month >= 5 or new_initiative_count >= 3:
        return "high", 0.80
    elif rate_per_month >= 2:
        return "medium", 0.75
    else:
        return "low", 0.70


def infer_risk_behaviour(
    decisions: List[Dict],
    projects: List[Dict],
) -> Tuple[str, float]:
    """
    Infer risk appetite from decision and project data.
    """
    if not decisions and not projects:
        return "unknown", 0.0

    # Decisions with high stakes = risk indicators
    high_risk_decisions = sum(
        1 for d in decisions
        if d.get("risk_level", "low") in ("high", "critical")
    )
    total_decisions = max(len(decisions), 1)
    risk_decision_ratio = high_risk_decisions / total_decisions

    # Projects with experimental/moonshot tags
    risky_projects = sum(
        1 for p in projects
        if p.get("type") in ("experiment", "r&d", "pilot") or p.get("is_risky", False)
    )
    project_risk_ratio = risky_projects / max(len(projects), 1)

    combined = (risk_decision_ratio * 0.6) + (project_risk_ratio * 0.4)

    if combined >= 0.35:
        return "aggressive", min(0.90, 0.5 + combined)
    elif combined >= 0.15:
        return "moderate", 0.75
    else:
        return "conservative", min(0.90, 0.5 + (0.35 - combined))


def infer_communication_style(
    knowledge_items: List[Dict],
    decisions: List[Dict],
) -> Tuple[str, float]:
    """
    Infer communication style from data sources.
    """
    chat_email_count = sum(
        1 for k in knowledge_items
        if k.get("source_type") in ("chat", "email")
    )
    doc_count = sum(
        1 for k in knowledge_items
        if k.get("source_type") in ("document", "wiki")
    )
    total = max(chat_email_count + doc_count, 1)

    informal_ratio = chat_email_count / total

    if informal_ratio >= 0.65:
        return "informal", 0.78
    elif informal_ratio <= 0.35:
        return "formal", 0.78
    else:
        return "mixed", 0.70


def infer_learning_behaviour(
    knowledge_items: List[Dict],
    training_events: List[Dict],
) -> Tuple[str, float]:
    """
    Infer learning speed from knowledge creation velocity.
    """
    if not knowledge_items:
        return "slow", 0.5

    now = datetime.now(timezone.utc)
    cutoff_30 = now - timedelta(days=30)
    cutoff_90 = now - timedelta(days=90)

    recent_30 = sum(
        1 for k in knowledge_items
        if _parse_dt(k.get("created_at")) > cutoff_30
    )
    recent_90 = sum(
        1 for k in knowledge_items
        if _parse_dt(k.get("created_at")) > cutoff_90
    )

    monthly_rate = recent_30
    quarterly_acceleration = recent_90 / 3  # avg per month

    if monthly_rate >= quarterly_acceleration * 1.3:
        return "fast_accelerating", 0.82
    elif monthly_rate >= 5:
        return "fast", 0.78
    elif monthly_rate >= 2:
        return "moderate", 0.72
    else:
        return "slow", 0.68


def infer_knowledge_behaviour(
    sharing_events: List[Dict],
    total_employees: int,
) -> Tuple[str, float]:
    """
    Infer whether the org hoards or shares knowledge.
    """
    if not sharing_events or total_employees == 0:
        return "hoarder", 0.55

    sharers = len(set(e.get("sharer_id") for e in sharing_events))
    sharing_rate = sharers / total_employees

    if sharing_rate >= 0.5:
        return "sharer", min(0.90, 0.5 + sharing_rate * 0.5)
    elif sharing_rate >= 0.25:
        return "mixed", 0.70
    else:
        return "hoarder", min(0.90, 0.5 + (0.5 - sharing_rate) * 0.8)


def compute_organizational_dna(
    decisions: List[Dict],
    knowledge_items: List[Dict],
    projects: List[Dict],
    training_events: Optional[List[Dict]] = None,
    sharing_events: Optional[List[Dict]] = None,
    total_employees: int = 1,
) -> OrganizationalDNAProfile:
    """
    Full Organizational DNA inference pipeline.
    Combines all dimension inferences into a cohesive profile.
    """
    decision_style, d_conf = infer_decision_style(decisions)
    knowledge_style, k_conf = infer_knowledge_style(knowledge_items)
    innovation_style, i_conf = infer_innovation_style(projects)
    risk_behaviour, r_conf = infer_risk_behaviour(decisions, projects)
    communication_style, c_conf = infer_communication_style(knowledge_items, decisions)
    learning_behaviour, l_conf = infer_learning_behaviour(
        knowledge_items, training_events or []
    )
    knowledge_behaviour, kb_conf = infer_knowledge_behaviour(
        sharing_events or [], total_employees
    )

    return OrganizationalDNAProfile(
        decision_style=decision_style,
        knowledge_style=knowledge_style,
        innovation_style=innovation_style,
        risk_behaviour=risk_behaviour,
        communication_style=communication_style,
        learning_behaviour=learning_behaviour,
        knowledge_behaviour=knowledge_behaviour,
        confidence_scores={
            "decision_style": d_conf,
            "knowledge_style": k_conf,
            "innovation_style": i_conf,
            "risk_behaviour": r_conf,
            "communication_style": c_conf,
            "learning_behaviour": l_conf,
            "knowledge_behaviour": kb_conf,
        },
        raw_indicators={
            "total_decisions": len(decisions),
            "total_knowledge_items": len(knowledge_items),
            "total_projects": len(projects),
            "total_employees": total_employees,
        },
    )


def _parse_dt(value: Optional[str | datetime]) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.min.replace(tzinfo=timezone.utc)
