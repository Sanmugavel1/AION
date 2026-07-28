"""
AION GraphRAG Engine — Hybrid Graph + Vector Retrieval
Combines Neo4j traversal with Qdrant vector search for contextual Q&A
"""
from __future__ import annotations

from typing import Any, Optional

from app.ai.embeddings.embedding_service import embed_text
from app.ai.llm.llm_client import complete
from app.core.logging import get_logger
from app.core.neo4j_client import execute_query
from app.core.qdrant_client import search_vectors

logger = get_logger(__name__)

COLLECTION_KNOWLEDGE = "knowledge_embeddings"


async def retrieve_graph_context(org_id: str, query: str, max_hops: int = 2) -> list[dict]:
    """
    Retrieve relevant graph nodes via keyword + semantic graph traversal.
    Returns a list of node dicts with type, name, and properties.
    """
    cypher = """
    CALL db.index.fulltext.queryNodes('knowledge_fulltext', $query)
    YIELD node, score
    WHERE node.org_id = $org_id
    WITH node, score ORDER BY score DESC LIMIT 5
    MATCH path = (node)-[*0..%(hops)d]-(neighbor)
    WHERE neighbor.org_id = $org_id
    RETURN DISTINCT
        labels(neighbor)[0] AS node_type,
        neighbor.name AS name,
        neighbor.domain AS domain,
        neighbor.relevance_score AS relevance,
        score
    ORDER BY score DESC LIMIT 20
    """ % {"hops": max_hops}

    try:
        records = await execute_query(cypher, {"query": query, "org_id": org_id})
        return [dict(r) for r in records]
    except Exception as e:
        logger.warning("Graph context retrieval failed", error=str(e))
        return []


async def retrieve_vector_context(
    query: str, org_id: str, top_k: int = 10
) -> list[dict]:
    """
    Retrieve semantically similar knowledge items from Qdrant.
    """
    query_vec = embed_text(query)
    results = await search_vectors(
        collection_name=COLLECTION_KNOWLEDGE,
        query_vector=query_vec,
        top_k=top_k,
        filter_payload={"org_id": org_id},
    )
    return results


async def hybrid_retrieve(
    query: str,
    org_id: str,
    top_k: int = 10,
    graph_weight: float = 0.3,
) -> list[dict]:
    """
    Merge graph and vector results with configurable weight.
    Returns deduplicated, ranked knowledge items.
    """
    graph_ctx, vector_ctx = await _parallel_retrieve(query, org_id, top_k)

    # Merge by knowledge_id / name
    seen: dict[str, dict] = {}
    for item in vector_ctx:
        kid = item.get("payload", {}).get("knowledge_id", item.get("id", ""))
        score = item.get("score", 0.0) * (1 - graph_weight)
        seen[str(kid)] = {**item.get("payload", {}), "score": score, "source": "vector"}

    for item in graph_ctx:
        name = item.get("name", "")
        if name in seen:
            seen[name]["score"] += item.get("score", 0.0) * graph_weight
            seen[name]["source"] = "hybrid"
        else:
            seen[name] = {**item, "score": item.get("score", 0.0) * graph_weight, "source": "graph"}

    ranked = sorted(seen.values(), key=lambda x: x["score"], reverse=True)
    return ranked[:top_k]


async def _parallel_retrieve(query: str, org_id: str, top_k: int):
    """Fire graph + vector retrieval concurrently."""
    import asyncio
    return await asyncio.gather(
        retrieve_graph_context(org_id, query),
        retrieve_vector_context(query, org_id, top_k),
    )


def _format_context(items: list[dict]) -> str:
    """Format retrieved items into a context string for the LLM."""
    lines = []
    for i, item in enumerate(items, 1):
        name = item.get("name") or item.get("title", "Unknown")
        domain = item.get("domain", "")
        score = item.get("score", 0.0)
        lines.append(f"{i}. [{domain}] {name} (relevance: {score:.2f})")
    return "\n".join(lines)


async def graph_rag_answer(
    question: str,
    org_id: str,
    top_k: int = 10,
) -> dict[str, Any]:
    """
    Full GraphRAG pipeline:
    1. Hybrid retrieval (graph + vector)
    2. Context assembly
    3. LLM generation with citations
    """
    retrieved = await hybrid_retrieve(question, org_id, top_k=top_k)
    context = _format_context(retrieved)

    system = (
        "You are Axon, AION's organizational intelligence system. "
        "Use the provided knowledge context to answer questions about the organization. "
        "Cite sources by number. Be concise and factual."
    )
    prompt = (
        f"Knowledge Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer based on the context above. If information is missing, say so."
    )

    answer = await complete(prompt, system=system, temperature=0.2)

    return {
        "question": question,
        "answer": answer,
        "sources": retrieved[:5],
        "source_count": len(retrieved),
    }
