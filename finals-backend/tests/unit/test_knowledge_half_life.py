"""Unit tests for Knowledge Half-Life algorithm (Module 4)."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

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
        """Technology domains should decay faster than legal/compliance."""
        assert DOMAIN_VOLATILITY.get("technology", 0) > DOMAIN_VOLATILITY.get("legal", 1)

    def test_general_domain_exists(self):
        assert "general" in DOMAIN_VOLATILITY


class TestComputeKnowledgeHalfLife:
    def test_returns_required_fields(self):
        result = compute_knowledge_half_life(
            domain="engineering",
            last_accessed_at=datetime.now(timezone.utc) - timedelta(days=10),
            access_count=5,
        )
        assert "half_life_days" in result
        assert "lambda" in result
        assert result["half_life_days"] > 0

    def test_documented_extends_half_life(self):
        base = compute_knowledge_half_life(
            domain="engineering",
            last_accessed_at=datetime.now(timezone.utc) - timedelta(days=30),
            access_count=1,
            is_documented=False,
        )
        documented = compute_knowledge_half_life(
            domain="engineering",
            last_accessed_at=datetime.now(timezone.utc) - timedelta(days=30),
            access_count=1,
            is_documented=True,
        )
        assert documented["half_life_days"] >= base["half_life_days"]

    def test_multiple_owners_extends_half_life(self):
        single = compute_knowledge_half_life(
            domain="engineering",
            last_accessed_at=datetime.now(timezone.utc) - timedelta(days=30),
            access_count=1,
            owner_count=1,
        )
        multi = compute_knowledge_half_life(
            domain="engineering",
            last_accessed_at=datetime.now(timezone.utc) - timedelta(days=30),
            access_count=1,
            owner_count=5,
        )
        assert multi["half_life_days"] >= single["half_life_days"]

    def test_unknown_domain_uses_default(self):
        result = compute_knowledge_half_life(
            domain="unknown_domain_xyz",
            last_accessed_at=datetime.now(timezone.utc),
            access_count=1,
        )
        assert result["half_life_days"] > 0


class TestComputeCurrentRelevance:
    def test_new_knowledge_is_fully_relevant(self):
        r = compute_current_relevance(r0=1.0, half_life_days=30, days_elapsed=0)
        assert r == pytest.approx(1.0)

    def test_at_half_life_relevance_is_half(self):
        hl = 30
        r = compute_current_relevance(r0=1.0, half_life_days=hl, days_elapsed=hl)
        assert r == pytest.approx(0.5, abs=0.01)

    def test_relevance_never_below_zero(self):
        r = compute_current_relevance(r0=1.0, half_life_days=10, days_elapsed=10000)
        assert r >= 0

    def test_relevance_decreases_over_time(self):
        r1 = compute_current_relevance(r0=1.0, half_life_days=30, days_elapsed=10)
        r2 = compute_current_relevance(r0=1.0, half_life_days=30, days_elapsed=60)
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
