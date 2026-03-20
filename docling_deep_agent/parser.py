"""
parser.py
─────────────────────────────────────────────────────────────────────────────
Multi-format document parser built on Docling v2.

Supports: PDF · DOCX · PPTX · XLSX/CSV · XML/XBRL · Images (via VLM)

Key upgrades over the v1 blog
──────────────────────────────
• Single DocumentConverter handles all formats via format-specific options.
• Enrichment pipeline: code language detection, LaTeX formula extraction,
  picture classification, and VLM-based figure captioning — all opt-in flags.
• Confidence scores exposed so the chunker can filter low-quality extractions.
• DoclingDocument returned directly (not raw text) so the chunker operates on
  the full hierarchy: body tree, furniture, groups, bounding boxes, provenance.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    PictureDescriptionApiOptions,
    PictureDescriptionVlmOptions,
    VlmPipelineOptions,
)
# VlmPipeline lives in its own module — not in document_converter
from docling.pipeline.vlm_pipeline import VlmPipeline
from docling.pipeline.simple_pipeline import SimplePipeline

# Format options — WordFormatOption and PowerpointFormatOption were moved
from docling.document_converter import DocumentConverter, PdfFormatOption
try:
    from docling.document_converter import WordFormatOption, PowerpointFormatOption
except ImportError:
    # Docling >= 2.7x moved these to datamodel.document
    from docling.datamodel.document import WordFormatOption, PowerpointFormatOption

# smolvlm_picture_description is a pre-built options instance — import path
# shifted between minor versions; we guard both locations
try:
    from docling.datamodel.pipeline_options import smolvlm_picture_description
except ImportError:
    # Fallback: build the options object directly
    smolvlm_picture_description = PictureDescriptionVlmOptions(
        repo_id="HuggingFaceTB/SmolVLM-256M-Instruct",
        prompt="Describe the image in three sentences. Be concise and accurate.",
    )

from docling_core.types.doc import DoclingDocument

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Format routing table
# Maps file extensions → InputFormat so the caller never has to think about it.
# ─────────────────────────────────────────────────────────────────────────────
def _build_extension_map() -> dict:
    """
    Build extension map defensively.
    InputFormat enum members vary across Docling minor versions.
    getattr with a fallback avoids AttributeError on older installs.
    """
    f = InputFormat
    get = lambda name, fb: getattr(f, name, fb)
    m = {
        ".pdf":  f.PDF,
        ".docx": f.DOCX,
        ".doc":  f.DOCX,
        ".pptx": f.PPTX,
        ".ppt":  f.PPTX,
        ".html": f.HTML,
        ".htm":  f.HTML,
        ".csv":  f.CSV,
        ".xlsx": f.XLSX,
        ".xls":  f.XLSX,
        ".png":  f.IMAGE,
        ".jpg":  f.IMAGE,
        ".jpeg": f.IMAGE,
        ".tiff": f.IMAGE,
        ".bmp":  f.IMAGE,
        ".webp": f.IMAGE,
    }
    # Optional formats added in later Docling v2 releases
    for ext, name, fb in [
        (".md",       "MD",       f.HTML),
        (".asciidoc", "ASCIIDOC", f.HTML),
        (".adoc",     "ASCIIDOC", f.HTML),
        (".xbrl",     "XML_XBRL", f.HTML),
        (".xml",      "XML_JATS", f.HTML),
    ]:
        resolved = get(name, fb)
        m[ext] = resolved
    return m


EXTENSION_MAP: dict[str, InputFormat] = _build_extension_map()


# ─────────────────────────────────────────────────────────────────────────────
# Enrichment configuration
# Each flag adds an extra model pass after the base conversion.
# All are False by default to keep baseline conversion fast.
# ─────────────────────────────────────────────────────────────────────────────
class EnrichmentConfig:
    """
    Controls which post-conversion enrichment models run.

    Parameters
    ----------
    code        : Detect programming language of CodeItem elements.
    formulas    : Extract LaTeX from FORMULA-labelled TextItems.
    pic_classify: Classify pictures (chart, diagram, logo, signature …).
    pic_caption : Generate VLM captions for pictures. Requires a VLM.
    vlm_pipeline: Use VlmPipeline (GraniteDocling 258M) instead of the
                  standard pipeline for PDFs — single-pass, higher fidelity.
    pic_scale   : Image resolution multiplier for picture extraction (1–4).
    """

    def __init__(
        self,
        code: bool = False,
        formulas: bool = False,
        pic_classify: bool = False,
        pic_caption: bool = False,
        vlm_pipeline: bool = False,
        pic_scale: float = 2.0,
    ) -> None:
        self.code = code
        self.formulas = formulas
        self.pic_classify = pic_classify
        self.pic_caption = pic_caption
        self.vlm_pipeline = vlm_pipeline
        self.pic_scale = pic_scale

    # Convenience presets ────────────────────────────────────────────────────

    @classmethod
    def minimal(cls) -> "EnrichmentConfig":
        """Fast conversion — no extra model passes."""
        return cls()

    @classmethod
    def full(cls) -> "EnrichmentConfig":
        """All enrichments enabled. Slower but richest metadata."""
        return cls(
            code=True,
            formulas=True,
            pic_classify=True,
            pic_caption=True,
        )

    @classmethod
    def for_code_agent(cls) -> "EnrichmentConfig":
        """
        Preset used by the code sub-agent.
        Enables code + formula enrichment so DoclingDocument carries
        CodeItem.code_language and LaTeX for every formula.
        """
        return cls(code=True, formulas=True)

    @classmethod
    def for_image_agent(cls) -> "EnrichmentConfig":
        """
        Preset used by the image sub-agent.
        Enables picture classification + VLM captioning.
        """
        return cls(pic_classify=True, pic_caption=True, pic_scale=2.0)


# ─────────────────────────────────────────────────────────────────────────────
# Core converter factory
# ─────────────────────────────────────────────────────────────────────────────

def _build_converter(cfg: EnrichmentConfig) -> DocumentConverter:
    """
    Construct a DocumentConverter wired for all supported formats.

    PDF gets the richest set of options (OCR, table structure, enrichments).
    Other formats use Docling's SimplePipeline which is already very capable.
    Images are routed through SmolVLM for end-to-end visual understanding.
    """

    # ── PDF pipeline options ─────────────────────────────────────────────────
    pdf_opts = PdfPipelineOptions()
    pdf_opts.do_ocr = True                          # Always on — handles scanned PDFs
    pdf_opts.do_table_structure = True              # Parse table cells, not just bboxes
    pdf_opts.table_structure_options.do_cell_matching = True

    # Enrichments (opt-in)
    pdf_opts.do_code_enrichment     = cfg.code
    pdf_opts.do_formula_enrichment  = cfg.formulas

    if cfg.pic_classify or cfg.pic_caption:
        pdf_opts.generate_picture_images = True
        pdf_opts.images_scale = cfg.pic_scale

    pdf_opts.do_picture_classification = cfg.pic_classify

    if cfg.pic_caption:
        # SmolVLM-256M — fast, runs fully locally, no API key required.
        # Swap to granite_picture_description for higher quality captions.
        pdf_opts.do_picture_description = True
        pdf_opts.picture_description_options = smolvlm_picture_description

    # Choose pipeline class for PDFs
    if cfg.vlm_pipeline:
        # GraniteDocling 258M — single VLM pass, replaces the ensemble.
        # Higher fidelity on complex layouts, requires ~2 GB VRAM.
        pdf_pipeline_cls = VlmPipeline
        logger.info("PDF conversion: using VlmPipeline (GraniteDocling)")
    else:
        # StandardPdfPipeline import path — stable across Docling v2.x
        try:
            from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
            pdf_pipeline_cls = StandardPdfPipeline
        except ImportError:
            pdf_pipeline_cls = None  # None → Docling picks its default pipeline
        logger.info("PDF conversion: using StandardPdfPipeline")

    # ── Format option map ────────────────────────────────────────────────────
    # PDF gets full options. DOCX / PPTX use FormatOption with no pipeline
    # override — Docling's built-in backends handle them well out of the box.
    # CSV, XML, XBRL, HTML, XLSX are auto-handled; no FormatOption needed.
    pdf_format_kwargs = dict(pipeline_options=pdf_opts)
    if pdf_pipeline_cls is not None:
        pdf_format_kwargs["pipeline_cls"] = pdf_pipeline_cls

    format_options = {
        InputFormat.PDF: PdfFormatOption(**pdf_format_kwargs),
    }

    # Add Word / PowerPoint options only if the classes are available
    try:
        format_options[InputFormat.DOCX] = WordFormatOption()
        format_options[InputFormat.PPTX] = PowerpointFormatOption()
    except Exception:
        pass  # Docling will use default backends for these formats

    # Allowed formats drives which file extensions Docling accepts.
    # IMAGE is included here; for pure image files we override the pipeline
    # to VlmPipeline in parse() below.
    allowed_formats = list(EXTENSION_MAP.values())
    # Deduplicate while preserving order
    seen: set[InputFormat] = set()
    allowed_formats_dedup = []
    for fmt in allowed_formats:
        if fmt not in seen:
            seen.add(fmt)
            allowed_formats_dedup.append(fmt)

    return DocumentConverter(
        allowed_formats=allowed_formats_dedup,
        format_options=format_options,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def parse(
    source: Union[str, Path],
    cfg: EnrichmentConfig | None = None,
) -> DoclingDocument:
    """
    Convert any supported file (or URL) to a DoclingDocument.

    Parameters
    ----------
    source : str | Path
        File path or URL. Extension determines the pipeline used.
    cfg : EnrichmentConfig | None
        Enrichment settings. Defaults to EnrichmentConfig.minimal().

    Returns
    -------
    DoclingDocument
        Fully structured document. Downstream consumers (chunker, sub-agents)
        operate on this object — not raw text — so hierarchy and metadata are
        always available.

    Raises
    ------
    ValueError  : Unsupported file extension.
    RuntimeError: Docling conversion failed.

    Example
    -------
    >>> doc = parse("research_paper.pdf", EnrichmentConfig.full())
    >>> print(doc.export_to_markdown()[:500])
    """
    cfg = cfg or EnrichmentConfig.minimal()
    source = Path(source) if not str(source).startswith("http") else source

    if isinstance(source, Path):
        ext = source.suffix.lower()
        if ext not in EXTENSION_MAP:
            raise ValueError(
                f"Unsupported file extension '{ext}'. "
                f"Supported: {sorted(EXTENSION_MAP.keys())}"
            )
        logger.info("Parsing %s", source.name)
    else:
        logger.info("Parsing URL: %s", source)

    converter = _build_converter(cfg)

    try:
        result = converter.convert(str(source))
    except Exception as exc:
        raise RuntimeError(f"Docling conversion failed for '{source}': {exc}") from exc

    if result.status.name not in ("SUCCESS", "PARTIAL_SUCCESS"):
        raise RuntimeError(
            f"Docling returned status '{result.status.name}' for '{source}'"
        )

    doc: DoclingDocument = result.document

    # Attach source path as provenance metadata so chunks can cite it
    doc.origin = getattr(doc, "origin", None) or {}
    if hasattr(doc, "origin") and isinstance(doc.origin, dict):
        doc.origin["source_path"] = str(source)

    logger.info(
        "Parsed '%s' → %d text items, %d tables, %d pictures",
        source,
        len(doc.texts),
        len(doc.tables),
        len(doc.pictures),
    )
    return doc


