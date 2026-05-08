from datetime import datetime
from pydantic import BaseModel, Field


# ── Summary ──────────────────────────────────────────────────────────────────

class SummarySectionRead(BaseModel):
    heading: str
    content: str
    timestamp_start: float | None = None
    timestamp_end: float | None = None
    key_points: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SummaryRead(BaseModel):
    id: str
    lecture_id: str
    level: str                          # "brief" | "standard" | "detailed"
    title: str
    content: str
    sections: list[SummarySectionRead] = Field(default_factory=list)
    created_at: datetime | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_sections(cls, obj) -> "SummaryRead":
        """Convert DB Summary, parsing sections JSON list into SummarySectionRead."""
        raw_sections = obj.sections or []
        sections = []
        for s in raw_sections:
            if isinstance(s, dict):
                sections.append(SummarySectionRead(
                    heading=s.get("heading", ""),
                    content=s.get("content", ""),
                    timestamp_start=s.get("timestamp_start"),
                    timestamp_end=s.get("timestamp_end"),
                    key_points=s.get("key_points") or [],
                ))
        return cls(
            id=obj.id,
            lecture_id=obj.lecture_id,
            level=obj.level,
            title=obj.title,
            content=obj.content,
            sections=sections,
            created_at=getattr(obj, "created_at", None),
        )


# ── Chapters ──────────────────────────────────────────────────────────────────

class ChapterRead(BaseModel):
    id: str
    lecture_id: str
    sequence_index: int
    title: str
    summary: str | None = None
    timestamp_start: float
    timestamp_end: float | None = None
    concept_names: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ── Concepts ──────────────────────────────────────────────────────────────────

class ConceptRead(BaseModel):
    id: str
    lecture_id: str
    name: str
    definition: str | None = None
    explanation: str | None = None
    examples: list | None = None
    importance: str
    tags: list | None = None
    timestamp_start: float | None = None
    timestamp_end: float | None = None

    # Learn Mode enrichment fields
    exam_likelihood: float = 0.5
    time_spent_seconds: float | None = None
    why_it_matters: str | None = None
    prerequisites: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)
    evidence_timestamps: list[dict] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ── Learn Mode aggregate ──────────────────────────────────────────────────────

class LearnModeRead(BaseModel):
    """Single response object for the /learn endpoint."""
    summaries: list[SummaryRead] = Field(default_factory=list)
    chapters: list[ChapterRead] = Field(default_factory=list)
    concepts: list[ConceptRead] = Field(default_factory=list)


# ── Flashcards ────────────────────────────────────────────────────────────────

class FlashcardRead(BaseModel):
    id: str
    lecture_id: str
    concept_id: str | None = None
    front: str
    back: str
    difficulty: str
    tags: list | None = None

    model_config = {"from_attributes": True}


class FlashcardSessionItem(BaseModel):
    flashcard_id: str
    result: str = Field(..., pattern="^(correct|incorrect|skipped)$")


class FlashcardSessionSubmit(BaseModel):
    items: list[FlashcardSessionItem]


# ── Quiz ──────────────────────────────────────────────────────────────────────

class QuizQuestionRead(BaseModel):
    id: str
    lecture_id: str
    question_text: str
    question_type: str
    options: list | None = None
    correct_answer: str
    explanation: str
    difficulty: str

    model_config = {"from_attributes": True}


# ── Mastery ───────────────────────────────────────────────────────────────────

class UserMasteryRead(BaseModel):
    id: str
    lecture_id: str
    concept_id: str | None = None
    flashcard_id: str | None = None
    mastery_level: str
    attempts: int
    correct_count: int

    model_config = {"from_attributes": True}


class MasteryStatsRead(BaseModel):
    total: int
    unseen: int
    learning: int
    familiar: int
    mastered: int
    mastery_percentage: float


# ── Mind Map ──────────────────────────────────────────────────────────────────

class MindMapNodeRead(BaseModel):
    id: str
    lecture_id: str
    concept_id: str | None = None
    label: str
    description: str | None = None
    node_type: str
    position_x: float
    position_y: float
    color: str | None = None

    model_config = {"from_attributes": True}


class MindMapEdgeRead(BaseModel):
    id: str
    lecture_id: str
    source_node_id: str
    target_node_id: str
    label: str | None = None
    edge_type: str

    model_config = {"from_attributes": True}


class MindMapRead(BaseModel):
    nodes: list[MindMapNodeRead]
    edges: list[MindMapEdgeRead]


# ── Search (re-exported from app.schemas.search for backwards compatibility) ──

from app.schemas.search import SearchQuerySchema, SearchResultRead  # noqa: F401, E402
