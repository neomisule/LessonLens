"""ExamCoachAgent — generates flashcards, quiz questions, and oral exam material.

Pipeline node (runs after concept_extraction).

Per-concept generation:
  core       → 3 flashcards (surface + deep + application), 2 quiz questions
  supporting → 2 flashcards (surface + deep),               1 quiz question
  supplemental → 1 flashcard (surface),                     0 quiz questions

All content is grounded in transcript evidence.  Mastery records are
initialized at "not_started" for every new flashcard.
"""
import logging
import random
from typing import Any

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.database import AsyncSessionLocal
from app.models.concept import Concept
from app.models.flashcard import Flashcard
from app.models.quiz import QuizQuestion
from app.models.mastery import UserMastery
from app.learn.llm_client import LLMClient
from app.revise.schemas import GeneratedFlashcard, GeneratedQuizQuestion, QuestionType
from app.revise.prompts import (
    EXAM_COACH_SYSTEM,
    FLASHCARD_GEN_USER,
    QUIZ_GEN_SYSTEM,
    QUIZ_GEN_USER,
    ORAL_QUESTION_TEMPLATES,
)
from app.config import get_settings

logger = logging.getLogger(__name__)

_CARDS_BY_IMPORTANCE   = {"core": 3, "supporting": 2, "supplemental": 1}
_QUIZ_BY_IMPORTANCE    = {"core": 2, "supporting": 1, "supplemental": 0}


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _load_concepts(db: AsyncSession, lecture_id: str) -> list[Concept]:
    result = await db.execute(
        select(Concept)
        .where(Concept.lecture_id == lecture_id)
        .order_by(Concept.exam_likelihood.desc())
    )
    return list(result.scalars().all())


async def _generate_flashcards(
    concept: Concept,
    llm: LLMClient,
    n_cards: int,
) -> list[GeneratedFlashcard]:
    if not llm.available or n_cards == 0:
        return []

    examples_str = "; ".join(concept.examples[:2]) if concept.examples else "none"
    user_prompt = FLASHCARD_GEN_USER.format(
        name=concept.name,
        importance=concept.importance,
        definition=concept.definition[:350],
        explanation=(concept.explanation or "")[:300],
        examples=examples_str,
        evidence_quote=(concept.evidence_quote or "")[:250],
        timestamp=concept.timestamp_start or 0.0,
        n_cards=n_cards,
    )

    response = await llm.extract_json(EXAM_COACH_SYSTEM, user_prompt)
    raw_cards = response.get("flashcards", [])
    if not isinstance(raw_cards, list):
        return []

    out: list[GeneratedFlashcard] = []
    for c in raw_cards[:n_cards]:
        if not isinstance(c, dict):
            continue
        front = str(c.get("front", "")).strip()
        back  = str(c.get("back",  "")).strip()
        if not front or not back:
            continue
        qt_raw = c.get("question_type", "surface")
        try:
            qt = QuestionType(qt_raw)
        except ValueError:
            qt = QuestionType.SURFACE
        out.append(GeneratedFlashcard(
            concept_id=concept.id,
            front=front,
            back=back,
            question_type=qt,
            difficulty=str(c.get("difficulty", "medium")),
            hint=str(c.get("hint", "")) or None,
            evidence_quote=str(c.get("evidence_quote", concept.evidence_quote or "")).strip(),
            timestamp_start=concept.timestamp_start or 0.0,
            timestamp_end=concept.timestamp_end,
        ))
    return out


async def _generate_quiz_questions(
    concept: Concept,
    llm: LLMClient,
    n_questions: int,
) -> list[GeneratedQuizQuestion]:
    if not llm.available or n_questions == 0:
        return []

    examples_str = "; ".join(concept.examples[:2]) if concept.examples else "none"
    user_prompt = QUIZ_GEN_USER.format(
        name=concept.name,
        importance=concept.importance,
        definition=concept.definition[:350],
        explanation=(concept.explanation or "")[:300],
        examples=examples_str,
        evidence_quote=(concept.evidence_quote or "")[:250],
        timestamp=concept.timestamp_start or 0.0,
        n_questions=n_questions,
    )

    response = await llm.extract_json(QUIZ_GEN_SYSTEM, user_prompt)
    raw_qs = response.get("questions", [])
    if not isinstance(raw_qs, list):
        return []

    out: list[GeneratedQuizQuestion] = []
    for q in raw_qs[:n_questions]:
        if not isinstance(q, dict):
            continue
        qt = str(q.get("question_type", "multiple_choice"))
        question_text = str(q.get("question_text", "")).strip()
        correct = str(q.get("correct_answer", "")).strip()
        if not question_text or not correct:
            continue
        options = q.get("options")
        if options is not None and not isinstance(options, list):
            options = None
        out.append(GeneratedQuizQuestion(
            concept_id=concept.id,
            question_text=question_text,
            question_type=qt,
            options=options,
            correct_answer=correct,
            explanation=str(q.get("explanation", "")).strip(),
            evidence_quote=str(q.get("evidence_quote", concept.evidence_quote or "")).strip(),
            timestamp_start=concept.timestamp_start or 0.0,
            difficulty=str(q.get("difficulty", "medium")),
        ))
    return out


# ── Agent ─────────────────────────────────────────────────────────────────────

class ExamCoachAgent(BaseAgent):
    """
    Generates study materials for all concepts in a lecture.

    Pipeline state inputs:
      - lecture_id: str

    Pipeline state outputs:
      - flashcards_ready: bool
      - flashcard_count: int
      - quiz_count: int
    """

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        lecture_id: str = state.get("lecture_id", "")
        settings = get_settings()
        llm = LLMClient(
            anthropic_key=settings.anthropic_api_key or "",
            openai_key=settings.openai_api_key or "",
        )

        async with AsyncSessionLocal() as db:
            try:
                concepts = await _load_concepts(db, lecture_id)
                if not concepts:
                    logger.warning("[exam_coach] No concepts for lecture %s", lecture_id)
                    return {"flashcards_ready": False, "flashcard_count": 0, "quiz_count": 0}

                logger.info(
                    "[exam_coach] Generating study materials for %d concepts in lecture %s",
                    len(concepts), lecture_id,
                )

                # ── Clear stale material ──────────────────────────────────────
                await db.execute(sa_delete(Flashcard).where(Flashcard.lecture_id == lecture_id))
                await db.execute(sa_delete(QuizQuestion).where(QuizQuestion.lecture_id == lecture_id))
                await db.execute(sa_delete(UserMastery).where(UserMastery.lecture_id == lecture_id))

                total_cards = 0
                total_quiz  = 0

                for concept in concepts:
                    n_cards = _CARDS_BY_IMPORTANCE.get(concept.importance, 1)
                    n_quiz  = _QUIZ_BY_IMPORTANCE.get(concept.importance, 0)

                    # ── Flashcards ────────────────────────────────────────────
                    if llm.available:
                        generated = await _generate_flashcards(concept, llm, n_cards)
                    else:
                        # Fallback: one surface card from definition
                        generated = [GeneratedFlashcard(
                            concept_id=concept.id,
                            front=f"What is {concept.name}?",
                            back=concept.definition,
                            question_type=QuestionType.SURFACE,
                            difficulty="easy",
                            hint=None,
                            evidence_quote=concept.evidence_quote or "",
                            timestamp_start=concept.timestamp_start or 0.0,
                            timestamp_end=concept.timestamp_end,
                        )]

                    for gf in generated:
                        card = Flashcard(
                            lecture_id=lecture_id,
                            concept_id=concept.id,
                            front=gf.front,
                            back=gf.back,
                            hint=gf.hint,
                            difficulty=gf.difficulty,
                            tags=concept.tags or [],
                            question_type=gf.question_type.value,
                            timestamp_start=gf.timestamp_start,
                            timestamp_end=gf.timestamp_end,
                            time_spent_seconds=concept.time_spent_seconds,
                            exam_likelihood=concept.exam_likelihood,
                            evidence_quote=gf.evidence_quote,
                        )
                        db.add(card)
                        total_cards += 1

                    # ── Quiz questions ────────────────────────────────────────
                    if llm.available and n_quiz > 0:
                        quiz_qs = await _generate_quiz_questions(concept, llm, n_quiz)
                        for gq in quiz_qs:
                            db.add(QuizQuestion(
                                lecture_id=lecture_id,
                                concept_id=concept.id,
                                question_text=gq.question_text,
                                question_type=gq.question_type,
                                options=gq.options,
                                correct_answer=gq.correct_answer,
                                explanation=gq.explanation,
                                difficulty=gq.difficulty,
                                timestamp_start=gq.timestamp_start,
                                evidence_quote=gq.evidence_quote,
                            ))
                            total_quiz += 1

                await db.flush()

                # ── Initialize mastery records (one per flashcard) ────────────
                flashcard_result = await db.execute(
                    select(Flashcard.id).where(Flashcard.lecture_id == lecture_id)
                )
                flashcard_ids = [row[0] for row in flashcard_result.fetchall()]

                for fid in flashcard_ids:
                    db.add(UserMastery(
                        lecture_id=lecture_id,
                        flashcard_id=fid,
                        mastery_level="unseen",
                        confidence="not_started",
                        attempts=0,
                        correct_count=0,
                        ease_factor=2.5,
                        next_review_interval_days=1,
                    ))

                # Also initialize per-concept mastery
                for concept in concepts:
                    db.add(UserMastery(
                        lecture_id=lecture_id,
                        concept_id=concept.id,
                        mastery_level="unseen",
                        confidence="not_started",
                        attempts=0,
                        correct_count=0,
                        ease_factor=2.5,
                        next_review_interval_days=1,
                    ))

                await db.commit()
                logger.info(
                    "[exam_coach] Done: %d flashcards, %d quiz qs for lecture %s",
                    total_cards, total_quiz, lecture_id,
                )

            except Exception as exc:
                logger.error("[exam_coach] Failed: %s", exc, exc_info=True)
                await db.rollback()
                return {"flashcards_ready": False, "error": str(exc)}

        return {
            "flashcards_ready": True,
            "flashcard_count": total_cards,
            "quiz_count": total_quiz,
        }
