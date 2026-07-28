"""
AION Knowledge Half-Life Algorithm
Original metric: T½ = ln(2) / λ
where λ = relevance decay constant derived from access patterns and domain volatility
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

# Domain volatility constants — how quickly knowledge in each domain becomes obsolete
DOMAIN_VOLATILITY: Dict[str, float] = {
    "technology": 0.025,    # ~28 days half-life baseline
    "security": 0.030,      # ~23 days — high volatility
    "compliance": 0.015,    # ~46 days
    "marketing": 0.020,     # ~35 days
    "sales": 0.018,         # ~39 days
    "operations": 0.010,    # ~69 days
    "hr": 0.008,            # ~87 days
    "finance": 0.007,       # ~99 days
    "strategy": 0.005,      # ~139 days
    "culture": 0.003,       # ~231 days — low volatility
    "general": 0.012,       # ~58 days
}


def compute_lambda(
    domain: str,
    access_frequency_per_week: float,
    last_updated_days_ago: float,
    is_documented: bool,
    owner_count: int,
) -> float:
    """
    Compute the decay constant λ for a knowledge item.

    λ = base_volatility × access_penalty × documentation_bonus × owner_penalty

    Higher λ → faster decay → shorter half-life.
    """
    base = DOMAIN_VOLATILITY.get(domain.lower(), DOMAIN_VOLATILITY["general"])

    # Access penalty: rarely accessed knowledge decays faster
    # Normalize: 0 accesses/week = 1.5x penalty, 5+/week = 0.5x
    access_penalty = max(0.5, 1.5 - (access_frequency_per_week * 0.2))

    # Documentation bonus: well-documented knowledge decays slower
    doc_bonus = 0.8 if is_documented else 1.2

    # Owner penalty: single-owner knowledge is at risk
    owner_penalty = 1.5 if owner_count <= 1 else max(0.7, 1.0 - (owner_count - 1) * 0.1)

    # Staleness multiplier: knowledge not updated recently decays faster
    staleness = 1.0 + min(last_updated_days_ago / 365, 1.0)

    lam = base * access_penalty * doc_bonus * owner_penalty * staleness
    return max(0.001, lam)  # floor to prevent infinite half-life


def compute_knowledge_half_life(
    domain: str,
    access_frequency_per_week: float = 1.0,
    last_updated_days_ago: float = 30.0,
    is_documented: bool = True,
    owner_count: int = 1,
) -> float:
    """
    Compute the half-life of a knowledge item in days.
    T½ = ln(2) / λ
    """
    lam = compute_lambda(
        domain=domain,
        access_frequency_per_week=access_frequency_per_week,
        last_updated_days_ago=last_updated_days_ago,
        is_documented=is_documented,
        owner_count=owner_count,
    )
    half_life = math.log(2) / lam
    logger.debug(
        f"Knowledge half-life computed",
        domain=domain, lambda_=lam, half_life_days=round(half_life, 1)
    )
    return round(half_life, 2)


def compute_current_relevance(
    half_life_days: float,
    days_since_last_access: float,
    initial_relevance: float = 1.0,
) -> float:
    """
    Compute current relevance using exponential decay.
    R(t) = R₀ × 2^(-t / T½)
    """
    if half_life_days <= 0:
        return 0.0
    relevance = initial_relevance * math.pow(2, -days_since_last_access / half_life_days)
    return max(0.0, min(1.0, round(relevance, 4)))


def compute_days_until_critical(
    half_life_days: float,
    current_relevance: float,
    critical_threshold: float = 0.25,
) -> Optional[float]:
    """
    How many more days until relevance drops below critical_threshold?
    t = T½ × log2(R₀ / R_critical)
    """
    if current_relevance <= critical_threshold:
        return 0.0
    if half_life_days <= 0:
        return None
    days = half_life_days * math.log2(current_relevance / critical_threshold)
    return max(0.0, round(days, 1))


def batch_compute_half_lives(
    knowledge_items: List[Dict],
) -> List[Dict]:
    """
    Compute half-lives for a batch of knowledge items.
    Each item: {id, domain, access_freq_per_week, last_updated_days_ago, is_documented, owner_count}
    """
    results = []
    for item in knowledge_items:
        hl = compute_knowledge_half_life(
            domain=item.get("domain", "general"),
            access_frequency_per_week=item.get("access_freq_per_week", 1.0),
            last_updated_days_ago=item.get("last_updated_days_ago", 30.0),
            is_documented=item.get("is_documented", True),
            owner_count=item.get("owner_count", 1),
        )
        relevance = compute_current_relevance(
            half_life_days=hl,
            days_since_last_access=item.get("days_since_last_access", 0.0),
        )
        days_critical = compute_days_until_critical(hl, relevance)
        results.append({
            "id": item["id"],
            "half_life_days": hl,
            "current_relevance": relevance,
            "days_until_critical": days_critical,
            "decay_rate": compute_lambda(
                item.get("domain", "general"),
                item.get("access_freq_per_week", 1.0),
                item.get("last_updated_days_ago", 30.0),
                item.get("is_documented", True),
                item.get("owner_count", 1),
            ),
        })
    return results
