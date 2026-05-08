"""Revise Mode API router.

Base: /api/v1/revise

Endpoints:
  GET  /revise/{lecture_id}/flashcards           → flashcard list
  GET  /revise/{lecture_id}/quiz                 → quiz question list
  GET  /revise/{lecture_id}/mastery              → mastery records
  POST /revise/confidence                        → update confidence + SM-2
  GET  /revise/{lecture_id}/oral/{concept_id}    → generate oral question
  POST /revise/oral/evaluate                     → LLM oral answer eval
  GET  /revise/{lecture_id}/plan                 → revision plan
  GET  /revise/{lecture_id}/summary              → overall progress summary
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.revise import (
    FlashcardListRead,
    FlashcardRead,
    QuizListRead,
    QuizQuestionRead,
    MasteryRead,
    ConfidenceUpdateIn,
    ConfidenceUpdateResult,
    OralExamQuestionRead,
    OralExamAnswerIn,
    OralExamFeedbackRead,
    RevisionPlanRead,
    ReviseSummaryRead,
)
from app.services import revise_service

router = APIRouter(prefix="/revise", tags=["revise"])


# ── Flashcards ────────────────────────────────────────────────────────────────

@router.get("/{lecture_id}/flashcards", response_model=FlashcardListRead)
async def list_flashcards(
    lecture_id: str,
    question_type: str | None = Query(None, description="surface|deep|application"),
    difficulty: str | None = Query(None, description="easy|medium|hard"),
    concept_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return all flashcards for a lecture, sorted by exam likelihood."""
    cards = await revise_service.get_flashcards(
        db, lecture_id,
        question_type=question_type,
        difficulty=difficulty,
        concept_id=concept_id,
    )
    return FlashcardListRead(
        flashcards=[FlashcardRead.model_validate(c) for c in cards],
        total=len(cards),
    )


# ── Quiz ──────────────────────────────────────────────────────────────────────

@router.get("/{lecture_id}/quiz", response_model=QuizListRead)
async def list_quiz_questions(
    lecture_id: str,
    question_type: str | None = Query(None, description="multiple_choice|true_false"),
    concept_id: str | None = Query(None),
    shuffle: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """Return quiz questions for a lecture (shuffled by default)."""
    qs = await revise_service.get_quiz_questions(
        db, lecture_id,
        question_type=question_type,
        concept_id=concept_id,
        shuffle=shuffle,
    )
    return QuizListRead(
        questions=[QuizQuestionRead.model_validate(q) for q in qs],
        total=len(qs),
    )


# ── Mastery ───────────────────────────────────────────────────────────────────

@router.get("/{lecture_id}/mastery", response_model=list[MasteryRead])
async def get_mastery(
    lecture_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return all mastery records for flashcards in this lecture."""
    records = await revise_service.get_mastery(db, lecture_id)
    return [MasteryRead.model_validate(m) for m in records]


@router.post("/confidence", response_model=ConfidenceUpdateResult)
async def update_confidence(
    body: ConfidenceUpdateIn,
    db: AsyncSession = Depends(get_db),
):
    """
    Update mastery confidence for a flashcard and advance the SM-2 schedule.
    Returns the new review interval and next due date.
    """
    try:
        return await revise_service.update_confidence(
            db, body.flashcard_id, body.confidence
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── Oral Exam ─────────────────────────────────────────────────────────────────

@router.get("/{lecture_id}/oral/{concept_id}", response_model=OralExamQuestionRead)
async def get_oral_question(
    lecture_id: str,
    concept_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Generate an oral exam question for a concept (randomly picked template)."""
    try:
        return await revise_service.generate_oral_question(db, concept_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/oral/evaluate", response_model=OralExamFeedbackRead)
async def evaluate_oral_answer(
    body: OralExamAnswerIn,
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluate a student's oral answer against the lecture evidence using LLM.
    Returns score (0-100), detailed feedback, and transcript citations.
    """
    try:
        return await revise_service.evaluate_oral_answer(
            db,
            concept_id=body.concept_id,
            question_text=body.question_text,
            student_answer=body.student_answer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── Revision Plan ─────────────────────────────────────────────────────────────

@router.get("/{lecture_id}/plan", response_model=RevisionPlanRead)
async def get_revision_plan(
    lecture_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Compute and return the SM-2 spaced repetition revision plan for this lecture.
    Entries sorted by priority (1=highest) and exam likelihood.
    """
    return await revise_service.compute_revision_plan(db, lecture_id)


# ── Revise Summary ────────────────────────────────────────────────────────────

@router.get("/{lecture_id}/summary", response_model=ReviseSummaryRead)
async def get_revise_summary(
    lecture_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return overall progress statistics for the revise mode dashboard."""
    return await revise_service.get_revise_summary(db, lecture_id)
