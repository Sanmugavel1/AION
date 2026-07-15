"""
AION API v1 Router — All 13 modules aggregated
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    memory_graph,
    decay_engine,
    disease_detection,
    simulation,
    self_healing,
    intelligence_index,
    board_advisor,
    ocsie,
    mri,
    ingestion,
)

api_router = APIRouter()

# Core
api_router.include_router(auth.router)

# Document upload / ingestion
api_router.include_router(ingestion.router)

# Module 2: Organizational Memory Graph
api_router.include_router(memory_graph.router)

# Module 4: Knowledge Decay Engine
api_router.include_router(decay_engine.router)

# Module 5: Disease Detection
api_router.include_router(disease_detection.router)

# Module 6: Future Simulation Engine
api_router.include_router(simulation.router)

# Module 7: Self-Healing AI
api_router.include_router(self_healing.router)

# Module 9: Organizational Intelligence Index
api_router.include_router(intelligence_index.router)

# Module 10: AI Board Advisor
api_router.include_router(board_advisor.router)

# Module 11: OCSIE
api_router.include_router(ocsie.router)

# Module 13: Organizational MRI
api_router.include_router(mri.router)
