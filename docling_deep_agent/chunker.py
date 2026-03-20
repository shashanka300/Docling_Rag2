"""
chunker.py
─────────────────────────────────────────────────────────────────────────────
Chunking layer: DoclingDocument → scored, embeddable chunks.

Filters out chunks whose Docling extraction score falls below a threshold
before they reach the vector store.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Iterator

from docling.chunking import HybridChunker
from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker
from docling_core.types.doc import DoclingDocument

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Chunk dataclass
# Wraps the raw Docling chunk with extra metadata for Qdrant upsert.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ScoredChunk:
    """
    A single chunk ready for embedding and storage.

    Attributes
    ----------
    text          : The serialized chunk text (heading context prepended).
    doc_source    : Original file path / URL.
    page_numbers  : Page numbers this chunk spans (if available).
    headings      : Heading breadcrumb trail from DoclingDocument hierarchy.
    content_type  : "text" | "table" | "picture" | "code" | "formula"
    confidence    : Docling extraction confidence (0–1). None = not available.
    chunk_id      : Stable hash key for deduplication in Qdrant.
    extra_meta    : Any additional metadata (e.g. code_language, caption).
    """
    text: str
    doc_source: str = ""
    page_numbers: list[int] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    content_type: str = "text"
    confidence: float | None = None
    chunk_id: str = ""
    extra_meta: dict = field(default_factory=dict)

    def to_qdrant_payload(self) -> dict:
        """Serialize to a flat dict for Qdrant point payload."""
        return {
            "text":         self.text,
            "source":       self.doc_source,
            "pages":        self.page_numbers,
            "headings":     self.headings,
            "content_type": self.content_type,
            "confidence":   self.confidence,
            **self.extra_meta,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Chunker configuration
# ─────────────────────────────────────────────────────────────────────────────

class ChunkerConfig:
    """
    Parameters
    ----------
    tokenizer        : HuggingFace tokenizer repo id aligned to the embedding
                       model. Default is all-MiniLM-L6-v2 (384-dim).
    max_tokens       : Hard token ceiling per chunk.
    min_confidence   : Chunks below this confidence score are dropped.
                       Set to 0.0 to disable filtering.
    merge_peers      : Merge successive small chunks with the same heading
                       (HybridChunker default = True).
    use_hierarchical : Use HierarchicalChunker instead of HybridChunker.
                       Produces finer-grained chunks (one per element).
                       Good for table-heavy documents.
    """

    def __init__(
        self,
        tokenizer: str = "sentence-transformers/all-MiniLM-L6-v2",
        max_tokens: int = 512,
        min_confidence: float = 0.5,
        merge_peers: bool = True,
        use_hierarchical: bool = False,
    ) -> None:
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens
        self.min_confidence = min_confidence
        self.merge_peers = merge_peers
        self.use_hierarchical = use_hierarchical


# ─────────────────────────────────────────────────────────────────────────────
# Core chunking function
# ─────────────────────────────────────────────────────────────────────────────

def chunk_document(
    doc: DoclingDocument,
    cfg: ChunkerConfig | None = None,
    source_path: str = "",
) -> list[ScoredChunk]:
    """
    Chunk a DoclingDocument into ScoredChunk objects ready for embedding.

    Steps
    ─────
    1. Run HybridChunker (or HierarchicalChunker) on the DoclingDocument.
    2. Serialize each chunk using the chunker's contextualize() — this
       prepends heading breadcrumbs so embedding captures full context.
    3. Attach metadata: content type, page numbers, headings, confidence.
    4. Filter out chunks below min_confidence threshold.

    Parameters
    ----------
    doc         : DoclingDocument from parser.parse().
    cfg         : ChunkerConfig. Defaults to ChunkerConfig().
    source_path : Original file path string for provenance metadata.

    Returns
    -------
    list[ScoredChunk] — filtered, metadata-rich chunks.
    """
    cfg = cfg or ChunkerConfig()

    # ── Pick chunker ─────────────────────────────────────────────────────────
    if cfg.use_hierarchical:
        chunker = HierarchicalChunker(merge_list_items=True)
        logger.info("Using HierarchicalChunker")
    else:
        chunker = HybridChunker(
            tokenizer=cfg.tokenizer,
            max_tokens=cfg.max_tokens,
            merge_peers=cfg.merge_peers,
        )
        logger.info("Using HybridChunker (tokenizer=%s, max=%d)", cfg.tokenizer, cfg.max_tokens)

    raw_chunks = list(chunker.chunk(doc))
    logger.info("Raw chunks: %d", len(raw_chunks))

    # ── Build ScoredChunks ───────────────────────────────────────────────────
    scored: list[ScoredChunk] = []

    for raw in raw_chunks:
        # contextualize() prepends heading path to the chunk text.
        # This is the string that gets embedded — not raw.text alone.
        text = chunker.contextualize(raw)

        if not text.strip():
            continue

        # Extract metadata from the chunk's meta object
        meta = raw.meta if hasattr(raw, "meta") else None

        headings: list[str] = []
        page_nums: list[int] = []
        confidence: float | None = None
        content_type = "text"
        extra: dict = {}

        if meta:
            # Heading breadcrumbs
            if hasattr(meta, "headings") and meta.headings:
                headings = [str(h) for h in meta.headings]

            # Page numbers from provenance
            if hasattr(meta, "doc_items"):
                for item in meta.doc_items:
                    prov = getattr(item, "prov", [])
                    for p in prov:
                        page = getattr(p, "page_no", None)
                        if page is not None:
                            page_nums.append(int(page))

                    # Content type detection
                    item_type = type(item).__name__
                    if "Table" in item_type:
                        content_type = "table"
                    elif "Picture" in item_type:
                        content_type = "picture"
                    elif "Code" in item_type:
                        content_type = "code"
                        lang = getattr(item, "code_language", None)
                        if lang:
                            extra["code_language"] = lang
                    elif hasattr(item, "label") and str(getattr(item, "label", "")).upper() == "FORMULA":
                        content_type = "formula"

                    # Confidence
                    conf = getattr(item, "confidence", None)
                    if conf is not None:
                        confidence = float(conf)

            # Caption for pictures
            if content_type == "picture" and hasattr(meta, "doc_items"):
                for item in meta.doc_items:
                    annots = getattr(item, "annotations", [])
                    for a in annots:
                        if hasattr(a, "text") and a.text:
                            extra["caption"] = a.text
                            break

        # ── Confidence filter ─────────────────────────────────────────────
        if (
            confidence is not None
            and cfg.min_confidence > 0.0
            and confidence < cfg.min_confidence
        ):
            logger.debug(
                "Filtered low-confidence chunk (%.2f < %.2f): %s…",
                confidence, cfg.min_confidence, text[:60],
            )
            continue

        chunk_id = hashlib.md5(
            f"{source_path}:{text[:200]}".encode()
        ).hexdigest()

        scored.append(ScoredChunk(
            text=text,
            doc_source=source_path,
            page_numbers=sorted(set(page_nums)),
            headings=headings,
            content_type=content_type,
            confidence=confidence,
            chunk_id=chunk_id,
            extra_meta=extra,
        ))

    filtered_count = len(raw_chunks) - len(scored)
    if filtered_count > 0:
        logger.info(
            "Confidence filter removed %d/%d chunks (threshold=%.2f)",
            filtered_count, len(raw_chunks), cfg.min_confidence,
        )

    logger.info("Final chunk count: %d", len(scored))
    return scored


