"""
AION API â€” Module 6: Future Simulation Engine
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.ai.agents.simulation_agent import SimulationAgent
from app.core.dependencies import AuthUser, DbSession, require_perm
from app.core.security import Permission
from app.repositories.graph_repository import GraphRepository

router = APIRouter(prefix="/simulation", tags=["Module 6: Future Simulation Engine"])


class SimulationRequest(BaseModel):
    scenario_type: str = Field(
        ...,
        description="Type: employee_departure | mass_resignation | department_closure | project_delay | system_failure",
    )
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


PREDEFINED_SCENARIOS = [
    {
        "id": "cto_resignation",
        "name": "CTO Resigns",
        "scenario_type": "employee_departure",
        "description": "Simulate the organizational impact if the CTO suddenly resigns",
        "parameters": {"employee_ids": ["<cto_user_id>"]},
    },
    {
        "id": "mass_resignation_20",
        "name": "20 Engineers Resign",
        "scenario_type": "mass_resignation",
        "description": "Simulate mass resignation of 20 engineers from engineering department",
        "parameters": {"count": 20, "department": "engineering"},
    },
    {
        "id": "dept_closure",
        "name": "Department Closes",
        "scenario_type": "department_closure",
        "description": "Simulate full closure of a department",
        "parameters": {"department_id": "<dept_id>"},
    },
    {
        "id": "project_delayed",
        "name": "Key Project Delayed 3 Months",
        "scenario_type": "project_delay",
        "description": "Cascade impact of a flagship project being delayed by 3 months",
        "parameters": {"delay_weeks": 12},
    },
]


@router.get("/scenarios")
async def list_predefined_scenarios(
    current_user: AuthUser,
):
    """List all predefined what-if simulation scenarios."""
    return {"scenarios": PREDEFINED_SCENARIOS}


@router.post("/run")
async def run_simulation(
    request: SimulationRequest,
    current_user: AuthUser,
):
    """
    Run a what-if simulation. Cascades consequences through the memory graph:
    Employee departure â†’ Knowledge loss â†’ Project delays â†’ Revenue impact â†’ Customer impact â†’ Recovery time.
    Returns complete cascade chain with quantified business impact.
    """
    agent = SimulationAgent(graph_repo=GraphRepository())
    result = await agent.run(
        scenario_type=request.scenario_type,
        parameters=request.parameters,
        org_id=current_user.org_id,
    )
    return {
        "simulation_id": "sim_" + str(hash(str(request.parameters)))[:8],
        "scenario_type": result["scenario_type"],
        "org_id": current_user.org_id,
        "status": "completed",
        "cascade_chain": result["cascade_chain"],
        "results": {
            "knowledge_loss_percentage": result["knowledge_loss_percentage"],
            "affected_projects": result["affected_projects"],
            "affected_customers": result["affected_customers"],
            "orphaned_knowledge": result["orphaned_knowledge"],
            "revenue_risk_usd": result["revenue_risk_usd"],
            "recovery_time_days": result["recovery_time_days"],
            "business_impact_summary": result["business_impact_summary"],
        },
    }
