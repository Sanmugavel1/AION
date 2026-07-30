"""
AION — Artificial Intelligence Organizational Nervous System
FastAPI Application Entry Point
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import (
    AIONBaseException,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
)
from app.core.graph_store import graph_store
from app.core.logging import configure_logging, get_logger
from app.core.middleware import setup_middleware
from scripts.seed_demo_data import seed_demo_data
from scripts.seed_enterprise import main as seed_enterprise
from scripts.seed_workforce import main as seed_workforce
from scripts.reconcile_workforce import main as reconcile_workforce
from scripts.seed_workplace_data import main as seed_workplace_data

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → yield → shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.APP_ENV}]")

    # Startup
    try:
        await init_db()
        logger.info("Database connected (SQLite)")
    except Exception as e:
        logger.warning(f"Database init warning: {e}")

    # Render's free tier has no persistent disk — the SQLite file (and the
    # demo account in it) is wiped on every redeploy/cold-start. Reseed it
    # here so demo@aion.ai always exists; the seeder is idempotent and
    # no-ops if the demo org is already present.
    try:
        await seed_demo_data()
        logger.info("Demo data verified/seeded")
    except Exception as e:
        logger.warning(f"Demo data seeding warning: {e}")

    # seed_demo_data() alone only produces a ~10-person starter org (5 generic
    # departments). The full "Nova Robotics" demo — 6 departments, 61 people,
    # salaries, funding, leave history — needs this chain on top of it. All four
    # steps are idempotent (match-by-name upserts), so re-running them against an
    # already-complete org is a safe no-op — required on Render, where this whole
    # chain reruns from scratch on every cold start.
    try:
        await seed_enterprise()
        await seed_workforce(apply=True)
        await reconcile_workforce(apply=True)
        await seed_workplace_data(apply=True)
        logger.info("Full workforce and workplace data verified/seeded")
    except Exception as e:
        logger.warning(f"Workforce/workplace seeding warning: {e}")

    logger.info(
        f"Graph store ready: {graph_store._graph.number_of_nodes()} nodes, "
        f"{graph_store._graph.number_of_edges()} edges"
    )
    logger.info("AION is alive and sensing the organization")

    yield

    # Shutdown
    await close_db()
    logger.info("AION shutdown complete")


app = FastAPI(
    title="AION — Artificial Intelligence Organizational Nervous System",
    description=(
        "An AI Nervous System that continuously senses, understands, predicts, "
        "preserves, and evolves an organization's intelligence. "
        "Not a chatbot. Not a RAG tool. The organization's digital brain."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Middleware
setup_middleware(app)

# Prometheus metrics
if settings.PROMETHEUS_ENABLED:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Exception Handlers
@app.exception_handler(AIONBaseException)
async def aion_exception_handler(request: Request, exc: AIONBaseException) -> JSONResponse:
    status_map = {
        "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "CONFLICT": status.HTTP_409_CONFLICT,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
    }
    http_status = status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(
        status_code=http_status,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "tagline": "An AI Nervous System that continuously senses, understands, predicts, preserves, and evolves an organization's intelligence.",
        "status": "alive",
        "layers": 13,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS if settings.is_production else 1,
        reload=not settings.is_production,
        log_level=settings.LOG_LEVEL.lower(),
    )
