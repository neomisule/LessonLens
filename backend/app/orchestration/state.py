from typing import TypedDict


class PipelineState(TypedDict, total=False):
    """Shared state dict threaded through every LangGraph node."""

    # ── Input ──────────────────────────────────────────────────────────────
    lecture_id: str
    job_id: str
    youtube_url: str
    youtube_id: str          # 11-char YouTube video ID

    # ── Stage: transcript extraction ───────────────────────────────────────
    transcript_ready: bool
    transcript_segments: list[dict]   # NormalizedSegment dicts
    transcript_quality: dict          # QualityReport summary dict
    transcript_error: str | None

    # ── Stage: semantic segmentation ───────────────────────────────────────
    segmentation_ready: bool
    semantic_segments: list[dict]     # SemanticSegmentDict list

    # ── Stage: concept extraction ──────────────────────────────────────────
    concepts_ready: bool
    concepts: list[dict]              # lightweight {name, importance, timestamp_start}

    # ── Stage: learn mode (chapters + summaries, fan-out from concepts) ────
    learn_ready: bool
    total_duration: float             # seconds, used by ConceptMapperAgent
    chapters_count: int
    summaries_count: int

    # ── Stage: concept mapping (enrichment, runs after learn_mode) ─────────
    concept_mapping_ready: bool

    # ── Stage: grounding verification ──────────────────────────────────────
    grounding_ready: bool
    grounding_report: dict            # per-level and per-concept coverage scores

    # ── Stage: flashcard generation (fan-out from concepts) ────────────────
    flashcards_ready: bool
    flashcards: list[dict]

    # ── Stage: mind map (converges after flashcards + summaries) ───────────
    mindmap_ready: bool
    mindmap_nodes: list[dict]
    mindmap_edges: list[dict]

    # ── Error propagation ──────────────────────────────────────────────────
    error: str | None
