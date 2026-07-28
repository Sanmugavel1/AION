"""
AION Cognitive Resilience Score (CRS)
Original metric: Organization's ability to absorb loss of key personnel
CRS = 1 - (weighted_single_person_dependencies / total_critical_knowledge_weight)
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


def compute_cognitive_resilience_score(
    knowledge_items: List[Dict],
    employee_profiles: List[Dict],
) -> Dict:
    """
    Compute Cognitive Resilience Score for an organization.

    CRS = 1 - (Σ w_i × single_owner_indicator_i) / Σ w_i
    where w_i = criticality weight of knowledge item i

    Score: 0 = completely fragile, 1 = fully resilient

    knowledge_items: [{id, criticality, owner_count, domain, is_documented}]
    employee_profiles: [{user_id, knowledge_criticality_score, replacement_difficulty_score}]
    """
    if not knowledge_items:
        return _empty_crs_result()

    total_weight = 0.0
    single_owner_weight = 0.0
    undocumented_weight = 0.0
    critical_bottlenecks = []

    for item in knowledge_items:
        criticality = item.get("criticality", 0.5)
        owner_count = item.get("owner_count", 1)
        is_documented = item.get("is_documented", True)

        # Weight = criticality of this knowledge
        weight = criticality
        total_weight += weight

        if owner_count <= 1:
            single_owner_weight += weight
            if criticality >= 0.7:
                critical_bottlenecks.append({
                    "id": item["id"],
                    "domain": item.get("domain", "unknown"),
                    "criticality": criticality,
                    "risk_level": "critical" if criticality >= 0.9 else "high",
                })

        if not is_documented:
            undocumented_weight += weight

    if total_weight == 0:
        return _empty_crs_result()

    # Base CRS from single-owner dependency
    base_crs = 1.0 - (single_owner_weight / total_weight)

    # Documentation penalty: undocumented knowledge reduces resilience
    doc_ratio = 1.0 - (undocumented_weight / total_weight)
    documentation_factor = 0.7 + 0.3 * doc_ratio  # 70-100% weight

    # Expert dependency from employee profiles
    high_dependency_employees = [
        p for p in employee_profiles
        if p.get("replacement_difficulty_score", 0) >= 0.75
    ]
    expert_dependency_ratio = (
        len(high_dependency_employees) / max(len(employee_profiles), 1)
    )
    expert_factor = 1.0 - (expert_dependency_ratio * 0.3)  # up to 30% penalty

    crs = base_crs * documentation_factor * expert_factor
    crs = max(0.0, min(1.0, crs))

    return {
        "cognitive_resilience_score": round(crs, 4),
        "score_percentage": round(crs * 100, 1),
        "interpretation": _interpret_crs(crs),
        "single_owner_knowledge_ratio": round(single_owner_weight / total_weight, 4),
        "documentation_coverage": round(doc_ratio, 4),
        "expert_dependency_ratio": round(expert_dependency_ratio, 4),
        "critical_bottlenecks": critical_bottlenecks[:20],  # top 20
        "total_knowledge_items": len(knowledge_items),
        "high_risk_employees": len(high_dependency_employees),
        "recommendations": _generate_crs_recommendations(crs, critical_bottlenecks, high_dependency_employees),
    }


def compute_knowledge_redundancy_index(
    knowledge_items: List[Dict],
) -> float:
    """
    KRI = average number of owners per knowledge item (weighted by criticality)
    Higher = more resilient
    """
    if not knowledge_items:
        return 0.0

    weighted_sum = sum(
        item.get("owner_count", 1) * item.get("criticality", 0.5)
        for item in knowledge_items
    )
    total_weight = sum(item.get("criticality", 0.5) for item in knowledge_items)

    return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0


def compute_knowledge_bus_factor(
    employee_knowledge_map: Dict[str, List[str]],
    critical_knowledge_ids: List[str],
) -> int:
    """
    Bus factor: minimum number of people who must leave to cause critical knowledge loss.
    Classic metric extended with criticality weighting.

    employee_knowledge_map: {employee_id: [knowledge_id, ...]}
    critical_knowledge_ids: knowledge items that must be covered
    """
    if not critical_knowledge_ids:
        return len(employee_knowledge_map)

    # Greedy set cover to find minimum critical employees
    covered = set()
    removed_count = 0
    remaining = dict(employee_knowledge_map)

    target = set(critical_knowledge_ids)

    while covered < target and remaining:
        # Find employee with most critical coverage
        best_emp = max(
            remaining,
            key=lambda e: len(set(remaining[e]) & (target - covered))
        )
        new_coverage = set(remaining[best_emp]) & (target - covered)
        if not new_coverage:
            break
        covered |= new_coverage
        del remaining[best_emp]
        removed_count += 1

    return removed_count


def _interpret_crs(score: float) -> str:
    if score >= 0.85:
        return "Excellent — organization can absorb significant personnel changes without disruption"
    elif score >= 0.70:
        return "Good — moderate resilience with some knowledge concentration risks"
    elif score >= 0.55:
        return "Fair — notable single-person dependencies requiring attention"
    elif score >= 0.40:
        return "Poor — significant fragility; key departures would cause operational disruption"
    else:
        return "Critical — organization is highly dependent on a few individuals; immediate action required"


def _generate_crs_recommendations(
    score: float,
    bottlenecks: List[Dict],
    high_risk_employees: List[Dict],
) -> List[str]:
    recs = []
    if score < 0.85:
        if bottlenecks:
            recs.append(
                f"Document and redistribute knowledge for {len(bottlenecks)} critical single-owner items"
            )
        if high_risk_employees:
            recs.append(
                f"Initiate knowledge transfer plans for {len(high_risk_employees)} high-dependency employees"
            )
        if score < 0.55:
            recs.append("Implement mandatory pair-programming / knowledge-pairing protocols")
            recs.append("Establish cross-training sessions within the next 30 days")
        if score < 0.40:
            recs.append("URGENT: Activate OCSIE emergency backup protocols for critical employees")
    return recs


def _empty_crs_result() -> Dict:
    return {
        "cognitive_resilience_score": 0.0,
        "score_percentage": 0.0,
        "interpretation": "Insufficient data",
        "single_owner_knowledge_ratio": 0.0,
        "documentation_coverage": 0.0,
        "expert_dependency_ratio": 0.0,
        "critical_bottlenecks": [],
        "total_knowledge_items": 0,
        "high_risk_employees": 0,
        "recommendations": [],
    }
