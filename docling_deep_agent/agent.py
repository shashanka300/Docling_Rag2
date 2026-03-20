"""
agent.py
─────────────────────────────────────────────────────────────────────────────
Entry point — two strict phases, in order:

  PHASE 1 — INGESTION
  ────────────────────
  Scans the data/ folder for all supported files.
  For each file: parse (Docling) → enrich → chunk (with full metadata)
  → embed → upsert to Qdrant.
  No agent, no LLM, no chat. Pure pipeline.
  Progress is printed to the terminal.
  Chat does not open until every file is indexed.

  PHASE 2 — CHAT (RAG only)
  ──────────────────────────
  The Deep Agent opens ONLY after Phase 1 completes with at least one
  chunk in Qdrant.
  The agent is hard-constrained to answer ONLY from retrieved chunks.
  It NEVER answers from training knowledge.
  Every answer must cite source file + page number.

Usage
─────
  # Drop files into data/ then run:
  uv run python docling_deep_agent/agent.py

  # Specify a different folder:
  uv run python docling_deep_agent/agent.py --data-dir path/to/docs

  # Demo mode (runs preset questions after ingestion):
  uv run python docling_deep_agent/agent.py --demo
"""

from __future__ import annotations

import argparse
import logging
import sys
import uuid
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from parser import parse, EnrichmentConfig, EXTENSION_MAP
from chunker import chunk_document, ChunkerConfig
from store import upsert_chunks, retrieve_chunks, get_store_stats, get_collection_stats, get_indexed_sources
from subagents import build_all_subagents

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — Ingestion pipeline
# Runs entirely without the agent or LLM.
# ─────────────────────────────────────────────────────────────────────────────

def _pick_enrichment(path: Path) -> EnrichmentConfig:
    """
    Choose enrichment level based on file type.
    PDFs get full enrichment. Images get VLM captioning.
    Everything else gets minimal (fast).
    """
    ext = path.suffix.lower()
    if ext == ".pdf":
        return EnrichmentConfig.full()
    if ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"):
        return EnrichmentConfig.for_image_agent()
    return EnrichmentConfig.minimal()


def run_ingestion(data_dir: Path) -> int:
    """
    Scan data_dir, parse every supported file, chunk with metadata,
    and upsert all chunks into Qdrant.

    Returns total chunk count across all files.
    """
    supported = set(EXTENSION_MAP.keys())
    files = [
        f for f in sorted(data_dir.iterdir())
        if f.is_file() and f.suffix.lower() in supported
    ]

    if not files:
        print(f"\n  \u2717  No supported files found in '{data_dir}'.")
        print(f"     Supported: {', '.join(sorted(supported))}")
        sys.exit(1)

    # Check which files are already indexed in Qdrant (persisted on disk)
    already_indexed = get_indexed_sources()
    new_files = [f for f in files if str(f) not in already_indexed]
    skipped   = [f for f in files if str(f) in already_indexed]

    print(f"\n  Found {len(files)} file(s) in '{data_dir}':")
    for f in files:
        tag = "  [already indexed]" if str(f) in already_indexed else ""
        print(f"    \u2022 {f.name}{tag}")

    if skipped:
        print(f"\n  Skipping {len(skipped)} already-indexed file(s).")

    if not new_files:
        stats = get_collection_stats()
        print(f"\n  \u2713  All files already indexed \u2014 {stats['total_points']} chunks in Qdrant.")
        print(f"     Delete '.qdrant_store/' to force re-ingestion.\n")
        return stats["total_points"]

    print("\n" + "\u2500" * 60)
    print(f"  PHASE 1 \u2014 Ingesting {len(new_files)} new file(s)")
    print("\u2500" * 60)

    total_chunks = 0

    for i, path in enumerate(new_files, 1):
        print(f"\n  [{i}/{len(files)}] {path.name}")

        # ── Parse ────────────────────────────────────────────────────────
        try:
            cfg = _pick_enrichment(path)
            print(f"    ▶ Parsing  (enrichment: {_describe_cfg(cfg)})")
            doc = parse(path, cfg)
        except Exception as exc:
            print(f"    ✗ Parse failed: {exc}")
            logger.exception("Parse failed for %s", path)
            continue

        print(f"    ✓ Parsed   → {len(doc.texts)} texts, "
              f"{len(doc.tables)} tables, {len(doc.pictures)} pictures")

        # ── Chunk ────────────────────────────────────────────────────────
        try:
            chunks = chunk_document(
                doc,
                cfg=ChunkerConfig(
                    min_confidence=0.4,   # Filter very low-quality extractions
                    merge_peers=True,
                ),
                source_path=str(path),
            )
        except Exception as exc:
            print(f"    ✗ Chunking failed: {exc}")
            logger.exception("Chunking failed for %s", path)
            continue

        if not chunks:
            print(f"    ⚠  No chunks produced (all filtered by confidence threshold)")
            continue

        # Breakdown by content type — shows readers what metadata was captured
        type_counts: dict[str, int] = {}
        for c in chunks:
            type_counts[c.content_type] = type_counts.get(c.content_type, 0) + 1
        breakdown = "  |  ".join(f"{k}: {v}" for k, v in sorted(type_counts.items()))
        print(f"    ✓ Chunked  → {len(chunks)} chunks  [{breakdown}]")

        # ── Embed + upsert ────────────────────────────────────────────────
        try:
            print(f"    ▶ Embedding + upserting to Qdrant …")
            count = upsert_chunks(chunks)
            total_chunks += count
            print(f"    ✓ Indexed  → {count} vectors in Qdrant")
        except Exception as exc:
            print(f"    ✗ Upsert failed: {exc}")
            logger.exception("Upsert failed for %s", path)
            continue

    print()
    print("─" * 60)
    if total_chunks == 0:
        print("  ✗  Ingestion produced 0 chunks. Check file contents and try again.")
        sys.exit(1)

    stats = get_collection_stats()
    print(f"  ✓  PHASE 1 COMPLETE")
    print(f"     Total chunks in Qdrant : {stats['total_points']}")
    print(f"     Embedding model        : {stats['embedding_model']}")
    print(f"     Reranker model         : {stats['reranker_model']}")
    print("─" * 60)

    return total_chunks


def _describe_cfg(cfg: EnrichmentConfig) -> str:
    parts = []
    if cfg.code:        parts.append("code")
    if cfg.formulas:    parts.append("formulas")
    if cfg.pic_classify: parts.append("pic-classify")
    if cfg.pic_caption:  parts.append("pic-caption")
    return ", ".join(parts) if parts else "minimal"


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — RAG-only chat
# ─────────────────────────────────────────────────────────────────────────────

# Hard-constrained system prompt — no fallback to training knowledge
RAG_ONLY_PROMPT = """
You are a document question-answering assistant.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE RULES — never break these
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. You ONLY answer using content retrieved from the knowledge base.
2. You NEVER answer from your own training knowledge.
3. Every answer MUST cite the source file and page number.
4. If retrieved chunks do not contain the answer, say exactly:
   "The ingested documents do not contain information about this."
   Do NOT attempt to answer from memory.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR WORKFLOW FOR EVERY QUESTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1 — DECOMPOSE (for complex questions)
  Use write_todos to break multi-part questions into sub-questions.
  Each sub-question is answered independently then merged.

Step 2 — RETRIEVE
  Call retrieve_chunks() for every sub-question.
  Use content_type filter when the question is clearly about a specific
  type: tables → "table", code → "code", figures → "picture".

Step 3 — ROUTE TO SPECIALIST (when content type is clear)
  Tables / structured data  → task("table-agent", sub_question)
  Figures / charts          → task("image-agent", sub_question)
  Code / formulas           → task("code-agent", sub_question)

Step 4 — ANSWER
  Synthesise ONLY from retrieved content.
  Format: direct answer → supporting evidence → citations.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CITATION FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Always end your answer with:
  Source: <filename>, page <N>

If multiple sources: list each on its own line.
""".strip()


def build_agent():
    """
    Build the RAG-only Deep Agent.
    Called AFTER ingestion completes.
    """
    llm = ChatOllama(
        model="minimax-m2.7:cloud",
        base_url="http://localhost:11434",
        temperature=0,
    )

    subagents, resources = build_all_subagents()

    store        = InMemoryStore()
    checkpointer = MemorySaver()

    def make_backend(runtime):
        return CompositeBackend(
            default=StateBackend(runtime),
            routes={"/memories/": StoreBackend(runtime)},
        )

    agent = create_deep_agent(
        model=llm,
        tools=[retrieve_chunks, get_store_stats],
        subagents=subagents,
        system_prompt=RAG_ONLY_PROMPT,
        store=store,
        backend=make_backend,
        checkpointer=checkpointer,
        name="docling-rag-agent",
    )

    return agent, resources


def run_chat(agent, config: dict) -> None:
    """
    Simple REPL — only opens after ingestion is confirmed complete.
    Streams the agent's response token by token.
    """
    print("\n" + "═" * 60)
    print("  PHASE 2 — RAG Chat")
    print("  Ask questions about your documents.")
    print("  Commands: 'stats'  ·  'exit'")
    print("═" * 60 + "\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not question:
            continue

        if question.lower() in ("exit", "quit"):
            break

        if question.lower() == "stats":
            stats = get_collection_stats()
            print(f"\n  {stats['total_points']} chunks | "
                  f"embed: {stats['embedding_model']} | "
                  f"rerank: {stats['reranker_model']}\n")
            continue

        print("\nAgent: ", end="", flush=True)
        last_printed = ""

        try:
            for chunk in agent.stream(
                {"messages": [{"role": "user", "content": question}]},
                config=config,
                stream_mode="values",
            ):
                messages = chunk.get("messages", [])
                if messages:
                    last = messages[-1]
                    if hasattr(last, "content") and isinstance(last.content, str):
                        new_content = last.content
                        if new_content != last_printed:
                            print(new_content[len(last_printed):], end="", flush=True)
                            last_printed = new_content
        except Exception as exc:
            print(f"\n  ✗ Error: {exc}")
            logger.exception("Agent error")

        print("\n")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Docling Deep Agent — Agentic RAG"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Folder to scan for documents (default: ./data)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run preset demo questions after ingestion",
    )
    args = parser.parse_args()

    data_dir: Path = args.data_dir

    if not data_dir.exists():
        print(f"\n  ✗  data directory not found: '{data_dir}'")
        print(f"     Create it and add documents:\n")
        print(f"     mkdir -p {data_dir}")
        print(f"     cp your_file.pdf {data_dir}/\n")
        sys.exit(1)

    print("\n" + "═" * 60)
    print("  Docling Deep Agent  ·  Agentic RAG  ·  MiniMax-M2.7")
    print("═" * 60)

    # ── Phase 1: Ingestion ────────────────────────────────────────────────
    run_ingestion(data_dir)

    # ── Phase 2: Build agent + chat ───────────────────────────────────────
    print("\n  Loading models (LLM + sub-agents) …\n")
    agent, resources = build_agent()
    thread_id = str(uuid.uuid4())
    config    = {"configurable": {"thread_id": thread_id}}

    try:
        if args.demo:
            demo_questions = [
                "What are the main topics covered in the documents?",
                "Summarise the key findings or conclusions.",
                "Are there any tables or structured data? What do they show?",
                "Are there any code blocks or formulas? What do they compute?",
            ]
            print("\n  Running demo questions …\n")
            for q in demo_questions:
                print(f"{'─'*50}\nQ: {q}\n")
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": q}]},
                    config=config,
                )
                print("A:", result["messages"][-1].content[:600], "\n")
        else:
            run_chat(agent, config)
    finally:
        for r in resources:
            if hasattr(r, "stop"):
                r.stop()
        print("\nSession ended. Resources cleaned up.")


if __name__ == "__main__":
    main()
