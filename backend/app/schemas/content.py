from pydantic import BaseModel, Field


# ── Summary ──────────────────────────────────────────────────────────────────

class SummarySectionRead(BaseModel):
    heading: str
    body: str
    timestamp_start: float | None
    timestamp_end: float | None

    model_config = {"from_attributes": True}


class SummaryRead(BaseModel):
    id: str
    lecture_id: str
    summary_type: str
    content: str
    sections: list | None

    model_config = {"from_attributes": True}


# ── Concepts ──────────────────────────────────────────────────────────────────

class ConceptRead(BaseModel):
    id: str
    lecture_id: str
    title: str
    definition: str | None
    explanation: str | None
    examples: list | None
    importance: str
    timestamp_start: float | None
    timestamp_end: float | None

    model_config = {"from_attributes": True}


# ── Flashcards ────────────────────────────────────────────────────────────────

class FlashcardRead(BaseModel):
    id: str
    lecture_id: str
    concept_id: str | None
    front: str
    back: str
    difficulty: str
    tags: list | None

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
    options: list | None
    correct_answer: str
    explanation: str
    difficulty: str

    model_config = {"from_attributes": True}


# ── Mastery ───────────────────────────────────────────────────────────────────

class UserMasteryRead(BaseModel):
    id: str
    lecture_id: str
    concept_id: str | None
    flashcard_id: str | None
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
    concept_id: str | None
    label: str
    description: str | None
    node_type: str
    position_x: float
    position_y: float
    color: str | None

    model_config = {"from_attributes": True}


class MindMapEdgeRead(BaseModel):
    id: str
    lecture_id: str
    source_node_id: str
    target_node_id: str
    label: str | None
    edge_type: str

    model_config = {"from_attributes": True}


class MindMapRead(BaseModel):
    nodes: list[MindMapNodeRead]
    edges: list[MindMapEdgeRead]


# ── Search ────────────────────────────────────────────────────────────────────

class SearchQuerySchema(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    lecture_id: str | None = None
    subject_id: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class SearchResultRead(BaseModel):
    segment_id: str
    lecture_id: str
    content: str
    similarity: float
    timestamp_start: float | None
    timestamp_end: float | None
