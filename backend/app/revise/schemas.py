"""Internal dataclasses for Revise Mode.

Pure Python dataclasses — NOT Pydantic API schemas.
"""
from dataclasses import dataclass, field
from enum import Enum


class QuestionType(str, Enum):
    SURFACE     = "surface"      # define / recall
    DEEP        = "deep"         # explain / analyse
    APPLICATION = "application"  # apply to scenario


class Confidence(str, Enum):
    MASTERED    = "mastered"    # fully confident
    SHAKY       = "shaky"       # partially correct
    CONFUSED    = "confused"    # didn't get it
    NOT_STARTED = "not_started" # never reviewed


# SM-2 quality scores per confidence level
CONFIDENCE_Q: dict[str, int] = {
    "mastered":    5,
    "shaky":       3,
    "confused":    1,
    "not_started": 0,
}


@dataclass
class GeneratedFlashcard:
    concept_id: str
    front: str
    back: str
    question_type: QuestionType
    difficulty: str            # "easy" | "medium" | "hard"
    hint: str | None
    evidence_quote: str        # verbatim transcript quote grounding the answer
    timestamp_start: float
    timestamp_end: float | None


@dataclass
class GeneratedQuizQuestion:
    concept_id: str
    question_text: str
    question_type: str         # "multiple_choice" | "true_false"
    options: list[str] | None  # None for true_false
    correct_answer: str
    explanation: str
    evidence_quote: str
    timestamp_start: float
    difficulty: str


@dataclass
class OralExamQuestion:
    concept_id: str
    concept_name: str
    question_text: str
    expected_points: list[str]     # key points the answer should contain
    timestamp_start: float | None


@dataclass
class OralExamFeedback:
    score: int                      # 0–100
    feedback: str                   # overall feedback paragraph
    strong_points: list[str]        # what the student got right
    missed_points: list[str]        # what was missing
    timestamp_citations: list[dict] # [{"ts": float, "quote": str}]
    suggested_review_ts: float | None


@dataclass
class RevisionPlanEntry:
    concept_id: str
    concept_name: str
    due_in_days: int
    reason: str
    priority: int              # 1 = highest
    timestamp_start: float | None
    exam_likelihood: float
    confidence: str            # current confidence state
