"""
AION Organizational Intelligence Index (OII) Scorer
12-dimension intelligence assessment + 3 proprietary AION metrics

Dimensions:
  1. knowledge_velocity     — rate of new knowledge creation
  2. knowledge_coverage     — breadth across domains
  3. knowledge_quality      — relevance + accuracy ratio
  4. learning_agility       — adaptation speed to new information
  5. collaboration_density  — cross-node knowledge exchange
  6. innovation_index       — novel idea generation rate
  7. decision_intelligence  — decision quality and speed
  8. cognitive_resilience   — resistance to knowledge loss
  9. knowledge_accessibility — ease of retrieval
 10. expertise_depth        — specialist depth per domain
 11. knowledge_retention    — long-term preservation
 12. adaptability_score     — org-wide change response

Proprietary:
  - Knowledge Half-Life     (T½ average across the org)
  - Knowledge Entropy       (H = -Σ p(i)log₂p(i))
  - Organizational Memory Compression
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OIIScore:
    # 12 OII Dimensions
    knowledge_velocity: float = 0.0
    knowledge_coverage: float = 0.0
    knowledge_quality: float = 0.0
    learning_agility: float = 0.0
    collaboration_density: float = 0.0
    innovation_index: float = 0.0
    decision_intelligence: float = 0.0
    cognitive_resilience: float = 0.0
    knowledge_accessibility: float = 0.0
    expertise_depth: float = 0.0
    knowledge_retention: float = 0.0
    adaptability_score: float = 0.0

    # Proprietary metrics
    knowledge_half_life: float = 0.0
    knowledge_entropy: float = 0.0
    memory_compression: float = 0.0

    # True once the org has at least one knowledge item to score against.
    # Without this, an org with zero uploaded data reads several "1 minus
    # bad_ratio" dimensions as a false 1.0 (nothing bad because nothing
    # exists at all) and looks confidently "healthy" before it has any
    # real basis to be.
    has_sufficient_data: bool = True

    # Computed composite
    overall: float = field(init=False)

    # Dimension weights (must sum to 1.0)
    _WEIGHTS = [
        0.08,  # knowledge_velocity
        0.07,  # knowledge_coverage
        0.10,  # knowledge_quality
        0.08,  # learning_agility
        0.09,  # collaboration_density
        0.08,  # innovation_index
        0.09,  # decision_intelligence
        0.12,  # cognitive_resilience (highest — central to AION)
        0.07,  # knowledge_accessibility
        0.07,  # expertise_depth
        0.08,  # knowledge_retention
        0.07,  # adaptability_score
    ]

    def __post_init__(self) -> None:
        dims = [
            self.knowledge_velocity, self.knowledge_coverage, self.knowledge_quality,
            self.learning_agility, self.collaboration_density, self.innovation_index,
            self.decision_intelligence, self.cognitive_resilience, self.knowledge_accessibility,
            self.expertise_depth, self.knowledge_retention, self.adaptability_score,
        ]
        self.overall = round(sum(d * w for d, w in zip(dims, self._WEIGHTS)), 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": self.overall,
            "knowledge_velocity": self.knowledge_velocity,
            "knowledge_coverage": self.knowledge_coverage,
            "knowledge_quality": self.knowledge_quality,
            "learning_agility": self.learning_agility,
            "collaboration_density": self.collaboration_density,
            "innovation_index": self.innovation_index,
            "decision_intelligence": self.decision_intelligence,
            "cognitive_resilience": self.cognitive_resilience,
            "knowledge_accessibility": self.knowledge_accessibility,
            "expertise_depth": self.expertise_depth,
            "knowledge_retention": self.knowledge_retention,
            "adaptability_score": self.adaptability_score,
            "knowledge_half_life": self.knowledge_half_life,
            "knowledge_entropy": self.knowledge_entropy,
            "memory_compression": self.memory_compression,
            "has_sufficient_data": self.has_sufficient_data,
        }


def compute_oii_score(raw_data: dict[str, Any]) -> OIIScore:
    """
    Compute all 12 OII dimensions + 3 proprietary metrics from raw org data.

    raw_data keys:
      - user_count: int
      - knowledge_health: dict (total, avg_relevance_score, health_ratio, outdated, isolated)
      - domain_distribution: list[dict] (domain, count)
      - active_disease_count: int
      - disease_severity_avg: float
      - graph_data: dict (persons, knowledge_nodes, collaboration_links, avg_knowledge_per_person)
    """
    health = raw_data.get("knowledge_health", {})
    domain_dist = raw_data.get("domain_distribution", [])
    user_count = max(raw_data.get("user_count", 1), 1)
    disease_count = raw_data.get("active_disease_count", 0)
    disease_severity = raw_data.get("disease_severity_avg", 0.0)
    graph = raw_data.get("graph_data", {})

    # `total` is the org's real knowledge-item count, unfloored — used to tell
    # "nothing bad happened because there's genuinely nothing yet" apart from
    # "nothing bad happened because everything is healthy". The dimensions
    # below are all "1 - bad_ratio" formulas, which read as a false, perfect
    # 1.0 when total is 0 (0 bad / 0 total) — misleading a brand-new org with
    # zero uploaded data into looking confidently "healthy".
    real_total = int(health.get("total", 0))
    has_data = real_total > 0
    total_items = max(real_total, 1)
    avg_relevance = float(health.get("avg_relevance_score", 0.5))
    health_ratio = float(health.get("health_ratio", 0.5))
    outdated = int(health.get("outdated", 0))
    isolated = int(health.get("isolated", 0))

    # ── 1. Knowledge Velocity: knowledge items per user (normalized) ──────────
    items_per_user = real_total / user_count
    knowledge_velocity = _clamp(items_per_user / 20.0)  # 20 items/user = perfect

    # ── 2. Knowledge Coverage: domain diversity ───────────────────────────────
    n_domains = max(len(domain_dist), 1)
    # Normalized vs. a target of 10 domains
    knowledge_coverage = _clamp(n_domains / 10.0) if has_data else 0.0

    # ── 3. Knowledge Quality: avg relevance × health ratio ────────────────────
    knowledge_quality = _clamp(avg_relevance * health_ratio)

    # ── 4. Learning Agility: inverse of outdated/stale ratio ─────────────────
    outdated_ratio = outdated / total_items
    learning_agility = _clamp(1.0 - outdated_ratio * 2) if has_data else 0.0

    # ── 5. Collaboration Density: graph connections per person ────────────────
    collab_links = int(graph.get("collaboration_links", 0) or graph.get("collaboration_count", 0))
    persons = max(int(graph.get("persons", 1) or graph.get("person_count", 1)), 1)
    # Target: 5 connections per person = good collaboration
    collaboration_density = _clamp(collab_links / (persons * 5))

    # ── 6. Innovation Index: inverse of disease impact + knowledge growth ─────
    disease_impact = disease_count * disease_severity / 5.0  # 5 diseases max
    innovation_index = _clamp(1.0 - disease_impact) if has_data else 0.0

    # ── 7. Decision Intelligence: ratio of non-conflicted knowledge ───────────
    conflicted = int(health.get("conflicted", 0))
    decision_intelligence = _clamp(1.0 - conflicted / total_items * 3) if has_data else 0.0

    # ── 8. Cognitive Resilience: multi-owner coverage ─────────────────────────
    # Use knowledge nodes / persons ratio as proxy for coverage
    knowledge_nodes = int(graph.get("knowledge_nodes", total_items))
    avg_k_per_person = float(
        graph.get("avg_knowledge_per_person", knowledge_nodes / persons)
    )
    cognitive_resilience = _clamp(avg_k_per_person / 10.0)  # 10 items/person = resilient

    # ── 9. Knowledge Accessibility: inverse isolation rate ───────────────────
    isolation_rate = isolated / total_items
    knowledge_accessibility = _clamp(1.0 - isolation_rate * 2) if has_data else 0.0

    # ── 10. Expertise Depth: avg items per domain ─────────────────────────────
    avg_per_domain = real_total / n_domains
    expertise_depth = _clamp(avg_per_domain / 50.0)  # 50 items/domain = deep expertise

    # ── 11. Knowledge Retention: overall health ratio ─────────────────────────
    knowledge_retention = _clamp(health_ratio) if has_data else 0.0

    # ── 12. Adaptability Score: composite of velocity + quality + resilience ──
    adaptability_score = _clamp(
        (knowledge_velocity + knowledge_quality + cognitive_resilience) / 3.0
    )

    # ── Proprietary Metrics ───────────────────────────────────────────────────

    # Knowledge Half-Life (average T½ proxy from domain volatility)
    # Derived from domain count: more domains = lower avg half-life
    # Typical T½ for a mixed-domain org: 180-365 days
    knowledge_half_life = max(30.0, 365.0 - (n_domains * 15)) if has_data else 0.0

    # Knowledge Entropy: Shannon entropy of domain distribution
    knowledge_entropy = _shannon_entropy(domain_dist)

    # Memory Compression: unique knowledge / total (higher = more unique)
    duplicated = int(health.get("duplicated", 0))
    memory_compression = _clamp(1.0 - duplicated / total_items) if has_data else 0.0

    return OIIScore(
        has_sufficient_data=has_data,
        knowledge_velocity=round(knowledge_velocity, 4),
        knowledge_coverage=round(knowledge_coverage, 4),
        knowledge_quality=round(knowledge_quality, 4),
        learning_agility=round(learning_agility, 4),
        collaboration_density=round(collaboration_density, 4),
        innovation_index=round(innovation_index, 4),
        decision_intelligence=round(decision_intelligence, 4),
        cognitive_resilience=round(cognitive_resilience, 4),
        knowledge_accessibility=round(knowledge_accessibility, 4),
        expertise_depth=round(expertise_depth, 4),
        knowledge_retention=round(knowledge_retention, 4),
        adaptability_score=round(adaptability_score, 4),
        knowledge_half_life=round(knowledge_half_life, 1),
        knowledge_entropy=round(knowledge_entropy, 4),
        memory_compression=round(memory_compression, 4),
    )


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _shannon_entropy(domain_distribution: list[dict]) -> float:
    """Compute Shannon entropy of domain distribution in bits."""
    total = sum(d.get("count", 0) for d in domain_distribution)
    if total == 0:
        return 0.0
    entropy = 0.0
    for d in domain_distribution:
        count = d.get("count", 0)
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy
