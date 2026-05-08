"""Business logic for Revise Mode.

Covers:
  - Flashcard retrieval (filtered, sorted by exam_likelihood)
  - Quiz question retrieval
  - Confidence update + SM-2 scheduling
  - Oral exam question generation + LLM evaluation
  - Revision plan computation
  - Mastery summary
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.concept import Concept
from app.models.flashcard import Flashcard
from app.models.mastery import UserMastery
from app.models.quiz import QuizQuestion
from app.models.revision_plan import RevisionPlan
from app.revise.schemas import (
    OralExamFeedback,
    OralExamQuestion,
    RevisionPlanEntry,
)
from app.revise.spaced_repetition import next_review, due_in_days
from app.revise.prompts import (
    ORAL_EVAL_SYSTEM,
    ORAL_EVAL_USER,
    ORAL_QUESTION_TEMPLATES,
)
from app.schemas.revise import (
    ConfidenceUpdateResult,
    OralExamFeedbackRead,
    OralExamQuestionRead,
    RevisionPlanEntryRead,
    RevisionPlanRead,
    ReviseSummaryRead,
)
from app.learn.llm_client import LLMClient
from app.config import get_settings

logger = logging.getLogger(__name__)


# ── Flashcards ────────────────────────────────────────────────────────────────

async def get_flashcards(
    db: AsyncSession,
    lecture_id: str,
    question_type: str | None = None,
    difficulty: str | None = None,
    concept_id: str | None = None,
) -> list[Flashcard]:
    q = (
        select(Flashcard)
        .where(Flashcard.lecture_id == lecture_id)
        .order_by(Flashcard.exam_likelihood.desc())
    )
    if question_type:
        q = q.where(Flashcard.question_type == question_type)
    if difficulty:
        q = q.where(Flashcard.difficulty == difficulty)
    if concept_id:
        q = q.where(Flashcard.concept_id == concept_id)
    result = await db.execute(q)
    return list(result.scalars().all())


# ── Quiz questions ────────────────────────────────────────────────────────────

async def get_quiz_questions(
    db: AsyncSession,
    lecture_id: str,
    question_type: str | None = None,
    concept_id: str | None = None,
    shuffle: bool = True,
) -> list[QuizQuestion]:
    q = select(QuizQuestion).where(QuizQuestion.lecture_id == lecture_id)
    if question_type:
        q = q.where(QuizQuestion.question_type == question_type)
    if concept_id:
        q = q.where(QuizQuestion.concept_id == concept_id)
    result = await db.execute(q)
    qs = list(result.scalars().all())
    if shuffle:
        random.shuffle(qs)
    return qs


# ── Mastery retrieval ─────────────────────────────────────────────────────────

async def get_mastery(db: AsyncSession, lecture_id: str) -> list[UserMastery]:
    result = await db.execute(
        select(UserMastery)
        .where(UserMastery.lecture_id == lecture_id)
        .where(UserMastery.flashcard_id.is_not(None))
    )
    return list(result.scalars().all())


async def get_mastery_for_flashcard(
    db: AsyncSession, flashcard_id: str
) -> UserMastery | None:
    result = await db.execute(
        select(UserMastery).where(UserMastery.flashcard_id == flashcard_id)
    )
    return result.scalar_one_or_none()


# ── Confidence update (SM-2) ──────────────────────────────────────────────────

async def update_confidence(
    db: AsyncSession,
    flashcard_id: str,
    confidence: str,
) -> ConfidenceUpdateResult:
    mastery = await get_mastery_for_flashcard(db, flashcard_id)
    if mastery is None:
        # Create on-the-fly (shouldn't happen, but safe)
        fc_result = await db.execute(
            select(Flashcard).where(Flashcard.id == flashcard_id)
        )
        fc = fc_result.scalar_one_or_none()
        if fc is None:
            raise ValueError(f"Flashcard {flashcard_id} not found")
        mastery = UserMastery(
            lecture_id=fc.lecture_id,
            flashcard_id=flashcard_id,
            mastery_level="unseen",
            confidence="not_started",
            attempts=0,
            correct_count=0,
            ease_factor=2.5,
            next_review_interval_days=1,
        )
        db.add(mastery)
        await db.flush()

    # Apply SM-2
    new_interval, new_ef, due_at = next_review(
        confidence=confidence,
        current_interval_days=mastery.next_review_interval_days,
        ease_factor=mastery.ease_factor,
        attempt_number=mastery.attempts,
    )

    # Map confidence to mastery_level
    level_map = {
        "mastered": "mastered",
        "shaky": "familiar",
        "confused": "learning",
        "not_started": "unseen",
    }

    mastery.confidence = confidence
    mastery.mastery_level = level_map.get(confidence, "unseen")
    mastery.ease_factor = new_ef
    mastery.next_review_interval_days = new_interval
    mastery.next_review_at = due_at
    mastery.last_reviewed_at = datetime.now(timezone.utc)
    mastery.attempts += 1
    if confidence == "mastered":
        mastery.correct_count += 1

    await db.commit()

    return ConfidenceUpdateResult(
        flashcard_id=flashcard_id,
        confidence=confidence,
        new_interval_days=new_interval,
        new_ease_factor=new_ef,
        next_review_at=due_at,
    )


# ── Oral exam ─────────────────────────────────────────────────────────────────

async def generate_oral_question(
    db: AsyncSession, concept_id: str
) -> OralExamQuestionRead:
    result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = result.scalar_one_or_none()
    if concept is None:
        raise ValueError(f"Concept {concept_id} not found")

    template = random.choice(ORAL_QUESTION_TEMPLATES)
    question_text = template.format(name=concept.name)

    # Build expected key points from definition + explanation
    expected_points: list[str] = []
    if concept.definition:
        expected_points.append(f"Definition: {concept.definition[:200]}")
    if concept.explanation:
        expected_points.append(f"Explanation: {concept.explanation[:200]}")
    if concept.examples:
        for ex in concept.examples[:2]:
            expected_points.append(f"Example: {ex}")

    return OralExamQuestionRead(
        concept_id=concept.id,
        concept_name=concept.name,
        question_text=question_text,
        expected_points=expected_points,
        timestamp_start=concept.timestamp_start,
    )


async def evaluate_oral_answer(
    db: AsyncSession,
    concept_id: str,
    question_text: str,
    student_answer: str,
) -> OralExamFeedbackRead:
    result = await db.execute(select(Concept).where(Concept.id == concept_id))
    concept = result.scalar_one_or_none()
    if concept is None:
        raise ValueError(f"Concept {concept_id} not found")

    settings = get_settings()
    llm = LLMClient(
        anthropic_key=settings.anthropic_api_key or "",
        openai_key=settings.openai_api_key or "",
    )

    # Build expected points list
    expected_parts = []
    if concept.definition:
        expected_parts.append(f"- {concept.definition[:200]}")
    if concept.explanation:
        expected_parts.append(f"- {concept.explanation[:200]}")
    if concept.examples:
        for ex in concept.examples[:2]:
            expected_parts.append(f"- Example: {ex}")
    expected_points_str = "\n".join(expected_parts) or "- (no specific points)"

    user_prompt = ORAL_EVAL_USER.format(
        name=concept.name,
        definition=concept.definition[:350],
        explanation=(concept.explanation or "")[:300],
        evidence_quote=(concept.evidence_quote or "")[:250],
        timestamp=concept.timestamp_start or 0.0,
        expected_points=expected_points_str,
        student_answer=student_answer,
    )

    if not llm.available:
        # Graceful fallback
        return OralExamFeedbackRead(
            score=50,
            feedback="LLM unavailable — cannot evaluate answer automatically.",
            strong_points=[],
            missed_points=["Automatic evaluation unavailable"],
            timestamp_citations=[],
            suggested_review_ts=concept.timestamp_start,
        )

    response = await llm.extract_json(ORAL_EVAL_SYSTEM, user_prompt)

    return OralExamFeedbackRead(
        score=int(response.get("score", 50)),
        feedback=str(response.get("feedback", "")),
        strong_points=list(response.get("strong_points", [])),
        missed_points=list(response.get("missed_points", [])),
        timestamp_citations=list(response.get("timestamp_citations", [])),
        suggested_review_ts=response.get("suggested_review_ts"),
    )


# ── Revision plan ─────────────────────────────────────────────────────────────

async def compute_revision_plan(
    db: AsyncSession, lecture_id: str
) -> RevisionPlanRead:
    """
    Builds a prioritized revision plan by combining:
      1. Flashcard mastery states (SM-2 due dates)
      2. Concept exam_likelihood
      3. Concept importance
    """
    # Load concepts
    concept_result = await db.execute(
        select(Concept)
        .where(Concept.lecture_id == lecture_id)
        .order_by(Concept.exam_likelihood.desc())
    )
    concepts = list(concept_result.scalars().all())
    concept_map = {c.id: c for c in concepts}

    # Load per-concept mastery
    mastery_result = await db.execute(
        select(UserMastery)
        .where(UserMastery.lecture_id == lecture_id)
        .where(UserMastery.concept_id.is_not(None))
        .where(UserMastery.flashcard_id.is_(None))
    )
    concept_mastery: dict[str, UserMastery] = {
        m.concept_id: m for m in mastery_result.scalars().all()
        if m.concept_id is not None
    }

    entries: list[RevisionPlanEntryRead] = []

    for concept in concepts:
        mastery = concept_mastery.get(concept.id)
        confidence = mastery.confidence if mastery else "not_started"
        interval = mastery.next_review_interval_days if mastery else 1

        days = due_in_days(confidence, interval)

        # Build reason text
        reasons: list[str] = []
        if confidence in ("confused", "not_started"):
            reasons.append("not yet reviewed")
        elif confidence == "shaky":
            reasons.append("needs reinforcement")
        if concept.exam_likelihood >= 0.7:
            reasons.append("high exam likelihood")
        if concept.importance == "core":
            reasons.append("core concept")

        reason = "; ".join(reasons) or "scheduled review"

        # Priority: 1 = highest
        priority = 1 if days == 0 else (2 if days <= 3 else 3)
        if concept.exam_likelihood >= 0.8:
            priority = max(1, priority - 1)

        entries.append(RevisionPlanEntryRead(
            concept_id=concept.id,
            concept_name=concept.name,
            due_in_days=days,
            reason=reason,
            priority=priority,
            timestamp_start=concept.timestamp_start,
            exam_likelihood=concept.exam_likelihood or 0.5,
            confidence=confidence,
        ))

    # Sort: priority ASC, then exam_likelihood DESC
    entries.sort(key=lambda e: (e.priority, -e.exam_likelihood))

    due_today = sum(1 for e in entries if e.due_in_days == 0)
    due_this_week = sum(1 for e in entries if e.due_in_days <= 7)

    return RevisionPlanRead(
        lecture_id=lecture_id,
        entries=entries,
        due_today=due_today,
        due_this_week=due_this_week,
    )


# ── Mastery summary ───────────────────────────────────────────────────────────

async def get_revise_summary(
    db: AsyncSession, lecture_id: str
) -> ReviseSummaryRead:
    # Count flashcards
    fc_count_result = await db.execute(
        select(func.count()).where(Flashcard.lecture_id == lecture_id)  # type: ignore[arg-type]
    )
    flashcard_count = fc_count_result.scalar_one() or 0

    # Count quiz questions
    qz_count_result = await db.execute(
        select(func.count()).where(QuizQuestion.lecture_id == lecture_id)  # type: ignore[arg-type]
    )
    quiz_count = qz_count_result.scalar_one() or 0

    # Confidence distribution (per-flashcard mastery only)
    mastery_result = await db.execute(
        select(UserMastery.confidence, func.count())
        .where(UserMastery.lecture_id == lecture_id)
        .where(UserMastery.flashcard_id.is_not(None))
        .group_by(UserMastery.confidence)
    )
    conf_counts: dict[str, int] = {row[0]: row[1] for row in mastery_result.all()}

    mastered = conf_counts.get("mastered", 0)
    shaky = conf_counts.get("shaky", 0)
    confused = conf_counts.get("confused", 0)
    not_started = conf_counts.get("not_started", 0)
    total = mastered + shaky + confused + not_started or 1

    return ReviseSummaryRead(
        lecture_id=lecture_id,
        flashcard_count=flashcard_count,
        quiz_count=quiz_count,
        mastered_count=mastered,
        shaky_count=shaky,
        confused_count=confused,
        not_started_count=not_started,
        overall_progress=round(mastered / total, 3),
    )
