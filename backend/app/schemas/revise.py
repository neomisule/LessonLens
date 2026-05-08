"""Pydantic API schemas for Revise Mode endpoints."""
from __future__ import annotations
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Flashcard schemas ─────────────────────────────────────────────────────────

class FlashcardRead(BaseModel):
    id: str
    lecture_id: str
    concept_id: str | None
    front: str
    back: str
    hint: str | None
    difficulty: str
    tags: list[str]
    question_type: str              # surface | deep | application
    timestamp_start: float | None
    timestamp_end: float | None
    time_spent_seconds: int | None
    exam_likelihood: float
    evidence_quote: str | None

    class Config:
        from_attributes = True


class FlashcardListRead(BaseModel):
    flashcards: list[FlashcardRead]
    total: int


# ── Quiz schemas ──────────────────────────────────────────────────────────────

class QuizQuestionRead(BaseModel):
    id: str
    lecture_id: str
    concept_id: str | None
    question_text: str
    question_type: str              # multiple_choice | true_false
    options: list[str] | None
    correct_answer: str
    explanation: str
    difficulty: str
    timestamp_start: float | None
    evidence_quote: str | None

    class Config:
        from_attributes = True


class QuizListRead(BaseModel):
    questions: list[QuizQuestionRead]
    total: int


class QuizAnswerIn(BaseModel):
    question_id: str
    selected_answer: str            # "A" | "B" | "C" | "D" | "True" | "False"


class QuizAnswerResult(BaseModel):
    question_id: str
    correct: bool
    correct_answer: str
    explanation: str
    evidence_quote: str | None


# ── Mastery schemas ───────────────────────────────────────────────────────────

class MasteryRead(BaseModel):
    id: str
    lecture_id: str
    concept_id: str | None
    flashcard_id: str | None
    mastery_level: str
    confidence: str                 # mastered | shaky | confused | not_started
    attempts: int
    correct_count: int
    ease_factor: float
    next_review_interval_days: int
    last_reviewed_at: datetime | None
    next_review_at: datetime | None

    class Config:
        from_attributes = True


class ConfidenceUpdateIn(BaseModel):
    flashcard_id: str
    confidence: str = Field(..., pattern="^(mastered|shaky|confused|not_started)$")


class ConfidenceUpdateResult(BaseModel):
    flashcard_id: str
    confidence: str
    new_interval_days: int
    new_ease_factor: float
    next_review_at: datetime


# ── Oral exam schemas ─────────────────────────────────────────────────────────

class OralExamQuestionRead(BaseModel):
    concept_id: str
    concept_name: str
    question_text: str
    expected_points: list[str]
    timestamp_start: float | None


class OralExamAnswerIn(BaseModel):
    concept_id: str
    question_text: str
    student_answer: str = Field(..., min_length=1, max_length=4000)


class OralExamFeedbackRead(BaseModel):
    score: int                          # 0–100
    feedback: str
    strong_points: list[str]
    missed_points: list[str]
    timestamp_citations: list[dict[str, Any]]
    suggested_review_ts: float | None


# ── Revision plan schemas ─────────────────────────────────────────────────────

class RevisionPlanEntryRead(BaseModel):
    concept_id: str | None
    concept_name: str
    due_in_days: int
    reason: str
    priority: int
    timestamp_start: float | None
    exam_likelihood: float
    confidence: str

    class Config:
        from_attributes = True


class RevisionPlanRead(BaseModel):
    lecture_id: str
    entries: list[RevisionPlanEntryRead]
    due_today: int
    due_this_week: int


# ── Overall Revise Mode summary ───────────────────────────────────────────────

class ReviseSummaryRead(BaseModel):
    lecture_id: str
    flashcard_count: int
    quiz_count: int
    mastered_count: int
    shaky_count: int
    confused_count: int
    not_started_count: int
    overall_progress: float         # 0.0–1.0
