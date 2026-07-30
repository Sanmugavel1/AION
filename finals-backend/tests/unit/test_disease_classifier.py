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


def _empty_scan_kwargs(**overrides):
    kwargs = dict(
        knowledge_items=[],
        similarity_pairs=[],
        employee_departures=[],
        collaboration_events=[],
        departments=[],
        access_events=[],
        ideas=[],
        projects=[],
    )
    kwargs.update(overrides)
    return kwargs


class TestFullDiseaseScan:
    def test_returns_five_diseases(self):
        """All 5 disease types should always be in the result."""
        result = run_full_disease_scan(**_empty_scan_kwargs(
            knowledge_items=[{"id": f"k{i}"} for i in range(100)],
        ))
        expected = {
            "knowledge_cancer",
            "memory_alzheimers",
            "communication_stroke",
            "knowledge_obesity",
            "innovation_paralysis",
        }
        assert set(result["diseases"].keys()) == expected

    def test_scores_between_0_and_100(self):
        result = run_full_disease_scan(**_empty_scan_kwargs(
            knowledge_items=[{"id": f"k{i}"} for i in range(100)],
            similarity_pairs=[(f"k{i}", f"k{i+1}", 0.9) for i in range(50)],
        ))
        for d in result["diseases"].values():
            assert 0.0 <= d["severity_score"] <= 100.0, f"Invalid score for {d['disease_type']}"

    def test_high_duplication_triggers_cancer(self):
        """High duplication should produce a high knowledge_cancer score."""
        knowledge_items = [{"id": f"k{i}"} for i in range(100)]
        # 80 distinct documents paired up into 40 near-duplicate pairs, all above
        # the 0.85 duplicate_threshold.
        similarity_pairs = [(f"k{i}", f"k{i+1}", 0.95) for i in range(0, 80, 2)]
        result = run_full_disease_scan(**_empty_scan_kwargs(
            knowledge_items=knowledge_items,
            similarity_pairs=similarity_pairs,
        ))
        cancer = result["diseases"]["knowledge_cancer"]
        assert cancer["severity_score"] > 30.0

    def test_healthy_org_low_scores(self):
        """A healthy org with minimal duplication/turnover should not read as critical."""
        result = run_full_disease_scan(**_empty_scan_kwargs(
            knowledge_items=[{"id": f"k{i}"} for i in range(500)],
        ))
        for d in result["diseases"].values():
            assert d["severity"] in ("healthy", "warning"), f"{d['disease_type']} should not be critical"

    def test_result_has_timestamp(self):
        result = run_full_disease_scan(**_empty_scan_kwargs())
        assert "scan_timestamp" in result
        assert "diseases" in result

    def test_empty_input_has_insufficient_data(self):
        result = run_full_disease_scan(**_empty_scan_kwargs())
        assert result["has_sufficient_data"] is False
