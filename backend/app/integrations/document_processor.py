"""
AION Document Processor
Extracts text, creates embeddings, and indexes raw documents into the knowledge graph
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.integrations.base_connector import RawDocument
from app.ai.embeddings.embedding_service import embed_knowledge_item
from app.core.logging import get_logger

logger = get_logger(__name__)


async def process_and_index(
    doc: RawDocument,
    org_id: str,
    session,
    qdrant_client=None,
    graph_repo=None,
) -> dict:
    """
    Full processing pipeline for a single raw document:
    1. Clean and truncate content
    2. Create embedding vector
    3. Upsert into Qdrant (vector search)
    4. Create KnowledgeItem in PostgreSQL
    5. Create Knowledge node in Neo4j
    Returns the created knowledge_item_id.
    """
    from app.models.knowledge import KnowledgeItem
    from app.core.qdrant_client import upsert_vectors
    from app.core.neo4j_client import execute_write

    item_id = str(uuid4())
    content_clean = _clean_content(doc.content)
    domain = _infer_domain(doc)

    # 1. Embedding
    try:
        vector = embed_knowledge_item(
            title=doc.title,
            content=content_clean,
            domain=domain,
            tags=doc.tags,
        )
    except Exception as e:
        logger.warning("Embedding failed", error=str(e))
        vector = None

    # 2. Qdrant upsert
    vector_id = None
    if vector:
        try:
            from uuid import UUID
            await upsert_vectors(
                collection_name="knowledge_embeddings",
                vectors=[{"id": item_id, "vector": vector, "payload": {
                    "knowledge_id": item_id,
                    "org_id": org_id,
                    "title": doc.title,
                    "domain": domain,
                    "source": doc.source,
                    "tags": doc.tags,
                }}],
            )
            vector_id = item_id
        except Exception as e:
            logger.warning("Qdrant upsert failed", error=str(e))

    # 3. PostgreSQL KnowledgeItem
    try:
        from uuid import UUID
        item = KnowledgeItem(
            id=UUID(item_id),
            org_id=UUID(org_id),
            title=doc.title[:500],
            content=content_clean[:10000],
            domain=domain,
            source_type=doc.source,
            source_url=doc.url,
            vector_id=vector_id,
            is_active=True,
            relevance_score=1.0,
            access_count=0,
            last_accessed_at=datetime.now(timezone.utc),
            tags=doc.tags,
            item_metadata={
                "external_id": doc.external_id,
                "doc_type": doc.doc_type,
                **doc.metadata,
            },
        )
        session.add(item)
        await session.flush()
    except Exception as e:
        logger.warning("KnowledgeItem creation failed", error=str(e))

    # 4. Neo4j node
    try:
        await execute_write(
            """
            MERGE (k:Knowledge {external_id: $ext_id, org_id: $org_id})
            SET k.knowledge_id = $kid,
                k.name = $title,
                k.domain = $domain,
                k.source = $source,
                k.created_at = $created_at
            """,
            {
                "ext_id": doc.external_id,
                "org_id": org_id,
                "kid": item_id,
                "title": doc.title[:200],
                "domain": domain,
                "source": doc.source,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    except Exception as e:
        logger.warning("Neo4j node creation failed", error=str(e))

    return {"knowledge_id": item_id, "domain": domain, "source": doc.source}


def _clean_content(text: str) -> str:
    """Basic text cleaning."""
    if not text:
        return ""
    # Remove excess whitespace
    import re
    text = re.sub(r'\s+', ' ', text.strip())
    return text[:50000]


def _infer_domain(doc: RawDocument) -> str:
    """Infer knowledge domain from source and content."""
    source_domain_map = {
        "github": "engineering",
        "jira": "project_management",
        "confluence": "documentation",
        "slack": "communication",
        "email": "communication",
        "google_drive": "documentation",
        "sharepoint": "documentation",
        "teams": "communication",
    }
    if doc.source in source_domain_map:
        return source_domain_map[doc.source]

    # Keyword-based fallback
    content_lower = (doc.title + " " + doc.content).lower()
    if any(k in content_lower for k in ["bug", "deploy", "api", "code", "engineer"]):
        return "engineering"
    if any(k in content_lower for k in ["customer", "sales", "revenue", "churn"]):
        return "sales"
    if any(k in content_lower for k in ["design", "ux", "user experience", "prototype"]):
        return "design"
    return "general"
