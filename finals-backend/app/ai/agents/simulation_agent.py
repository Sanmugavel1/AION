"""
AION Future Simulation Engine — LangGraph Agent
What-if scenario cascading through the organizational memory graph
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from app.ai.agents import _compat  # noqa: F401  (neutralizes langchain_core's legacy debug shim)
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.core.logging import get_logger
from app.repositories.graph_repository import GraphRepository

logger = get_logger(__name__)


class SimulationState(TypedDict):
    scenario_type: str
    parameters: Dict[str, Any]
    org_id: str
    cascade_chain: List[Dict[str, Any]]
    affected_projects: List[Dict]
    affected_customers: List[Dict]
    orphaned_knowledge: List[Dict]
    revenue_risk_usd: float
    recovery_time_days: int
    knowledge_loss_percentage: float
    business_impact_summary: str
    error: Optional[str]


class SimulationAgent:
    """
    LangGraph-based simulation agent that runs what-if scenarios
    by cascading consequences through the Organizational Memory Graph.
    """

    SCENARIO_HANDLERS = {
        "employee_departure": "_simulate_employee_departure",
        "department_closure": "_simulate_department_closure",
        "mass_resignation": "_simulate_mass_resignation",
        "project_delay": "_simulate_project_delay",
        "system_failure": "_simulate_system_failure",
    }

    def __init__(self, graph_repo: GraphRepository) -> None:
        self._graph_repo = graph_repo
        self._agent = self._build_graph()

    def _build_graph(self) -> Any:
        workflow = StateGraph(SimulationState)

        workflow.add_node("parse_scenario", self._parse_scenario)
        workflow.add_node("assess_direct_impact", self._assess_direct_impact)
        workflow.add_node("cascade_knowledge_loss", self._cascade_knowledge_loss)
        workflow.add_node("cascade_project_impact", self._cascade_project_impact)
        workflow.add_node("cascade_customer_impact", self._cascade_customer_impact)
        workflow.add_node("compute_financial_impact", self._compute_financial_impact)
        workflow.add_node("compute_recovery_time", self._compute_recovery_time)
        workflow.add_node("generate_summary", self._generate_summary)

        workflow.set_entry_point("parse_scenario")
        workflow.add_edge("parse_scenario", "assess_direct_impact")
        workflow.add_edge("assess_direct_impact", "cascade_knowledge_loss")
        workflow.add_edge("cascade_knowledge_loss", "cascade_project_impact")
        workflow.add_edge("cascade_project_impact", "cascade_customer_impact")
        workflow.add_edge("cascade_customer_impact", "compute_financial_impact")
        workflow.add_edge("compute_financial_impact", "compute_recovery_time")
        workflow.add_edge("compute_recovery_time", "generate_summary")
        workflow.add_edge("generate_summary", END)

        return workflow.compile()

    async def run(self, scenario_type: str, parameters: Dict, org_id: str) -> SimulationState:
        initial_state: SimulationState = {
            "scenario_type": scenario_type,
            "parameters": parameters,
            "org_id": org_id,
            "cascade_chain": [],
            "affected_projects": [],
            "affected_customers": [],
            "orphaned_knowledge": [],
            "revenue_risk_usd": 0.0,
            "recovery_time_days": 0,
            "knowledge_loss_percentage": 0.0,
            "business_impact_summary": "",
            "error": None,
        }
        result = await self._agent.ainvoke(initial_state)
        return result

    async def _parse_scenario(self, state: SimulationState) -> SimulationState:
        logger.info(
            "Simulation: parsing scenario",
            scenario=state["scenario_type"],
            org_id=state["org_id"],
        )
        state["cascade_chain"].append({
            "step": 1,
            "event": f"Scenario initiated: {state['scenario_type']}",
            "parameters": state["parameters"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return state

    async def _assess_direct_impact(self, state: SimulationState) -> SimulationState:
        scenario = state["scenario_type"]
        params = state["parameters"]

        if scenario == "employee_departure":
            employee_ids = params.get("employee_ids", [])
            departures = []
            for emp_id in employee_ids:
                impact = await self._graph_repo.simulate_person_departure(
                    emp_id, state["org_id"]
                )
                departures.append(impact)

            total_orphaned = sum(d.get("orphaned_knowledge_count", 0) for d in departures)
            state["orphaned_knowledge"] = [
                k for d in departures for k in d.get("orphaned_knowledge", [])
            ]
            state["cascade_chain"].append({
                "step": 2,
                "event": f"{len(employee_ids)} employee(s) depart",
                "direct_impact": f"{total_orphaned} knowledge items become orphaned",
                "affected_employees": [d.get("person_name") for d in departures],
            })

        elif scenario == "mass_resignation":
            n = params.get("count", 20)
            dept = params.get("department")
            estimated_orphaned = int(n * 8.5)  # avg 8.5 knowledge items per engineer
            state["cascade_chain"].append({
                "step": 2,
                "event": f"Mass resignation: {n} employees from {dept or 'all departments'}",
                "direct_impact": f"~{estimated_orphaned} knowledge items at risk",
            })

        elif scenario == "department_closure":
            dept_id = params.get("department_id")
            state["cascade_chain"].append({
                "step": 2,
                "event": f"Department closure: {dept_id}",
                "direct_impact": "All department knowledge and projects affected",
            })

        return state

    async def _cascade_knowledge_loss(self, state: SimulationState) -> SimulationState:
        orphaned_count = len(state["orphaned_knowledge"])
        all_knowledge_count = await self._graph_repo.count_knowledge(state["org_id"])
        knowledge_loss_pct = min(100.0, (orphaned_count / max(all_knowledge_count, 1)) * 100)
        state["knowledge_loss_percentage"] = round(knowledge_loss_pct, 2)

        state["cascade_chain"].append({
            "step": 3,
            "event": "Knowledge cascade assessed",
            "knowledge_items_at_risk": orphaned_count,
            "knowledge_loss_percentage": knowledge_loss_pct,
            "critical_domains": list(set(
                k.get("domain", "unknown") for k in state["orphaned_knowledge"]
            ))[:5],
        })
        return state

    async def _cascade_project_impact(self, state: SimulationState) -> SimulationState:
        # Estimate project delays based on knowledge loss
        knowledge_loss_pct = state["knowledge_loss_percentage"]
        estimated_delayed_projects = max(0, int(knowledge_loss_pct * 0.15))

        state["affected_projects"] = [
            {"name": f"Project_{i}", "delay_weeks": max(1, int(knowledge_loss_pct / 10))}
            for i in range(min(estimated_delayed_projects, 10))
        ]
        state["cascade_chain"].append({
            "step": 4,
            "event": "Project impact cascaded",
            "projects_delayed": len(state["affected_projects"]),
            "average_delay_weeks": max(1, int(knowledge_loss_pct / 10)),
        })
        return state

    async def _cascade_customer_impact(self, state: SimulationState) -> SimulationState:
        delayed_projects = len(state["affected_projects"])
        estimated_affected_customers = delayed_projects * 3  # avg 3 customers per delayed project

        state["affected_customers"] = [
            {"name": f"Customer_{i}", "impact": "service_delay"}
            for i in range(min(estimated_affected_customers, 20))
        ]
        state["cascade_chain"].append({
            "step": 5,
            "event": "Customer impact cascaded",
            "customers_affected": len(state["affected_customers"]),
            "impact_type": "service delays and potential churn",
        })
        return state

    async def _compute_financial_impact(self, state: SimulationState) -> SimulationState:
        delayed = len(state["affected_projects"])
        customers = len(state["affected_customers"])
        knowledge_loss_pct = state["knowledge_loss_percentage"]

        # Revenue risk model:
        # - Each delayed project = $50K/week average
        # - Each affected customer = $10K churn risk
        # - Knowledge loss compounds over time
        avg_delay_weeks = max(1, int(knowledge_loss_pct / 10))
        project_revenue_risk = delayed * 50000 * avg_delay_weeks
        customer_churn_risk = customers * 10000
        knowledge_replacement_cost = len(state["orphaned_knowledge"]) * 5000

        state["revenue_risk_usd"] = project_revenue_risk + customer_churn_risk + knowledge_replacement_cost
        state["cascade_chain"].append({
            "step": 6,
            "event": "Financial impact computed",
            "revenue_risk_usd": state["revenue_risk_usd"],
            "breakdown": {
                "project_delays": project_revenue_risk,
                "customer_churn": customer_churn_risk,
                "knowledge_replacement": knowledge_replacement_cost,
            },
        })
        return state

    async def _compute_recovery_time(self, state: SimulationState) -> SimulationState:
        orphaned = len(state["orphaned_knowledge"])
        delayed_projects = len(state["affected_projects"])

        # Recovery model: each orphaned critical knowledge item = 5 days to rebuild
        # Each delayed project adds 2 weeks
        knowledge_recovery_days = orphaned * 5
        project_recovery_days = delayed_projects * 14
        state["recovery_time_days"] = max(7, int((knowledge_recovery_days + project_recovery_days) / 2))

        state["cascade_chain"].append({
            "step": 7,
            "event": "Recovery timeline computed",
            "recovery_time_days": state["recovery_time_days"],
            "recovery_weeks": round(state["recovery_time_days"] / 7, 1),
        })
        return state

    async def _generate_summary(self, state: SimulationState) -> SimulationState:
        scenario = state["scenario_type"].replace("_", " ").title()
        state["business_impact_summary"] = (
            f"Simulation '{scenario}' reveals: {len(state['orphaned_knowledge'])} knowledge items orphaned "
            f"({state['knowledge_loss_percentage']}% of org knowledge), "
            f"{len(state['affected_projects'])} projects delayed, "
            f"{len(state['affected_customers'])} customers affected. "
            f"Estimated revenue risk: ${state['revenue_risk_usd']:,.0f}. "
            f"Expected recovery: {state['recovery_time_days']} days."
        )
        logger.info(
            "Simulation completed",
            scenario=state["scenario_type"],
            recovery_days=state["recovery_time_days"],
            revenue_risk=state["revenue_risk_usd"],
        )
        return state
