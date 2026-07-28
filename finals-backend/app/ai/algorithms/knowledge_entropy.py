"""
AION Knowledge Entropy Algorithm
Original metric: H = -Σ p(i) × log₂(p(i))
Measures the degree of disorder, duplication, and inconsistency in the knowledge base.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Dict, List, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


def compute_knowledge_entropy(
    knowledge_distribution: Dict[str, int],
) -> float:
    """
    Compute Shannon entropy of knowledge distribution across domains.

    H = -Σ p(i) × log₂(p(i))

    Where p(i) = proportion of knowledge items in domain i.
    Higher entropy = more evenly distributed (healthy diversity).
    Lower entropy = concentrated in few domains (fragile).

    Returns: entropy value (bits)
    """
    total = sum(knowledge_distribution.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in knowledge_distribution.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return round(entropy, 4)


def compute_max_entropy(num_domains: int) -> float:
    """Maximum possible entropy for N domains (uniform distribution)."""
    if num_domains <= 1:
        return 0.0
    return math.log2(num_domains)


def compute_normalized_entropy(
    knowledge_distribution: Dict[str, int],
) -> float:
    """
    Normalized entropy: H / H_max ∈ [0, 1]
    1.0 = perfectly diverse, 0.0 = all knowledge in one domain
    """
    n = len(knowledge_distribution)
    if n <= 1:
        return 0.0
    h = compute_knowledge_entropy(knowledge_distribution)
    h_max = compute_max_entropy(n)
    return round(h / h_max, 4) if h_max > 0 else 0.0


def compute_duplication_entropy(
    similarity_matrix: List[Tuple[str, str, float]],
    threshold: float = 0.85,
) -> float:
    """
    Measure knowledge redundancy entropy.
    Higher value = more duplicated/overlapping knowledge.

    similarity_matrix: [(id_a, id_b, cosine_similarity), ...]
    """
    duplicate_pairs = [(a, b) for a, b, s in similarity_matrix if s >= threshold]
    n_duplicates = len(duplicate_pairs)
    n_total = len(similarity_matrix)

    if n_total == 0:
        return 0.0

    # Duplication ratio — what fraction of pairs are near-duplicates
    ratio = n_duplicates / n_total

    # Weight by average similarity of duplicates
    if duplicate_pairs:
        avg_sim = sum(s for _, _, s in similarity_matrix if s >= threshold) / n_duplicates
    else:
        avg_sim = 0.0

    return round(ratio * avg_sim, 4)


def compute_organizational_entropy_report(
    knowledge_items: List[Dict],
    similarity_matrix: Optional[List[Tuple[str, str, float]]] = None,
) -> Dict:
    """
    Full entropy report for an organization's knowledge base.

    knowledge_items: [{id, domain, dept_id, owner_count, is_isolated}]
    """
    # Domain distribution
    domain_counts: Dict[str, int] = Counter(
        item.get("domain", "unknown") for item in knowledge_items
    )

    # Department distribution
    dept_counts: Dict[str, int] = Counter(
        str(item.get("dept_id", "unassigned")) for item in knowledge_items
    )

    domain_entropy = compute_knowledge_entropy(domain_counts)
    dept_entropy = compute_knowledge_entropy(dept_counts)
    normalized_domain = compute_normalized_entropy(domain_counts)
    normalized_dept = compute_normalized_entropy(dept_counts)

    # Isolation metric
    isolated = sum(1 for item in knowledge_items if item.get("is_isolated", False))
    isolation_ratio = isolated / len(knowledge_items) if knowledge_items else 0.0

    # Ownership entropy
    ownership_counts: Dict[str, int] = Counter()
    for item in knowledge_items:
        owner_count = item.get("owner_count", 1)
        bucket = "1" if owner_count == 1 else ("2-3" if owner_count <= 3 else "4+")
        ownership_counts[bucket] += 1
    ownership_entropy = compute_knowledge_entropy(ownership_counts)

    # Duplication entropy
    duplication_entropy = 0.0
    if similarity_matrix:
        duplication_entropy = compute_duplication_entropy(similarity_matrix)

    # Composite organizational entropy score (lower = healthier)
    # High domain entropy is good (diverse), but high duplication entropy is bad
    composite_entropy = (
        (1 - normalized_domain) * 0.25 +    # penalize concentration
        duplication_entropy * 0.40 +          # penalize duplication
        isolation_ratio * 0.20 +              # penalize isolated knowledge
        (1 - normalized_dept) * 0.15          # penalize dept concentration
    )

    return {
        "domain_entropy_bits": domain_entropy,
        "department_entropy_bits": dept_entropy,
        "normalized_domain_entropy": normalized_domain,
        "normalized_department_entropy": normalized_dept,
        "duplication_entropy": duplication_entropy,
        "isolation_ratio": round(isolation_ratio, 4),
        "ownership_entropy_bits": ownership_entropy,
        "composite_entropy_score": round(composite_entropy, 4),  # 0-1, lower=healthier
        "health_interpretation": _interpret_entropy(composite_entropy),
        "domain_distribution": dict(domain_counts),
        "total_knowledge_items": len(knowledge_items),
        "isolated_items": isolated,
    }


def _interpret_entropy(score: float) -> str:
    if score < 0.2:
        return "Healthy — knowledge is diverse and well-distributed"
    elif score < 0.4:
        return "Moderate — some knowledge concentration detected"
    elif score < 0.6:
        return "Concerning — significant knowledge bottlenecks present"
    else:
        return "Critical — severe knowledge disorder requiring immediate attention"
