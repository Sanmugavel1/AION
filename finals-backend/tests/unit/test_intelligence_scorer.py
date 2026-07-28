"""Unit tests for the Organizational Intelligence Index scorer (Module 9)."""
from __future__ import annotations

import pytest

from app.ai.algorithms.intelligence_scorer import OIIScore, compute_oii_score


class TestOIIScore:
    def test_overall_between_0_and_1(self):
        raw = {
            "user_count": 50,
            "knowledge_health": {"total": 200, "avg_relevance_score": 0.75, "health_ratio": 0.85},
            "domain_distribution": [{"domain": "eng", "count": 100}, {"domain": "sales", "count": 100}],
            "active_disease_count": 1,
            "disease_severity_avg": 0.3,
            "graph_data": {"persons": 50, "knowledge_nodes": 200, "collaboration_links": 150},
        }
        oii = compute_oii_score(raw)
        assert 0.0 <= oii.overall <= 1.0

    def test_all_12_dimensions_present(self):
        raw = {
            "user_count": 10,
            "knowledge_health": {"total": 50, "avg_relevance_score": 0.5, "health_ratio": 0.7},
            "domain_distribution": [],
            "active_disease_count": 0,
            "disease_severity_avg": 0.0,
            "graph_data": {},
        }
        oii = compute_oii_score(raw)
        required = [
            "knowledge_velocity", "knowledge_coverage", "knowledge_quality",
            "learning_agility", "collaboration_density", "innovation_index",
            "decision_intelligence", "cognitive_resilience", "knowledge_accessibility",
            "expertise_depth", "knowledge_retention", "adaptability_score",
        ]
        for dim in required:
            val = getattr(oii, dim, None)
            assert val is not None, f"Missing dimension: {dim}"
            assert 0.0 <= val <= 1.0, f"Dimension {dim} out of range: {val}"

    def test_proprietary_metrics_present(self):
        raw = {"user_count": 5, "knowledge_health": {}, "domain_distribution": [], "active_disease_count": 0, "disease_severity_avg": 0, "graph_data": {}}
        oii = compute_oii_score(raw)
        assert hasattr(oii, "knowledge_half_life")
        assert hasattr(oii, "knowledge_entropy")
        assert hasattr(oii, "memory_compression")

    def test_many_diseases_lower_oii(self):
        healthy_raw = {
            "user_count": 100,
            "knowledge_health": {"total": 500, "avg_relevance_score": 0.9, "health_ratio": 0.95},
            "domain_distribution": [],
            "active_disease_count": 0,
            "disease_severity_avg": 0.0,
            "graph_data": {"persons": 100, "collaboration_links": 400},
        }
        sick_raw = {
            **healthy_raw,
            "active_disease_count": 5,
            "disease_severity_avg": 0.75,
        }
        healthy_oii = compute_oii_score(healthy_raw)
        sick_oii = compute_oii_score(sick_raw)
        assert healthy_oii.overall > sick_oii.overall
