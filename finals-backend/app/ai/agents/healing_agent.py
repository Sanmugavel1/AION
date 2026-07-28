"""
AION Self-Healing AI Agent — LangGraph
Automatically recommends recovery actions; human approval required
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from app.ai.agents import _compat  # noqa: F401  (neutralizes langchain_core's legacy debug shim)
from langgraph.graph import END, StateGraph

from app.core.logging import get_logger

logger = get_logger(__name__)

ACTION_TEMPLATES = {
    "create_sop": {
        "title_template": "Create SOP for {domain} processes",
        "description_template": (
            "Detected knowledge gap in {domain}. Create a Standard Operating Procedure "
            "to document {count} undocumented processes identified in the knowledge graph."
        ),
        "priority": "high",
    },
    "assign_mentor": {
        "title_template": "Assign mentor for {target_name}",
        "description_template": (
            "Employee {target_name} is a critical knowledge holder with replacement difficulty "
            "score of {score:.0%}. Assign a mentee to shadow and learn key processes before departure risk."
        ),
        "priority": "critical",
    },
    "schedule_training": {
        "title_template": "Schedule training for {skill_gap}",
        "description_template": (
            "Knowledge gap analysis identified missing expertise in {skill_gap} across "
            "{team_count} team members. Schedule targeted training sessions."
        ),
        "priority": "medium",
    },
    "merge_docs": {
        "title_template": "Merge {count} duplicate documents in {domain}",
        "description_template": (
            "Knowledge Cancer detected: {count} near-duplicate documents found in {domain} "
            "domain with similarity above {threshold:.0%}. Merge to create single source of truth."
        ),
        "priority": "high",
    },
    "archive_files": {
        "title_template": "Archive {count} stale knowledge items",
        "description_template": (
            "Knowledge Obesity detected: {count} documents not accessed in {days} days. "
            "Archive to reduce cognitive load while preserving institutional memory."
        ),
        "priority": "medium",
    },
    "notify_managers": {
        "title_template": "Alert: {disease_type} reaching critical level",
        "description_template": (
            "{disease_type} has reached severity score {score:.0%}. "
            "Leadership intervention required within {days_until_critical} days."
        ),
        "priority": "critical",
    },
    "generate_onboarding": {
        "title_template": "Generate onboarding material for {role}",
        "description_template": (
            "AI-generated onboarding package for {role} role using {source_name}'s knowledge profile. "
            "Package includes key documents, contacts, and first-week learning roadmap."
        ),
        "priority": "high",
    },
    "create_quiz": {
        "title_template": "Create knowledge retention quiz for {domain}",
        "description_template": (
            "Knowledge decay detected in {domain}. Create quiz to assess and reinforce "
            "team retention of {count} key concepts."
        ),
        "priority": "low",
    },
    "update_wiki": {
        "title_template": "Update wiki for {section}",
        "description_template": (
            "Wiki section '{section}' is {days_stale} days stale. "
            "AI has detected {update_count} factual discrepancies with current system state."
        ),
        "priority": "medium",
    },
    "knowledge_transfer": {
        "title_template": "Initiate knowledge transfer: {from_name} → {to_name}",
        "description_template": (
            "OCSIE triggered: {from_name} departure initiates structured knowledge transfer "
            "to {to_name}. Estimated transfer time: {weeks} weeks."
        ),
        "priority": "critical",
    },
}


class HealingState(TypedDict):
    org_id: str
    disease_reports: List[Dict]
    decay_report: Dict
    ocsie_alerts: List[Dict]
    generated_recommendations: List[Dict]
    prioritized_recommendations: List[Dict]


class SelfHealingAgent:
    """
    Generates healing recommendations from disease detections and decay reports.
    All recommendations go through human approval workflow before execution.
    """

    def __init__(self) -> None:
        self._agent = self._build_graph()

    def _build_graph(self) -> Any:
        workflow = StateGraph(HealingState)

        workflow.add_node("analyze_diseases", self._analyze_diseases)
        workflow.add_node("analyze_decay", self._analyze_decay)
        workflow.add_node("analyze_ocsie_alerts", self._analyze_ocsie_alerts)
        workflow.add_node("generate_recommendations", self._generate_recommendations)
        workflow.add_node("prioritize_and_deduplicate", self._prioritize_and_deduplicate)

        workflow.set_entry_point("analyze_diseases")
        workflow.add_edge("analyze_diseases", "analyze_decay")
        workflow.add_edge("analyze_decay", "analyze_ocsie_alerts")
        workflow.add_edge("analyze_ocsie_alerts", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "prioritize_and_deduplicate")
        workflow.add_edge("prioritize_and_deduplicate", END)

        return workflow.compile()

    async def run(
        self,
        org_id: str,
        disease_reports: List[Dict],
        decay_report: Dict,
        ocsie_alerts: List[Dict],
    ) -> List[Dict]:
        state: HealingState = {
            "org_id": org_id,
            "disease_reports": disease_reports,
            "decay_report": decay_report,
            "ocsie_alerts": ocsie_alerts,
            "generated_recommendations": [],
            "prioritized_recommendations": [],
        }
        result = await self._agent.ainvoke(state)
        return result["prioritized_recommendations"]

    # Each action's {count} placeholder means something different per disease —
    # map action_type to the evidence key that actually holds that count.
    _COUNT_EVIDENCE_KEY = {
        "merge_docs": "duplicate_pairs_count",       # knowledge_cancer
        "archive_files": "unused_items",              # knowledge_obesity
        "assign_mentor": "high_criticality_departures",  # memory_alzheimers
        "notify_managers": "active_cross_dept_pairs",  # communication_stroke
        "generate_onboarding": "low_originality_ideas",  # innovation_paralysis
    }

    async def _analyze_diseases(self, state: HealingState) -> HealingState:
        recs = []
        for disease in state["disease_reports"]:
            if disease["severity"] in ("critical", "warning"):
                action_type = disease.get("recommended_action", "notify_managers")
                template = ACTION_TEMPLATES.get(action_type, ACTION_TEMPLATES["notify_managers"])
                evidence = disease.get("evidence", {})
                count_key = self._COUNT_EVIDENCE_KEY.get(action_type, "duplicate_pairs_count")

                context = {
                    "disease_type": disease["disease_type"].replace("_", " ").title(),
                    "score": disease["severity_score"] / 100,
                    "days_until_critical": disease.get("days_until_critical") or 30,
                    "domain": evidence.get("top_domain", "operations"),
                    "count": evidence.get(count_key, 0),
                    "threshold": 0.85,
                    "days": 90,
                }

                recs.append({
                    "action_type": action_type,
                    "title": template["title_template"].format(**context),
                    "description": template["description_template"].format(**context),
                    "priority": template["priority"] if disease["severity"] == "critical" else "high",
                    "source": "disease_detection",
                    "trigger_disease": disease["disease_type"],
                    "estimated_impact": f"Reduce {disease['disease_type'].replace('_',' ')} severity by 40-60%",
                    "status": "pending",
                    "parameters": disease.get("evidence", {}),
                })
        state["generated_recommendations"].extend(recs)
        return state

    async def _analyze_decay(self, state: HealingState) -> HealingState:
        decay = state["decay_report"]
        recs = []

        forgotten = decay.get("forgotten_count", 0)
        if forgotten > 10:
            recs.append({
                "action_type": "archive_files",
                "title": f"Archive {forgotten} forgotten knowledge items",
                "description": ACTION_TEMPLATES["archive_files"]["description_template"].format(
                    count=forgotten, days=90
                ),
                "priority": "medium",
                "source": "decay_engine",
                "status": "pending",
                "parameters": {"forgotten_count": forgotten},
            })

        conflicts = decay.get("conflict_count", 0)
        if conflicts > 0:
            recs.append({
                "action_type": "merge_docs",
                "title": f"Resolve {conflicts} conflicting knowledge items",
                "description": f"Decay engine detected {conflicts} conflicting knowledge items requiring resolution.",
                "priority": "high",
                "source": "decay_engine",
                "status": "pending",
                "parameters": {"conflict_count": conflicts},
            })

        state["generated_recommendations"].extend(recs)
        return state

    async def _analyze_ocsie_alerts(self, state: HealingState) -> HealingState:
        recs = []
        for alert in state["ocsie_alerts"]:
            if alert.get("replacement_difficulty_score", 0) >= 0.7:
                recs.append({
                    "action_type": "assign_mentor",
                    "title": ACTION_TEMPLATES["assign_mentor"]["title_template"].format(
                        target_name=alert.get("name", "Unknown Employee")
                    ),
                    "description": ACTION_TEMPLATES["assign_mentor"]["description_template"].format(
                        target_name=alert.get("name", "Unknown"),
                        score=alert.get("replacement_difficulty_score", 0),
                    ),
                    "priority": "critical",
                    "source": "ocsie",
                    "status": "pending",
                    "parameters": alert,
                    "target_entities": [alert.get("user_id")],
                })
        state["generated_recommendations"].extend(recs)
        return state

    async def _generate_recommendations(self, state: HealingState) -> HealingState:
        return state  # All generated in previous steps

    async def _prioritize_and_deduplicate(self, state: HealingState) -> HealingState:
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        seen_types: set = set()
        unique_recs = []
        for rec in state["generated_recommendations"]:
            key = f"{rec['action_type']}_{rec.get('trigger_disease', '')}"
            if key not in seen_types:
                seen_types.add(key)
                unique_recs.append(rec)

        sorted_recs = sorted(
            unique_recs,
            key=lambda r: priority_order.get(r["priority"], 99)
        )
        state["prioritized_recommendations"] = sorted_recs
        logger.info(
            "Healing recommendations generated",
            count=len(sorted_recs),
            critical=sum(1 for r in sorted_recs if r["priority"] == "critical"),
        )
        return state
