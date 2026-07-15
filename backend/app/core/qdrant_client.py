"""
AION Qdrant Vector Database Client
Semantic search and similarity operations
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
    SearchRequest,
    UpdateStatus,
    VectorParams,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_qdrant_client: Optional[AsyncQdrantClient] = None


async def get_qdrant() -> AsyncQdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            timeout=30,
        )
    return _qdrant_client


async def close_qdrant() -> None:
    global _qdrant_client
    if _qdrant_client:
        await _qdrant_client.close()
        _qdrant_client = None


async def init_collections() -> None:
    """Initialize required Qdrant collections."""
    client = await get_qdrant()
    collections = [
        (settings.QDRANT_COLLECTION_KNOWLEDGE, settings.EMBEDDING_DIMENSION),
        (settings.QDRANT_COLLECTION_EMPLOYEES, settings.EMBEDDING_DIMENSION),
        (settings.QDRANT_COLLECTION_DECISIONS, settings.EMBEDDING_DIMENSION),
    ]
    existing = {c.name for c in (await client.get_collections()).collections}
    for name, dim in collections:
        if name not in existing:
            await client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {name}")


async def upsert_vectors(
    collection_name: str,
    points: List[Dict[str, Any]],
) -> bool:
    """Upsert vectors into a collection."""
    client = await get_qdrant()
    qdrant_points = [
        PointStruct(id=p["id"], vector=p["vector"], payload=p.get("payload", {}))
        for p in points
    ]
    result = await client.upsert(collection_name=collection_name, points=qdrant_points)
    return result.status == UpdateStatus.COMPLETED


async def search_vectors(
    collection_name: str,
    query_vector: List[float],
    limit: int = 10,
    score_threshold: float = 0.7,
    filter_conditions: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Search for similar vectors."""
    client = await get_qdrant()
    query_filter = None
    if filter_conditions:
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filter_conditions.items()
        ]
        query_filter = Filter(must=conditions)

    results = await client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        score_threshold=score_threshold,
        query_filter=query_filter,
        with_payload=True,
    )
    return [
        {"id": str(r.id), "score": r.score, "payload": r.payload}
        for r in results
    ]


async def delete_vectors(collection_name: str, ids: List[str]) -> bool:
    """Delete vectors by IDs."""
    client = await get_qdrant()
    result = await client.delete(
        collection_name=collection_name,
        points_selector=FilterSelector(
            filter=Filter(
                must=[FieldCondition(key="id", match=MatchValue(value=id_))]
            )
        ),
    )
    return result.status == UpdateStatus.COMPLETED
