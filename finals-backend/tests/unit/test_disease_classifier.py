"""Unit tests for Organizational Disease Classifier (Module 5)."""
from __future__ import annotations

import pytest

from app.ai.algorithms.disease_classifier import (
    run_full_disease_scan,
    _severity_label,
)


class TestSeverityLabel:
    def test_critical_threshold(self):
        assert _severity_label(0.70) == "critical"
        assert _severity_label(0.90) == "critical"

    def test_warning_threshold(self):
        assert _severity_label(0.40) == "warning"
        assert _severity_label(0.69) == "warning"

    def test_healthy_threshold(self):
        assert _severity_label(0.39) == "healthy"
        assert _severity_label(0.0) == "healthy"


class TestFullDiseaseScan:
    def test_returns_five_diseases(self):
        """All 5 disease types should always be in the result."""
        result = run_full_disease_scan({
            "knowledge_health": {"total": 100, "duplicated": 10, "isolated": 5, "outdated": 15, "conflicted": 3},
            "user_count": 20,
            "domain_distribution": [
                {"domain": "engineering", "count": 80},
                {"domain": "sales", "count": 20},
            ],
            "graph_stats": {"person_count": 20, "collaboration_count": 40},
        })
        disease_types = {d["type"] for d in result["diseases"]}
        expected = {
            "knowledge_cancer",
            "memory_alzheimers",
            "communication_stroke",
            "knowledge_obesity",
            "innovation_paralysis",
        }
        assert disease_types == expected

    def test_scores_between_0_and_1(self):
        result = run_full_disease_scan({
            "knowledge_health": {"total": 100, "duplicated": 50, "isolated": 30},
            "user_count": 10,
            "domain_distribution": [],
            "graph_stats": {},
        })
        for d in result["diseases"]:
            assert 0.0 <= d["severity_score"] <= 1.0, f"Invalid score for {d['type']}"

    def test_high_duplication_triggers_cancer(self):
        """High duplication should produce high knowledge_cancer score."""
        result = run_full_disease_scan({
            "knowledge_health": {"total": 100, "duplicated": 80, "isolated": 0, "outdated": 0},
            "user_count": 50,
            "domain_distribution": [],
            "graph_stats": {},
        })
        cancer = next(d for d in result["diseases"] if d["type"] == "knowledge_cancer")
        assert cancer["severity_score"] > 0.3

    def test_healthy_org_low_scores(self):
        """A healthy org should have low disease scores."""
        result = run_full_disease_scan({
            "knowledge_health": {"total": 500, "duplicated": 2, "isolated": 1, "outdated": 5, "conflicted": 0},
            "user_count": 100,
            "domain_distribution": [{"domain": d, "count": 50} for d in range(10)],
            "graph_stats": {"person_count": 100, "collaboration_count": 300},
        })
        for d in result["diseases"]:
            assert d["severity"] in ("healthy", "warning"), f"{d['type']} should not be critical"

    def test_result_has_timestamp(self):
        result = run_full_disease_scan({"knowledge_health": {}, "user_count": 0, "domain_distribution": [], "graph_stats": {}})
        assert "scan_timestamp" in result or "diseases" in result
