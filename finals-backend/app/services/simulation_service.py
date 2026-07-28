"""
AION Simulation Service — Module 6: Future State Simulation
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.simulation_agent import SimulationAgent
from app.core.logging import get_logger

logger = get_logger(__name__)

PREDEFINED_SCENARIOS = [
    {
        "id": "key_person_departure",
        "name": "Key Person Departure",
        "description": "Simulates the knowledge and project impact of losing a critical employee",
        "parameters": ["person_id", "departure_date"],
        "typical_duration_days": 90,
    },
    {
        "id": "department_restructure",
        "name": "Department Restructuring",
        "description": "Models knowledge flow disruption from team mergers or splits",
        "parameters": ["departments", "restructure_type"],
        "typical_duration_days": 180,
    },
    {
        "id": "technology_migration",
        "name": "Technology Migration",
        "description": "Estimates knowledge gap risk when adopting a new technology stack",
        "parameters": ["old_tech", "new_tech", "team_size"],
        "typical_duration_days": 365,
    },
    {
        "id": "rapid_scaling",
        "name": "Rapid Headcount Scaling",
        "description": "Predicts knowledge dilution risk during fast hiring phases",
        "parameters": ["current_headcount", "target_headcount", "timeline_months"],
        "typical_duration_days": 270,
    },
]


class SimulationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._agent = SimulationAgent()

    def get_scenarios(self) -> list[dict]:
        return PREDEFINED_SCENARIOS

    async def run_simulation(
        self, org_id: UUID, scenario_type: str, parameters: dict
    ) -> dict:
        logger.info(
            "Running simulation", org_id=str(org_id), scenario=scenario_type
        )
        result = await self._agent.run(
            org_id=str(org_id),
            scenario_type=scenario_type,
            parameters=parameters,
        )
        return result
