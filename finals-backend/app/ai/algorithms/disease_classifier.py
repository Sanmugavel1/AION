"""
AION Organizational Disease Detection Algorithms
5 diseases: Knowledge Cancer, Memory Alzheimer's, Communication Stroke,
Knowledge Obesity, Innovation Paralysis
"""
from __future__ import annotations

import statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

SEVERITY_THRESHOLDS = {
    "critical": 0.70,
    "warning": 0.40,
    "healthy": 0.0,
}


def _severity_label(score: float) -> str:
    if score >= SEVERITY_THRESHOLDS["critical"]:
        return "critical"
    elif score >= SEVERITY_THRESHOLDS["warning"]:
        return "warning"
    return "healthy"


def detect_knowledge_cancer(
    knowledge_items: List[Dict],
    similarity_pairs: List[Tuple[str, str, float]],
    duplicate_threshold: float = 0.85,
) -> Dict:
    """
    Knowledge Cancer: Duplicate SOPs, near-identical docs, version confusion.
    Score = weighted ratio of duplicate knowledge pairs.
    """
    total = len(knowledge_items)
    if total == 0:
        return _empty_disease("knowledge_cancer")

    duplicate_pairs = [(a, b, s) for a, b, s in similarity_pairs if s >= duplicate_threshold]
    near_duplicate_pairs = [(a, b, s) for a, b, s in similarity_pairs if 0.75 <= s < duplicate_threshold]

    # Score: proportion of docs involved in duplication
    involved_ids = set()
    for a, b, _ in duplicate_pairs:
        involved_ids.add(a)
        involved_ids.add(b)

    score = len(involved_ids) / total
    avg_similarity = (
        statistics.mean(s for _, _, s in duplicate_pairs) if duplicate_pairs else 0.0
    )

    # Weight by similarity
    weighted_score = score * (0.5 + avg_similarity * 0.5)

    days_until_critical = max(0, int((0.70 - weighted_score) / 0.005)) if weighted_score < 0.70 else 0

    return {
        "disease_type": "knowledge_cancer",
        "title": "Knowledge Cancer Detected",
        "severity": _severity_label(weighted_score),
        "severity_score": round(weighted_score * 100, 1),
        "confidence": min(0.95, 0.5 + len(duplicate_pairs) * 0.05),
        "description": (
            f"Found {len(duplicate_pairs)} duplicate knowledge pairs and "
            f"{len(near_duplicate_pairs)} near-duplicates. "
            f"{len(involved_ids)} documents ({round(score*100,1)}%) are affected."
        ),
        "evidence": {
            "duplicate_pairs_count": len(duplicate_pairs),
            "near_duplicate_pairs_count": len(near_duplicate_pairs),
            "affected_documents": len(involved_ids),
            "total_documents": total,
            "average_similarity": round(avg_similarity, 3),
        },
        "days_until_critical": days_until_critical,
        "recommended_action": "merge_docs",
    }


def detect_memory_alzheimers(
    employee_departures: List[Dict],
    knowledge_items: List[Dict],
    window_days: int = 90,
) -> Dict:
    """
    Memory Alzheimer's: Senior employees leaving with undocumented knowledge.
    Score = expertise_departure_rate × undocumented_ratio
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)

    recent_departures = [
        d for d in employee_departures
        if _parse_dt(d.get("departure_date")) > cutoff
    ]

    if not employee_departures:
        return {**_empty_disease("memory_alzheimers"), "severity": "healthy"}

    # High-criticality departures
    high_crit_departures = [
        d for d in recent_departures
        if d.get("knowledge_criticality_score", 0) >= 0.6
    ]

    # Undocumented knowledge
    undocumented = sum(
        1 for k in knowledge_items
        if not k.get("is_documented", True) or k.get("owner_count", 1) <= 1
    )
    undocumented_ratio = undocumented / max(len(knowledge_items), 1)

    departure_rate = len(high_crit_departures) / max(len(employee_departures), 1)
    score = departure_rate * 0.5 + undocumented_ratio * 0.5

    return {
        "disease_type": "memory_alzheimers",
        "title": "Memory Alzheimer's Detected",
        "severity": _severity_label(score),
        "severity_score": round(score * 100, 1),
        "confidence": min(0.90, 0.4 + len(recent_departures) * 0.1),
        "description": (
            f"{len(high_crit_departures)} high-criticality employees departed in {window_days} days. "
            f"{round(undocumented_ratio*100,1)}% of knowledge lacks documentation or shared ownership."
        ),
        "evidence": {
            "recent_departures": len(recent_departures),
            "high_criticality_departures": len(high_crit_departures),
            "undocumented_knowledge_ratio": round(undocumented_ratio, 3),
            "window_days": window_days,
        },
        "days_until_critical": None,
        "recommended_action": "assign_mentor",
    }


def detect_communication_stroke(
    collaboration_events: List[Dict],
    departments: List[Dict],
    window_days: int = 30,
) -> Dict:
    """
    Communication Stroke: Departments stop sharing information.
    Uses graph connectivity analysis — detect isolated department clusters.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)

    recent_events = [
        e for e in collaboration_events
        if _parse_dt(e.get("event_date")) > cutoff
    ]

    # Build cross-department communication graph
    dept_pairs: Dict[Tuple[str, str], int] = {}
    for event in recent_events:
        from_dept = event.get("from_dept_id", "")
        to_dept = event.get("to_dept_id", "")
        if from_dept and to_dept and from_dept != to_dept:
            pair = tuple(sorted([from_dept, to_dept]))
            dept_pairs[pair] = dept_pairs.get(pair, 0) + 1

    n_depts = len(departments)
    if n_depts < 2:
        return {**_empty_disease("communication_stroke"), "severity": "healthy"}

    max_possible_pairs = n_depts * (n_depts - 1) / 2
    active_pairs = len(dept_pairs)
    connectivity_ratio = active_pairs / max_possible_pairs

    # Isolated departments = those with zero cross-dept communication
    all_dept_ids = set(d["id"] for d in departments)
    communicating_depts = set()
    for from_dept, to_dept in [k for k in dept_pairs]:
        communicating_depts.add(from_dept)
        communicating_depts.add(to_dept)
    isolated_depts = all_dept_ids - communicating_depts

    isolation_ratio = len(isolated_depts) / n_depts
    score = (1 - connectivity_ratio) * 0.6 + isolation_ratio * 0.4

    return {
        "disease_type": "communication_stroke",
        "title": "Communication Stroke Detected",
        "severity": _severity_label(score),
        "severity_score": round(score * 100, 1),
        "confidence": 0.82,
        "description": (
            f"Only {active_pairs} of {int(max_possible_pairs)} possible department pairs are communicating. "
            f"{len(isolated_depts)} departments are completely isolated."
        ),
        "evidence": {
            "active_cross_dept_pairs": active_pairs,
            "max_possible_pairs": int(max_possible_pairs),
            "connectivity_ratio": round(connectivity_ratio, 3),
            "isolated_departments": list(isolated_depts),
            "window_days": window_days,
        },
        "days_until_critical": None,
        "recommended_action": "notify_managers",
    }


def detect_knowledge_obesity(
    knowledge_items: List[Dict],
    access_events: List[Dict],
    window_days: int = 90,
) -> Dict:
    """
    Knowledge Obesity: Too much accumulated info, nobody can find what they need.
    Score = (unused_ratio * age_factor) — heavy, bloated, inaccessible knowledge base.
    """
    total = len(knowledge_items)
    if total == 0:
        return _empty_disease("knowledge_obesity")

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)
    accessed_ids = set(
        e.get("knowledge_id") for e in access_events
        if _parse_dt(e.get("access_date")) > cutoff
    )

    unused_items = [k for k in knowledge_items if k.get("id") not in accessed_ids]
    unused_ratio = len(unused_items) / total

    # Average age of knowledge base
    ages = []
    for k in knowledge_items:
        created = _parse_dt(k.get("created_at"))
        if created > datetime.min.replace(tzinfo=timezone.utc):
            ages.append((now - created).days)
    avg_age_days = statistics.mean(ages) if ages else 0
    age_factor = min(1.0, avg_age_days / 365)

    score = unused_ratio * 0.6 + age_factor * 0.4

    return {
        "disease_type": "knowledge_obesity",
        "title": "Knowledge Obesity Detected",
        "severity": _severity_label(score),
        "severity_score": round(score * 100, 1),
        "confidence": 0.85,
        "description": (
            f"{len(unused_items)} of {total} knowledge items ({round(unused_ratio*100,1)}%) "
            f"were not accessed in {window_days} days. Average knowledge age: {round(avg_age_days)} days."
        ),
        "evidence": {
            "total_items": total,
            "unused_items": len(unused_items),
            "unused_ratio": round(unused_ratio, 3),
            "average_age_days": round(avg_age_days),
            "window_days": window_days,
        },
        "days_until_critical": None,
        "recommended_action": "archive_files",
    }


def detect_innovation_paralysis(
    ideas: List[Dict],
    projects: List[Dict],
    window_days: int = 180,
) -> Dict:
    """
    Innovation Paralysis: Same ideas repeated, no genuinely new solutions.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)

    recent_ideas = [
        i for i in ideas
        if _parse_dt(i.get("created_at")) > cutoff
    ]
    if not recent_ideas:
        return {**_empty_disease("innovation_paralysis"), "severity": "healthy"}

    # Unique concept velocity — ideas with low originality scores
    low_originality = [
        i for i in recent_ideas
        if i.get("originality_score", 0.5) < 0.4
    ]

    # New project types (experiment, r&d, pilot) vs total
    new_initiative_projects = [
        p for p in projects
        if _parse_dt(p.get("created_at")) > cutoff
        and p.get("type") in ("experiment", "r&d", "pilot", "innovation")
    ]

    repetition_ratio = len(low_originality) / max(len(recent_ideas), 1)
    new_initiative_ratio = len(new_initiative_projects) / max(len(projects), 1)

    score = repetition_ratio * 0.7 + (1 - new_initiative_ratio) * 0.3

    return {
        "disease_type": "innovation_paralysis",
        "title": "Innovation Paralysis Detected",
        "severity": _severity_label(score),
        "severity_score": round(score * 100, 1),
        "confidence": 0.75,
        "description": (
            f"{len(low_originality)} of {len(recent_ideas)} ideas show low originality. "
            f"Only {round(new_initiative_ratio*100,1)}% of projects are genuine new initiatives."
        ),
        "evidence": {
            "total_recent_ideas": len(recent_ideas),
            "low_originality_ideas": len(low_originality),
            "repetition_ratio": round(repetition_ratio, 3),
            "new_initiatives": len(new_initiative_projects),
            "window_days": window_days,
        },
        "days_until_critical": None,
        "recommended_action": "generate_onboarding",
    }


def run_full_disease_scan(
    knowledge_items: List[Dict],
    similarity_pairs: List[Tuple[str, str, float]],
    employee_departures: List[Dict],
    collaboration_events: List[Dict],
    departments: List[Dict],
    access_events: List[Dict],
    ideas: List[Dict],
    projects: List[Dict],
) -> Dict:
    """Run all 5 disease detections and return combined report."""
    cancer = detect_knowledge_cancer(knowledge_items, similarity_pairs)
    alzheimers = detect_memory_alzheimers(employee_departures, knowledge_items)
    stroke = detect_communication_stroke(collaboration_events, departments)
    obesity = detect_knowledge_obesity(knowledge_items, access_events)
    paralysis = detect_innovation_paralysis(ideas, projects)

    diseases = [cancer, alzheimers, stroke, obesity, paralysis]
    critical_count = sum(1 for d in diseases if d["severity"] == "critical")
    warning_count = sum(1 for d in diseases if d["severity"] == "warning")

    overall_score = statistics.mean(d["severity_score"] for d in diseases)

    # A scan with no real inputs anywhere returns all-"healthy" by construction
    # (nothing to detect), which reads as a confidently clean bill of health —
    # not "we haven't looked at anything yet". Surface that distinction.
    has_sufficient_data = bool(
        knowledge_items or employee_departures or collaboration_events or ideas or projects
    )

    return {
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_health_score": round(100 - overall_score, 1) if has_sufficient_data else 0.0,
        "has_sufficient_data": has_sufficient_data,
        "critical_diseases": critical_count,
        "warning_diseases": warning_count,
        "healthy_dimensions": (5 - critical_count - warning_count) if has_sufficient_data else 0,
        "diseases": {
            "knowledge_cancer": cancer,
            "memory_alzheimers": alzheimers,
            "communication_stroke": stroke,
            "knowledge_obesity": obesity,
            "innovation_paralysis": paralysis,
        },
    }


def _empty_disease(disease_type: str) -> Dict:
    return {
        "disease_type": disease_type,
        "title": f"{disease_type.replace('_', ' ').title()}",
        "severity": "healthy",
        "severity_score": 0.0,
        "confidence": 0.0,
        "description": "Insufficient data for detection",
        "evidence": {},
        "days_until_critical": None,
        "recommended_action": None,
    }


def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.min.replace(tzinfo=timezone.utc)
