"""
AION Base Integration Connector
All source connectors (Slack, GitHub, Jira, etc.) extend this class.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class RawDocument:
    """Normalized document from any source."""
    source: str
    external_id: str
    title: str
    content: str
    author_email: Optional[str] = None
    author_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    url: Optional[str] = None
    doc_type: str = "document"  # document, message, ticket, commit, pr
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestResult:
    source: str
    count: int
    errors: list[str] = field(default_factory=list)
    documents: list[RawDocument] = field(default_factory=list)


class BaseConnector(ABC):
    """Abstract base for all data source connectors."""

    source_name: str = "unknown"

    def __init__(self, org_id: str, credentials: dict[str, Any]) -> None:
        self.org_id = org_id
        self.credentials = credentials
        self._authenticated = False

    @abstractmethod
    async def authenticate(self) -> bool:
        """Validate credentials and establish connection."""
        ...

    @abstractmethod
    async def fetch_recent(self, since_hours: int = 6) -> list[RawDocument]:
        """Fetch documents modified/created in the last N hours."""
        ...

    @abstractmethod
    async def fetch_all(self, limit: int = 1000) -> list[RawDocument]:
        """Full historical fetch (used for initial sync)."""
        ...

    async def ingest(self, since_hours: int = 6) -> IngestResult:
        """Standard ingest pipeline with error handling."""
        errors = []
        docs = []
        try:
            if not self._authenticated:
                await self.authenticate()
            docs = await self.fetch_recent(since_hours=since_hours)
        except Exception as e:
            errors.append(str(e))
        return IngestResult(
            source=self.source_name,
            count=len(docs),
            errors=errors,
            documents=docs,
        )

    def _make_doc(self, **kwargs) -> RawDocument:
        return RawDocument(source=self.source_name, **kwargs)
