"""
subagents.py
─────────────────────────────────────────────────────────────────────────────
Defines the four specialist sub-agents registered with the Deep Agents
orchestrator.

Sub-agent roster
─────────────────
1. ingest_agent   — Converts any file via Docling MCP, chunks, upserts to Qdrant.
2. table_agent    — Structured data specialist: tables, CSV, XLSX.
3. image_agent    — VLM caption + picture classification specialist.
4. code_agent     — Code / formula specialist running in a Docker sandbox.

Why sub-agents and not a single agent
───────────────────────────────────────
Each sub-agent runs in context isolation. The orchestrator calls them via
task() and gets back a concise summary — not the raw tool output stream.
This keeps the orchestrator's context window clean and lets each specialist
be tuned independently (different system prompts, tools, model overrides).

Code agent uses CompiledSubAgent (not dict-based) because it needs its own
sandbox backend — the dict spec doesn't expose a backend parameter.
"""

from __future__ import annotations

import logging

from deepagents import create_deep_agent, CompiledSubAgent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from parser import parse, EnrichmentConfig
from chunker import chunk_document, ChunkerConfig, grade_chunks
from store import upsert_chunks, retrieve_chunks, get_store_stats
from sandbox import DockerSandbox, make_execute_tool, make_upload_tool

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Shared LLM
# MiniMax-M2.7 via Ollama — all sub-agents inherit this unless overridden.
# ─────────────────────────────────────────────────────────────────────────────

def get_llm() -> ChatOllama:
    return ChatOllama(
        model="minimax-m2.7:cloud",
        base_url="http://localhost:11434",
        temperature=0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Ingest tools
# ─────────────────────────────────────────────────────────────────────────────

@tool
def ingest_document(file_path: str) -> str:
    """
    Parse any supported document and store it in the vector knowledge base.

    Supported formats: PDF, DOCX, PPTX, XLSX, CSV, XML, XBRL, PNG, JPG,
    JPEG, TIFF, HTML.

    Call this whenever a user provides a file path or URL and wants to ask
    questions about the document.

    Parameters
    ----------
    file_path : Absolute or relative path to the document, or a URL.

    Returns
    -------
    Summary: how many chunks were ingested and what was detected.
    """
    try:
        doc = parse(file_path, EnrichmentConfig.minimal())
    except Exception as exc:
        return f"Parsing failed for '{file_path}': {exc}"

    chunks = chunk_document(
        doc,
        cfg=ChunkerConfig(min_confidence=0.5),
        source_path=file_path,
    )

    if not chunks:
        return f"Document parsed but produced no usable chunks: '{file_path}'"

    count = upsert_chunks(chunks)

    # Breakdown by content type for the orchestrator summary
    type_counts: dict[str, int] = {}
    for c in chunks:
        type_counts[c.content_type] = type_counts.get(c.content_type, 0) + 1

    breakdown = ", ".join(f"{v} {k}" for k, v in type_counts.items())
    return (
        f"Ingested '{file_path}' → {count} chunks stored ({breakdown}). "
        f"Texts: {len(doc.texts)}, Tables: {len(doc.tables)}, "
        f"Pictures: {len(doc.pictures)}."
    )


@tool
def ingest_document_with_enrichment(file_path: str, enrichment_level: str = "full") -> str:
    """
    Parse a document with enrichment models enabled and store it.

    Use this for documents that contain:
    - Code blocks (enrichment_level="code")
    - Mathematical formulas (enrichment_level="code")
    - Charts or figures (enrichment_level="image")
    - Everything (enrichment_level="full")

    Parameters
    ----------
    file_path        : Path or URL to the document.
    enrichment_level : "minimal" | "code" | "image" | "full"
    """
    cfg_map = {
        "minimal": EnrichmentConfig.minimal(),
        "code":    EnrichmentConfig.for_code_agent(),
        "image":   EnrichmentConfig.for_image_agent(),
        "full":    EnrichmentConfig.full(),
    }
    cfg = cfg_map.get(enrichment_level, EnrichmentConfig.minimal())

    try:
        doc = parse(file_path, cfg)
    except Exception as exc:
        return f"Parsing failed for '{file_path}': {exc}"

    chunks = chunk_document(doc, source_path=file_path)
    count  = upsert_chunks(chunks)
    return f"Ingested '{file_path}' with '{enrichment_level}' enrichment → {count} chunks."


# ─────────────────────────────────────────────────────────────────────────────
# 1. Ingest sub-agent
# ─────────────────────────────────────────────────────────────────────────────

INGEST_AGENT: dict = {
    "name": "ingest-agent",
    "description": (
        "Parses and ingests documents into the knowledge base. "
        "Use when a user provides a file path or URL and needs it indexed "
        "before questions can be answered. Supports PDF, DOCX, PPTX, "
        "XLSX, CSV, XML, XBRL, and images."
    ),
    "system_prompt": (
        "You are a document ingestion specialist. Your job is to:\n\n"
        "1. Call ingest_document() for each file or URL the user provides.\n"
        "2. If the document contains code, formulas, or figures, call "
        "   ingest_document_with_enrichment() with the appropriate level.\n"
        "3. Verify ingestion with get_store_stats().\n"
        "4. Return a concise summary: what was ingested, how many chunks, "
        "   and any content types detected.\n\n"
        "Do NOT answer questions about the content — only ingest and summarise."
    ),
    "tools": [ingest_document, ingest_document_with_enrichment, get_store_stats],
}


# ─────────────────────────────────────────────────────────────────────────────
# Table tools
# ─────────────────────────────────────────────────────────────────────────────

@tool
def retrieve_table_chunks(query: str, top_k: int = 4) -> str:
    """
    Search the knowledge base specifically for table and structured data chunks.

    Parameters
    ----------
    query : Natural language question about data, numbers, or comparisons.
    top_k : Number of results (default 4).
    """
    from store import search
    chunks = search(query=query, top_k=top_k, content_type="table")

    if not chunks:
        return "No table chunks found for this query."

    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append(
            f"[Table {i}] Source: {c.doc_source} | Pages: {c.page_numbers}\n"
            f"{c.text[:600]}\n"
        )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Table sub-agent
# ─────────────────────────────────────────────────────────────────────────────

TABLE_AGENT: dict = {
    "name": "table-agent",
    "description": (
        "Answers questions about structured data — tables, spreadsheets, "
        "CSV data, and numerical comparisons. Use when the user's question "
        "involves rows, columns, figures, statistics, or data analysis."
    ),
    "system_prompt": (
        "You are a structured data analyst specialising in document tables.\n\n"
        "Your workflow:\n"
        "1. Use retrieve_table_chunks() to find relevant table data.\n"
        "2. Analyse the data carefully — rows, columns, totals.\n"
        "3. Answer the question clearly with specific numbers and citations.\n"
        "4. Always mention the source document and page number.\n\n"
        "Output format:\n"
        "- Direct answer with figures\n"
        "- Supporting data from the table\n"
        "- Source citation\n"
        "Keep response under 400 words."
    ),
    "tools": [retrieve_table_chunks, retrieve_chunks],
}


# ─────────────────────────────────────────────────────────────────────────────
# Image tools
# ─────────────────────────────────────────────────────────────────────────────

@tool
def retrieve_picture_chunks(query: str, top_k: int = 4) -> str:
    """
    Search the knowledge base for picture and figure chunks, including VLM
    captions generated by the enrichment pipeline.

    Parameters
    ----------
    query : Question about a chart, diagram, figure, or visual element.
    top_k : Number of results.
    """
    from store import search
    chunks = search(query=query, top_k=top_k, content_type="picture")

    if not chunks:
        return "No picture chunks found. Ensure the document was ingested with image enrichment."

    lines = []
    for i, c in enumerate(chunks, 1):
        caption = c.extra_meta.get("caption", "(no caption)")
        lines.append(
            f"[Figure {i}] Source: {c.doc_source} | Pages: {c.page_numbers}\n"
            f"Caption: {caption}\n"
            f"Context: {c.text[:400]}\n"
        )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Image sub-agent
# ─────────────────────────────────────────────────────────────────────────────

IMAGE_AGENT: dict = {
    "name": "image-agent",
    "description": (
        "Answers questions about charts, figures, diagrams, and visual "
        "content extracted from documents. Use when the question involves "
        "a graph, plot, image, or any visual element."
    ),
    "system_prompt": (
        "You are a visual content analyst. Documents have been processed by "
        "a VLM pipeline that generated captions for all figures.\n\n"
        "Your workflow:\n"
        "1. Use retrieve_picture_chunks() to find relevant figure captions.\n"
        "2. Interpret the visual content from captions and context.\n"
        "3. Describe what the figure shows and answer the question.\n"
        "4. If no caption is available, say so — do not hallucinate.\n\n"
        "Output format:\n"
        "- What the figure shows\n"
        "- Direct answer to the question\n"
        "- Source citation (document + page)\n"
        "Keep response under 300 words."
    ),
    "tools": [retrieve_picture_chunks, retrieve_chunks],
}


# ─────────────────────────────────────────────────────────────────────────────
# Code sub-agent — CompiledSubAgent with Docker sandbox backend
# ─────────────────────────────────────────────────────────────────────────────

@tool
def retrieve_code_chunks(query: str, top_k: int = 4) -> str:
    """
    Search the knowledge base for code blocks and mathematical formulas
    extracted and enriched by Docling's code/formula enrichment pipeline.

    Parameters
    ----------
    query : Question about code, an algorithm, or a formula.
    top_k : Number of results.
    """
    from store import search
    code_chunks   = search(query=query, top_k=top_k // 2, content_type="code")
    formula_chunks = search(query=query, top_k=top_k // 2, content_type="formula")
    all_chunks = code_chunks + formula_chunks

    if not all_chunks:
        return "No code or formula chunks found for this query."

    lines = []
    for i, c in enumerate(all_chunks, 1):
        lang = c.extra_meta.get("code_language", "unknown")
        label = f"Code ({lang})" if c.content_type == "code" else "Formula (LaTeX)"
        lines.append(
            f"[{label} {i}] Source: {c.doc_source} | Pages: {c.page_numbers}\n"
            f"{c.text[:800]}\n"
        )
    return "\n".join(lines)


def build_code_agent() -> CompiledSubAgent:
    """
    Build the code sub-agent with a Docker sandbox as its execution backend.

    The sandbox is created fresh here. It will be stopped when the main
    agent session ends — the lifecycle is managed in agent.py.

    The code agent gets:
    - retrieve_code_chunks() to find extracted code/formulas from Docling
    - execute_in_sandbox() to run the code in the Docker container
    - upload_code_to_sandbox() to seed files before execution
    """
    sandbox = DockerSandbox.create(
        network_mode="none",    # No internet access inside container
        mem_limit="512m",
        cpu_quota=50_000,       # 50% of one CPU core
    )

    execute_tool = make_execute_tool(sandbox)
    upload_tool  = make_upload_tool(sandbox)

    code_agent_graph = create_deep_agent(
        model=get_llm(),
        tools=[retrieve_code_chunks, upload_tool, execute_tool],
        system_prompt=(
            "You are a code and mathematics specialist with access to an "
            "isolated Docker sandbox for safe code execution.\n\n"
            "Your workflow for code questions:\n"
            "1. Use retrieve_code_chunks() to find the relevant code/formula.\n"
            "2. Use upload_code_to_sandbox() to write it to /workspace/script.py.\n"
            "3. Use execute_in_sandbox() to run it and capture the output.\n"
            "4. If execution fails, debug and re-run (max 3 attempts).\n"
            "5. Return the result with a clear explanation.\n\n"
            "Your workflow for formula questions:\n"
            "1. Retrieve the LaTeX formula from retrieve_code_chunks().\n"
            "2. Convert it to a Python/sympy expression.\n"
            "3. Upload and execute in the sandbox.\n"
            "4. Return the numerical result and explain the formula.\n\n"
            "Output format:\n"
            "- Code or formula (quoted)\n"
            "- Execution result\n"
            "- Explanation\n"
            "- Source citation\n"
            "Keep response under 500 words."
        ),
    )

    return CompiledSubAgent(
        name="code-agent",
        description=(
            "Retrieves, runs, and explains code blocks and mathematical "
            "formulas extracted from documents. Executes code safely in an "
            "isolated Docker container. Use when the question involves "
            "code, algorithms, equations, or numerical computation."
        ),
        runnable=code_agent_graph,
    ), sandbox   # Return sandbox too so agent.py can manage its lifecycle


# ─────────────────────────────────────────────────────────────────────────────
# Sub-agent registry
# ─────────────────────────────────────────────────────────────────────────────

def build_all_subagents() -> tuple[list, list]:
    """
    Build and return all sub-agents plus any resources needing cleanup.

    Returns
    -------
    (subagents, resources)
        subagents : list to pass directly to create_deep_agent(subagents=...)
        resources : list of objects with a .stop() method (e.g. DockerSandbox)
    """
    code_agent, sandbox = build_code_agent()

    subagents = [
        INGEST_AGENT,
        TABLE_AGENT,
        IMAGE_AGENT,
        code_agent,        # CompiledSubAgent
    ]

    resources = [sandbox]  # Will be stopped in agent.py finally block

    logger.info(
        "Sub-agents built: %s",
        [s["name"] if isinstance(s, dict) else s.name for s in subagents],
    )
    return subagents, resources
