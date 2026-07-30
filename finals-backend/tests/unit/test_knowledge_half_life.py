"""Unit tests for Knowledge Half-Life algorithm (Module 4)."""
from __future__ import annotations

import pytest

from app.ai.algorithms.knowledge_half_life import (
    DOMAIN_VOLATILITY,
    compute_current_relevance,
    compute_days_until_critical,
    compute_knowledge_half_life,
)


class TestDomainVolatility:
    def test_all_domains_have_valid_lambda(self):
        for domain, λ in DOMAIN_VOLATILITY.items():
            assert 0 < λ <= 1.0, f"Domain {domain} has invalid λ={λ}"

    def test_high_volatility_domains(self):
        """Technology should decay faster (higher λ) than low-volatility culture knowledge."""
        assert DOMAIN_VOLATILITY["technology"] > DOMAIN_VOLATILITY["culture"]

    def test_general_domain_exists(self):
        assert "general" in DOMAIN_VOLATILITY


class TestComputeKnowledgeHalfLife:
    def test_returns_positive_half_life(self):
        half_life = compute_knowledge_half_life(
            domain="engineering",
            access_frequency_per_week=2.0,
            last_updated_days_ago=10,
        )
        assert half_life > 0

    def test_documented_extends_half_life(self):
        base = compute_knowledge_half_life(
            domain="engineering",
            last_updated_days_ago=30,
            is_documented=False,
        )
        documented = compute_knowledge_half_life(
            domain="engineering",
            last_updated_days_ago=30,
            is_documented=True,
        )
        assert documented >= base

    def test_multiple_owners_extends_half_life(self):
        single = compute_knowledge_half_life(
            domain="engineering",
            last_updated_days_ago=30,
            owner_count=1,
        )
        multi = compute_knowledge_half_life(
            domain="engineering",
            last_updated_days_ago=30,
            owner_count=5,
        )
        assert multi >= single

    def test_unknown_domain_uses_default(self):
        result = compute_knowledge_half_life(domain="unknown_domain_xyz")
        assert result > 0


class TestComputeCurrentRelevance:
    def test_new_knowledge_is_fully_relevant(self):
        r = compute_current_relevance(half_life_days=30, days_since_last_access=0)
        assert r == pytest.approx(1.0)

    def test_at_half_life_relevance_is_half(self):
        hl = 30
        r = compute_current_relevance(half_life_days=hl, days_since_last_access=hl)
        assert r == pytest.approx(0.5, abs=0.01)

    def test_relevance_never_below_zero(self):
        r = compute_current_relevance(half_life_days=10, days_since_last_access=10000)
        assert r >= 0

    def test_relevance_decreases_over_time(self):
        r1 = compute_current_relevance(half_life_days=30, days_since_last_access=10)
        r2 = compute_current_relevance(half_life_days=30, days_since_last_access=60)
        assert r1 > r2


class TestDaysUntilCritical:
    def test_already_critical_returns_zero(self):
        days = compute_days_until_critical(
            half_life_days=30, current_relevance=0.1, critical_threshold=0.2
        )
        assert days == 0

    def test_returns_positive_days(self):
        days = compute_days_until_critical(
            half_life_days=30, current_relevance=0.9, critical_threshold=0.2
        )
        assert days > 0

    def test_shorter_half_life_reaches_critical_sooner(self):
        days_short = compute_days_until_critical(
            half_life_days=10, current_relevance=0.8, critical_threshold=0.2
        )
        days_long = compute_days_until_critical(
            half_life_days=100, current_relevance=0.8, critical_threshold=0.2
        )
        assert days_short < days_long
