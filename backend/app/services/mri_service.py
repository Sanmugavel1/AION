"""
AION Organizational MRI Service — The Signature Feature
Brain visualization, knowledge flow, bottlenecks, innovation centers
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import UUID

from app.ai.algorithms.knowledge_half_life import DOMAIN_VOLATILITY
from app.core.logging import get_logger
from app.repositories.graph_repository import GraphRepository

logger = get_logger(__name__)


class MRIService:
    """
    Generates the Organizational MRI — a color-coded brain health map.
    Shows organization as a living brain with real-time health status.

    Green = Healthy knowledge flow
    Yellow = Weakening collaboration
    Red = Critical bottlenecks or single-person dependencies
    """

    def __init__(self, graph_repo: GraphRepository) -> None:
        self._graph_repo = graph_repo

    async def get_brain_map(self, org_id: str) -> Dict:
        """Full brain map data for the organizational MRI visualization."""
        raw_graph = await self._graph_repo.get_org_brain_map(org_id)
        nodes = raw_graph.get("nodes", [])
        edges = raw_graph.get("edges", [])

        # Color-code nodes based on health indicators
        colored_nodes = [self._color_node(n) for n in nodes]
        # Weight edges by interaction strength
        weighted_edges = [self._weight_edge(e) for e in edges]

        # Compute summary stats
        red_count = sum(1 for n in colored_nodes if n["health_color"] == "red")
        yellow_count = sum(1 for n in colored_nodes if n["health_color"] == "yellow")
        green_count = sum(1 for n in colored_nodes if n["health_color"] == "green")

        return {
            "org_id": org_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "nodes": colored_nodes,
            "edges": weighted_edges,
            "summary": {
                "total_nodes": len(colored_nodes),
                "total_connections": len(weighted_edges),
                "green_nodes": green_count,
                "yellow_nodes": yellow_count,
                "red_nodes": red_count,
                "overall_health_color": "red" if red_count > len(colored_nodes) * 0.3
                    else "yellow" if yellow_count > len(colored_nodes) * 0.4
                    else "green",
            },
            "legend": {
                "green": "Healthy knowledge flow — multiple owners, frequently accessed",
                "yellow": "Weakening collaboration — low access or few connections",
                "red": "Critical — single owner, isolated, or never accessed",
            },
        }

    def _color_node(self, node: Dict) -> Dict:
        """Assign health color to each node based on its properties."""
        connections = node.get("connection_count", 0)
        node_type = node.get("type", "Knowledge")

        if node_type == "Person":
            color = "green" if connections >= 5 else "yellow" if connections >= 2 else "red"
        elif node_type == "Knowledge":
            color = "green" if connections >= 3 else "yellow" if connections >= 1 else "red"
        elif node_type == "Project":
            color = "green" if connections >= 3 else "yellow" if connections >= 1 else "red"
        else:
            color = "green"

        return {
            **node,
            "health_color": color,
            "health_score": min(100, connections * 20),
            "tooltip": self._node_tooltip(node, color),
        }

    def _weight_edge(self, edge: Dict) -> Dict:
        weight = edge.get("weight", 1)
        return {
            **edge,
            "display_weight": min(5.0, max(0.5, math.log(weight + 1))),
        }

    def _node_tooltip(self, node: Dict, color: str) -> str:
        messages = {
            "red": "⚠️ Critical: knowledge concentration risk",
            "yellow": "⚡ Caution: weakening knowledge connections",
            "green": "✅ Healthy: well-connected and resilient",
        }
        return f"{node.get('label', 'Unknown')}: {messages.get(color, '')}"

    async def get_knowledge_flow(self, org_id: str) -> List[Dict]:
        """Track how knowledge flows between people and departments."""
        comm_graph = await self._graph_repo.get_department_communication_graph(org_id)
        return [
            {
                "from_department": row.get("from_dept"),
                "to_department": row.get("to_dept"),
                "flow_strength": row.get("total_interactions", 0),
                "unique_contributors": row.get("from_people", 0),
                "health_status": (
                    "healthy" if row.get("total_interactions", 0) >= 10
                    else "warning" if row.get("total_interactions", 0) >= 3
                    else "critical"
                ),
            }
            for row in comm_graph
        ]

    async def get_knowledge_bottlenecks(self, org_id: str) -> List[Dict]:
        """Find single-person dependencies — critical bottleneck risk."""
        single_owner = await self._graph_repo.find_single_owner_critical_knowledge(org_id)
        return [
            {
                "knowledge_id": item.get("id"),
                "title": item.get("title"),
                "domain": item.get("domain"),
                "owner_ids": item.get("owner_ids", []),
                "risk_level": "critical",
                "recommendation": "Immediately assign additional knowledge custodians",
            }
            for item in single_owner
        ]

    async def get_innovation_centers(self, org_id: str) -> List[Dict]:
        """Find where new ideas and innovation cluster in the organization."""
        clusters = await self._graph_repo.find_knowledge_clusters(org_id)
        return [
            {
                "center_id": c.get("center_id"),
                "title": c.get("title"),
                "domain": c.get("domain"),
                "connection_strength": c.get("connection_count", 0),
                "related_concepts": len(c.get("related_ids", [])),
                "innovation_score": min(100, c.get("connection_count", 0) * 10),
                "color": "green",
            }
            for c in clusters
        ]

    async def get_knowledge_black_holes(self, org_id: str) -> List[Dict]:
        """Find knowledge black holes — info goes in but nothing comes out."""
        isolated = await self._graph_repo.find_isolated_knowledge(org_id)
        return [
            {
                "knowledge_id": item.get("id"),
                "title": item.get("title"),
                "domain": item.get("domain"),
                "created_at": item.get("created_at"),
                "risk": "Information is stored but never referenced or shared",
                "color": "red",
            }
            for item in isolated
        ]

    async def get_timeline_forecast(
        self,
        org_id: str,
        db=None,
    ) -> Dict:
        """
        3, 6, 12 month forecast of organizational brain health.

        Real extrapolation from the current knowledge base: a weighted-average
        decay constant (lambda, same DOMAIN_VOLATILITY model as the per-item
        Knowledge Half-Life algorithm) is computed from the org's actual
        domain distribution, then projected forward exponentially against the
        current OII health score. This is a decay-rate extrapolation from a
        single current snapshot, NOT a fitted historical trend — the org only
        has one weekly OII snapshot so far, so confidence is deliberately
        modest and stated as such rather than invented.
        """
        now = datetime.now(timezone.utc)

        if db is None:
            # No DB session available (shouldn't happen via the API route) —
            # honest empty result rather than fabricated numbers.
            return {
                "forecast_generated_at": now.isoformat(),
                "org_id": org_id,
                "note": "Forecast requires knowledge-base and OII data; none available.",
                "3_month_forecast": None,
                "6_month_forecast": None,
                "12_month_forecast": None,
            }

        from app.api.v1.endpoints.intelligence_index import _compute_live_oii
        from app.repositories.knowledge_repository import KnowledgeRepository
        from app.services.intelligence_index_service import IntelligenceIndexService

        k_repo = KnowledgeRepository(db)
        intel_service = IntelligenceIndexService(db)

        domain_distribution = await k_repo.get_domain_distribution(UUID(org_id))
        health_summary = await k_repo.get_health_summary(UUID(org_id))

        oii = await intel_service.get_latest_oii(UUID(org_id))
        if not oii:
            oii = await _compute_live_oii(intel_service, db, org_id)
        current_health_pct = round((oii.get("overall_health") or 0.0) * 100, 1)

        total_items = sum(d["count"] for d in domain_distribution) or 1
        weighted_lambda = sum(
            DOMAIN_VOLATILITY.get(d["domain"].lower(), DOMAIN_VOLATILITY["general"]) * d["count"]
            for d in domain_distribution
        ) / total_items

        top_domains = [d["domain"] for d in sorted(domain_distribution, key=lambda d: -d["count"])[:2]]
        isolated_count = health_summary.get("isolated", 0)
        outdated_count = health_summary.get("outdated", 0)

        def _project(days: int) -> dict:
            # Exponential decay of current health under the weighted lambda —
            # the same model used per-item, applied at the org level.
            retained_fraction = math.exp(-weighted_lambda * days)
            points_lost = round(current_health_pct * (1 - retained_fraction), 1)
            # Confidence decays with horizon length and is capped modestly
            # since it's extrapolated from a single snapshot, not a trend.
            confidence = round(max(0.35, 0.6 - (days / 365) * 0.25), 2)
            return {
                "date": (now + timedelta(days=days)).strftime("%Y-%m"),
                "projected_health_change": f"-{max(0.0, points_lost - 2):.0f} to -{points_lost + 2:.0f} points without intervention",
                "critical_risks": [
                    f"Continued decay in the {top_domains[0]} domain" if top_domains else "Knowledge decay across the organization",
                    f"{isolated_count} isolated knowledge items at risk of becoming permanently unused" if isolated_count else "Low isolated-item risk currently",
                ],
                "required_actions": [
                    f"Update {outdated_count} outdated document(s)" if outdated_count else "Maintain current documentation cadence",
                    "Run a fresh disease scan and act on any critical findings",
                ],
                "confidence": confidence,
            }

        return {
            "forecast_generated_at": now.isoformat(),
            "org_id": org_id,
            "methodology": (
                "Extrapolated from the current domain-weighted knowledge decay rate "
                "(same model as the per-item Knowledge Half-Life algorithm) applied to "
                "the current OII health score. Confidence is intentionally conservative "
                "because this org has only one historical OII snapshot — accuracy will "
                "improve as more weekly snapshots accumulate."
            ),
            "current_health_pct": current_health_pct,
            "3_month_forecast": _project(90),
            "6_month_forecast": _project(180),
            "12_month_forecast": _project(365),
        }
