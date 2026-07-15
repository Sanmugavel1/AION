"""
AION Celery Worker — Module 1: Knowledge Sensing Layer
Continuously ingests data from all connected sources
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.core.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    name="aion.sensing.ingest_all_sources",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=300,
)
def ingest_all_sources(self, org_id: str) -> dict:
    """
    Ingest data from ALL connected organizational sources.
    Runs every 5 minutes via Celery Beat.
    Unlike RAG, this is continuous — not query-driven.
    """
    logger.info("Sensing worker: ingesting all sources", org_id=org_id)

    sources_processed = []
    errors = []

    source_handlers = [
        ("slack", _ingest_slack),
        ("github", _ingest_github),
        ("jira", _ingest_jira),
        ("confluence", _ingest_confluence),
        ("email", _ingest_email),
        ("google_drive", _ingest_google_drive),
        ("sharepoint", _ingest_sharepoint),
        ("teams", _ingest_teams),
    ]

    for source_name, handler in source_handlers:
        try:
            result = handler(org_id)
            sources_processed.append({
                "source": source_name,
                "items_processed": result.get("count", 0),
                "status": "success",
            })
        except Exception as e:
            logger.warning(f"Source {source_name} failed: {e}", org_id=org_id)
            errors.append({"source": source_name, "error": str(e)})

    return {
        "org_id": org_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources_processed": sources_processed,
        "errors": errors,
        "total_items": sum(s["items_processed"] for s in sources_processed),
    }


def _ingest_slack(org_id: str) -> dict:
    """Ingest messages and shared knowledge from Slack."""
    return {"count": 0, "source": "slack"}


def _ingest_github(org_id: str) -> dict:
    """Ingest commits, PRs, issues, and code reviews from GitHub."""
    return {"count": 0, "source": "github"}


def _ingest_jira(org_id: str) -> dict:
    """Ingest tickets, decisions, and project updates from Jira."""
    return {"count": 0, "source": "jira"}


def _ingest_confluence(org_id: str) -> dict:
    """Ingest pages and knowledge from Confluence."""
    return {"count": 0, "source": "confluence"}


def _ingest_email(org_id: str) -> dict:
    """Ingest email threads and decisions from connected email."""
    return {"count": 0, "source": "email"}


def _ingest_google_drive(org_id: str) -> dict:
    """Ingest documents from Google Drive."""
    return {"count": 0, "source": "google_drive"}


def _ingest_sharepoint(org_id: str) -> dict:
    """Ingest documents from SharePoint."""
    return {"count": 0, "source": "sharepoint"}


def _ingest_teams(org_id: str) -> dict:
    """Ingest chats and meeting transcripts from Microsoft Teams."""
    return {"count": 0, "source": "teams"}


@celery_app.task(name="aion.sensing.process_document")
def process_document(doc_id: str, org_id: str, file_type: str) -> dict:
    """Process a single document: extract text, create embeddings, add to graph."""
    logger.info("Processing document", doc_id=doc_id, file_type=file_type)
    return {"doc_id": doc_id, "status": "processed"}
