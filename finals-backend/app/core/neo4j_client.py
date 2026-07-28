"""
AION Neo4j Graph Database Client
Async driver for knowledge graph operations
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import ServiceUnavailable

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_driver: Optional[AsyncDriver] = None


async def get_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_pool_size=50,
            connection_timeout=5,
            max_transaction_retry_time=5,
        )
    return _driver


async def close_driver() -> None:
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    driver = await get_driver()
    async with driver.session(database=settings.NEO4J_DATABASE) as session:
        yield session


async def execute_query(
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    database: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Execute a Cypher query and return results as list of dicts."""
    driver = await get_driver()
    db = database or settings.NEO4J_DATABASE
    async with driver.session(database=db) as session:
        result = await session.run(query, parameters or {})
        records = await result.data()
        return records


async def execute_write(
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Execute a write Cypher query in a transaction."""
    driver = await get_driver()
    async with driver.session(database=settings.NEO4J_DATABASE) as session:
        async def _tx(tx: Any) -> List[Dict[str, Any]]:
            result = await tx.run(query, parameters or {})
            return await result.data()
        return await session.execute_write(_tx)


async def health_check() -> bool:
    """Check Neo4j connectivity."""
    try:
        driver = await get_driver()
        await driver.verify_connectivity()
        return True
    except ServiceUnavailable:
        return False


async def init_constraints() -> None:
    """Initialize Neo4j constraints and indexes."""
    constraints = [
        "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT knowledge_id_unique IF NOT EXISTS FOR (k:Knowledge) REQUIRE k.id IS UNIQUE",
        "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT process_id_unique IF NOT EXISTS FOR (p:Process) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT decision_id_unique IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT risk_id_unique IF NOT EXISTS FOR (r:Risk) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT department_id_unique IF NOT EXISTS FOR (d:Department) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT organization_id_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE",
        "CREATE INDEX person_email_idx IF NOT EXISTS FOR (p:Person) ON (p.email)",
        "CREATE INDEX knowledge_domain_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.domain)",
        "CREATE INDEX knowledge_created_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.created_at)",
        "CREATE INDEX knowledge_last_accessed_idx IF NOT EXISTS FOR (k:Knowledge) ON (k.last_accessed_at)",
    ]
    for constraint in constraints:
        try:
            await execute_write(constraint)
        except Exception as e:
            logger.warning(f"Constraint creation warning: {e}")
    logger.info("Neo4j constraints and indexes initialized")
