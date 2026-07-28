"""
AION Embedding Service — Vector Representation Layer
Converts text → dense vectors using Sentence Transformers
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_model: Optional[SentenceTransformer] = None
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 default


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        model_name = getattr(settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        logger.info("Loading embedding model", model=model_name)
        _model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded", dim=EMBEDDING_DIM)
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single text string. Returns list of floats."""
    model = get_embedding_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch embed multiple texts. More efficient than repeated single calls."""
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_knowledge_item(title: str, content: str, domain: str, tags: list[str]) -> list[float]:
    """
    Compose a rich text representation of a knowledge item and embed it.
    Combines title, domain, tags, and content snippet for richer semantic search.
    """
    tag_str = ", ".join(tags) if tags else ""
    content_snippet = content[:500] if content else ""
    composed = f"[Domain: {domain}] [Tags: {tag_str}] {title}. {content_snippet}"
    return embed_text(composed)


def embed_employee_profile(
    name: str,
    role: str,
    primary_domains: list[str],
    technical_expertise: list[str],
) -> list[float]:
    """Embed an employee knowledge profile for similarity search."""
    domains = ", ".join(primary_domains)
    expertise = ", ".join(technical_expertise)
    composed = f"Employee: {name}. Role: {role}. Domains: {domains}. Expertise: {expertise}."
    return embed_text(composed)


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity between two normalized vectors (dot product suffices)."""
    return sum(a * b for a, b in zip(vec_a, vec_b))


def compute_batch_similarity(query_vec: list[float], corpus_vecs: list[list[float]]) -> list[float]:
    """Compute cosine similarity of query against all corpus vectors."""
    return [compute_similarity(query_vec, v) for v in corpus_vecs]
