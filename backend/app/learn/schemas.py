"""Internal dataclasses for the Learn Mode pipeline.

These are NOT Pydantic API schemas — they are pure Python dataclasses used as
intermediate containers between pipeline stages.
"""
from dataclasses import dataclass, field


# ── LLM-extracted concept (before DB storage) ─────────────────────────────────

@dataclass
class ExtractedConcept:
    name: str
    definition: str
    explanation: str
    examples: list[str]
    importance: str                      # "core" | "supporting" | "supplemental"
    tags: list[str]
    timestamp_start: float               # always taken from source segment
    timestamp_end: float | None = None
    evidence_quote: str = ""             # verbatim quote from transcript proving definition
    segment_index: int = 0              # which semantic segment it came from


# ── Chapter boundary ──────────────────────────────────────────────────────────

@dataclass
class ExtractedChapter:
    sequence_index: int
    title: str
    summary: str
    timestamp_start: float
    timestamp_end: float | None
    concept_names: list[str] = field(default_factory=list)


# ── Summary section ───────────────────────────────────────────────────────────

@dataclass
class SummarySection:
    heading: str
    content: str
    timestamp_start: float               # always from actual segment
    timestamp_end: float | None = None
    key_points: list[str] = field(default_factory=list)


# ── Generated summary ─────────────────────────────────────────────────────────

@dataclass
class GeneratedSummary:
    level: str                           # "brief" | "standard" | "detailed"
    title: str
    content: str
    sections: list[SummarySection]


# ── Concept mapping metadata (computed post-extraction) ───────────────────────

@dataclass
class ConceptMapping:
    concept_name: str
    time_spent_seconds: float
    exam_likelihood: float               # 0-1
    why_it_matters: str | None
    prerequisites: list[str]             # names of prerequisite concepts
    related_concepts: list[str]          # names of related concepts
    evidence_timestamps: list[dict]      # [{"ts": float, "quote": str}, ...]


# ── Grounding evidence ────────────────────────────────────────────────────────

@dataclass
class GroundingResult:
    claim: str
    is_grounded: bool
    timestamp: float | None
    evidence_quote: str
    segment_id: str | None = None
