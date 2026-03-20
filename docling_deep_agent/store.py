"""
store.py
─────────────────────────────────────────────────────────────────────────────
Qdrant in-memory vector store — embed, upsert, retrieve, rerank.

Query pipeline
──────────────
  1. Dense retrieval   — embed query → cosine search in Qdrant (top_k * 3)
  2. Cross-encoder     — ms-marco-MiniLM-L-6-v2 rescores every candidate
  3. Top-k selection   — keep only the highest-scoring chunks after rerank

The cross-encoder sees the full (query, chunk) pair so it understands
relevance far better than the embedding model alone.

Metadata stored per chunk (from Docling enrichment)
────────────────────────────────────────────────────
  source        : original file path
  pages         : list of page numbers the chunk spans
  headings      : heading breadcrumb trail
  content_type  : text | table | picture | code | formula
  confidence    : Docling extraction confidence score
  code_language : (code chunks) detected programming language
  caption       : (picture chunks) VLM-generated caption
"""

from __future__ import annotations

import logging

from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from sentence_transformers import CrossEncoder

from chunker import ScoredChunk

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

COLLECTION_NAME  = "docling_rag"
EMBEDDING_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL   = "cross-encoder/ms-marco-MiniLM-L-6-v2"
VECTOR_DIM       = 384
RETRIEVAL_FACTOR = 3   # fetch top_k * RETRIEVAL_FACTOR before reranking


# ─────────────────────────────────────────────────────────────────────────────
# Singletons
# ─────────────────────────────────────────────────────────────────────────────

_client: QdrantClient | None = None
_embeddings: HuggingFaceEmbeddings | None = None
_reranker: CrossEncoder | None = None


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(":memory:")
        _client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        logger.info("Qdrant in-memory collection '%s' created", COLLECTION_NAME)
    return _client


def _get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        logger.info("Loading cross-encoder reranker: %s", RERANKER_MODEL)
        _reranker = CrossEncoder(RERANKER_MODEL, max_length=512)
    return _reranker


# ─────────────────────────────────────────────────────────────────────────────
# Upsert
# ─────────────────────────────────────────────────────────────────────────────

def upsert_chunks(chunks: list[ScoredChunk]) -> int:
    """
    Embed and upsert ScoredChunks into Qdrant.

    Idempotent — chunk_id is a stable MD5 hash so re-ingesting the same
    file overwrites existing points, never duplicates them.
    """
    if not chunks:
        return 0

    import uuid
    embedder = _get_embeddings()
    client   = _get_client()

    texts    = [c.text for c in chunks]
    vectors  = embedder.embed_documents(texts)
    payloads = [c.to_qdrant_payload() for c in chunks]

    points = [
        PointStruct(
            id=str(uuid.UUID(c.chunk_id)),
            vector=vec,
            payload=payload,
        )
        for c, vec, payload in zip(chunks, vectors, payloads)
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info("Upserted %d chunks into Qdrant", len(points))
    return len(points)


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval + cross-encoder reranking
# ─────────────────────────────────────────────────────────────────────────────

def retrieve(
    query: str,
    top_k: int = 5,
    content_type: str | None = None,
    source_filter: str | None = None,
) -> list[ScoredChunk]:
    """
    Two-stage retrieval: dense search → cross-encoder rerank → top_k.

    Stage 1 — Dense retrieval
        Embed the query and fetch top_k * RETRIEVAL_FACTOR candidates
        from Qdrant using cosine similarity. Optional metadata filters
        narrow the candidate pool before reranking.

    Stage 2 — Cross-encoder rerank
        ms-marco-MiniLM-L-6-v2 scores every (query, chunk) pair jointly.
        Unlike bi-encoder embeddings, the cross-encoder sees both inputs
        together — capturing exact term overlap, negation, and context.

    Parameters
    ----------
    query          : Natural language question.
    top_k          : Final number of chunks after reranking.
    content_type   : Optional filter — "text" | "table" | "picture" |
                     "code" | "formula".
    source_filter  : Optional partial match on source file name.
    """
    client   = _get_client()
    embedder = _get_embeddings()
    reranker = _get_reranker()

    # Stage 1 — dense retrieval
    query_vec = embedder.embed_query(query)

    conditions = []
    if content_type:
        conditions.append(
            FieldCondition(key="content_type", match=MatchValue(value=content_type))
        )
    if source_filter:
        from qdrant_client.models import MatchText
        conditions.append(
            FieldCondition(key="source", match=MatchText(text=source_filter))
        )

    qdrant_filter = Filter(must=conditions) if conditions else None

    hits = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vec,
        limit=top_k * RETRIEVAL_FACTOR,
        query_filter=qdrant_filter,
        with_payload=True,
    )

    if not hits:
        return []

    # Reconstruct ScoredChunk objects from payloads
    candidates: list[ScoredChunk] = []
    for hit in hits:
        p = hit.payload or {}
        candidates.append(ScoredChunk(
            text=p.get("text", ""),
            doc_source=p.get("source", ""),
            page_numbers=p.get("pages", []),
            headings=p.get("headings", []),
            content_type=p.get("content_type", "text"),
            confidence=p.get("confidence"),
            chunk_id=str(hit.id),
            extra_meta={
                k: v for k, v in p.items()
                if k not in ("text", "source", "pages", "headings",
                             "content_type", "confidence")
            },
        ))

    # Stage 2 — cross-encoder rerank
    pairs  = [(query, c.text) for c in candidates]
    scores = reranker.predict(pairs).tolist()

    ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
    top    = [chunk for _, chunk in ranked[:top_k]]

    logger.info(
        "Retrieve: %d candidates → reranked → %d returned | query='%s…'",
        len(candidates), len(top), query[:50],
    )
    return top


# ─────────────────────────────────────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────────────────────────────────────

def get_collection_stats() -> dict:
    client = _get_client()
    info   = client.get_collection(COLLECTION_NAME)
    return {
        "total_points":    info.points_count,
        "vectors_count":   info.vectors_count,
        "collection":      COLLECTION_NAME,
        "embedding_model": EMBEDDING_MODEL,
        "reranker_model":  RERANKER_MODEL,
        "vector_dim":      VECTOR_DIM,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LangChain tools
# ─────────────────────────────────────────────────────────────────────────────

@tool
def retrieve_chunks(query: str, top_k: int = 5, content_type: str = "") -> str:
    """
    Search the document knowledge base using dense retrieval + cross-encoder
    reranking. Only answers from ingested documents — never from training knowledge.

    Parameters
    ----------
    query        : The user's question exactly as asked.
    top_k        : Number of chunks to return (default 5, max 10).
    content_type : Optional — "table", "code", "formula", "picture", "text".
    """
    top_k = min(int(top_k), 10)
    ct    = content_type.strip() or None
    chunks = retrieve(query=query, top_k=top_k, content_type=ct)

    if not chunks:
        return "No relevant content found for this query in the knowledge base."

    lines = [f"Retrieved {len(chunks)} chunks (dense + cross-encoder rerank):\n"]
    for i, c in enumerate(chunks, 1):
        heading_str = " > ".join(c.headings) if c.headings else "(no heading)"
        page_str    = ", ".join(map(str, c.page_numbers)) if c.page_numbers else "?"
        lines.append(
            f"[{i}] {heading_str}\n"
            f"    Source : {c.doc_source}\n"
            f"    Pages  : {page_str}  |  Type: {c.content_type}\n"
            f"    {c.text[:500]}\n"
        )
    return "\n".join(lines)


@tool
def get_store_stats() -> str:
    """Return statistics about the current document knowledge base."""
    stats = get_collection_stats()
    if stats["total_points"] == 0:
        return "Knowledge base is empty. No documents have been ingested."
    return (
        f"Knowledge base: {stats['total_points']} chunks indexed.\n"
        f"Embedding : {stats['embedding_model']} ({stats['vector_dim']}d)\n"
        f"Reranker  : {stats['reranker_model']}"
    )
