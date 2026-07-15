"""
AION Test Configuration & Fixtures
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.core.dependencies import get_db
from app.models.base import Base

# Use SQLite for unit tests (fast, no infra needed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with DB override."""
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_org_id() -> str:
    return str(uuid4())


@pytest.fixture
def sample_user_id() -> str:
    return str(uuid4())


@pytest.fixture
def sample_knowledge_item() -> dict:
    return {
        "title": "Test Knowledge Item",
        "content": "This is test content for knowledge testing",
        "domain": "engineering",
        "tags": ["test", "engineering"],
        "source_type": "manual",
    }
