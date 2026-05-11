"""ExamCoachAgent — generates flashcards and quiz questions via batched LLM calls.

OLD approach: 1 LLM call per concept × (flashcards + quiz) = ~100-150 sequential calls.
NEW approach: batch all concepts together, ceil(N/10) calls per material type.

Fast-path mode (fast_path=True in state):
  - Takes top 8 concepts by importance
  - Generates 1 surface flashcard per concept (1 batch LLM call)
  - No quiz questions
  - Used when first rendering the dashboard

Deep-path mode (fast_path=False, default):
  - All concepts, full flashcard count per importance
  - Quiz questions for core + supporting
  - Overwrites fast-path flashcards with complete set
"""
import asyncio
import logging
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
    BATCH_FLASHCARD_SYSTEM,
    BATCH_FLASHCARD_USER,
    BATCH_QUIZ_SYSTEM,
    BATCH_QUIZ_USER,
)
from app.config import get_settings

logger = logging.getLogger(__name__)

_CARDS_BY_IMPORTANCE = {"core": 3, "supporting": 2, "supplemental": 1}
_QUIZ_BY_IMPORTANCE  = {"core": 2, "supporting": 1, "supplemental": 0}

# Max concepts per batch LLM call (keeps prompts within token limits)
_BATCH_SIZE = 10


# ── Helpers ───────────────────────────────────────────────────────────────────

def _concept_block(concept: Concept, n_cards: int) -> str:
    """Format one concept entry for the batch flashcard / quiz prompt."""
    examples = "; ".join((concept.examples or [])[:2]) or "none"
    return (
        f"--- {concept.name} ({concept.importance}, {n_cards} card(s)) ---\n"
        f"Definition: {concept.definition[:300]}\n"
        f"Explanation: {(concept.explanation or '')[:200]}\n"
        f"Examples: {examples}\n"
        f"Evidence: {(concept.evidence_quote or '')[:200]}\n"
        f"Timestamp: {concept.timestamp_start or 0.0:.1f}s"
    )


def _concept_quiz_block(concept: Concept, n_questions: int) -> str:
    examples = "; ".join((concept.examples or [])[:2]) or "none"
    return (
        f"--- {concept.name} ({concept.importance}, {n_questions} question(s)) ---\n"
        f"Definition: {concept.definition[:300]}\n"
        f"Explanation: {(concept.explanation or '')[:200]}\n"
        f"Examples: {examples}\n"
        f"Evidence: {(concept.evidence_quote or '')[:200]}\n"
        f"Timestamp: {concept.timestamp_start or 0.0:.1f}s"
    )


async def _batch_generate_flashcards(
    concepts_with_counts: list[tuple[Concept, int]],
    llm: LLMClient,
) -> dict[str, list[GeneratedFlashcard]]:
    """
    Generate flashcards for a batch of concepts in a single LLM call.

    Returns {concept_name_lower: [GeneratedFlashcard, ...]}
    """
    if not concepts_with_counts:
        return {}

    concepts_block = "\n\n".join(
        _concept_block(c, n) for c, n in concepts_with_counts
    )
    response = await llm.extract_json(
        BATCH_FLASHCARD_SYSTEM,
        BATCH_FLASHCARD_USER.format(concepts_block=concepts_block),
    )

    out: dict[str, list[GeneratedFlashcard]] = {}
    results = response.get("results", [])
    if not isinstance(results, list):
        return out

    concept_map = {c.name.lower(): (c, n) for c, n in concepts_with_counts}

    for item in results:
        if not isinstance(item, dict):
            continue
        cname = str(item.get("concept_name", "")).strip().lower()
        concept_entry = concept_map.get(cname)
        if not concept_entry:
            continue
        concept, n_cards = concept_entry
        raw_cards = item.get("cards", [])
        if not isinstance(raw_cards, list):
            continue

        cards: list[GeneratedFlashcard] = []
        for c in raw_cards[:n_cards]:
            if not isinstance(c, dict):
                continue
            front = str(c.get("front", "")).strip()
            back  = str(c.get("back",  "")).strip()
            if not front or not back:
                continue
            try:
                qt = QuestionType(c.get("question_type", "surface"))
            except ValueError:
                qt = QuestionType.SURFACE
            cards.append(GeneratedFlashcard(
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
        if cards:
            out[cname] = cards

    return out


async def _batch_generate_quiz(
    concepts_with_counts: list[tuple[Concept, int]],
    llm: LLMClient,
) -> dict[str, list[GeneratedQuizQuestion]]:
    """
    Generate quiz questions for a batch of concepts in a single LLM call.

    Returns {concept_name_lower: [GeneratedQuizQuestion, ...]}
    """
    if not concepts_with_counts:
        return {}

    concepts_block = "\n\n".join(
        _concept_quiz_block(c, n) for c, n in concepts_with_counts
    )
    response = await llm.extract_json(
        BATCH_QUIZ_SYSTEM,
        BATCH_QUIZ_USER.format(concepts_block=concepts_block),
    )

    out: dict[str, list[GeneratedQuizQuestion]] = {}
    results = response.get("results", [])
    if not isinstance(results, list):
        return out

    concept_map = {c.name.lower(): (c, n) for c, n in concepts_with_counts}

    for item in results:
        if not isinstance(item, dict):
            continue
        cname = str(item.get("concept_name", "")).strip().lower()
        entry = concept_map.get(cname)
        if not entry:
            continue
        concept, n_questions = entry
        raw_qs = item.get("questions", [])
        if not isinstance(raw_qs, list):
            continue

        qs: list[GeneratedQuizQuestion] = []
        for q in raw_qs[:n_questions]:
            if not isinstance(q, dict):
                continue
            question_text = str(q.get("question_text", "")).strip()
            correct       = str(q.get("correct_answer", "")).strip()
            if not question_text or not correct:
                continue
            options = q.get("options")
            if options is not None and not isinstance(options, list):
                options = None
            qs.append(GeneratedQuizQuestion(
                concept_id=concept.id,
                question_text=question_text,
                question_type=str(q.get("question_type", "multiple_choice")),
                options=options,
                correct_answer=correct,
                explanation=str(q.get("explanation", "")).strip(),
                evidence_quote=str(q.get("evidence_quote", concept.evidence_quote or "")).strip(),
                timestamp_start=concept.timestamp_start or 0.0,
                difficulty=str(q.get("difficulty", "medium")),
            ))
        if qs:
            out[cname] = qs

    return out


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


# ── Agent ─────────────────────────────────────────────────────────────────────

class ExamCoachAgent(BaseAgent):
    """
    Generates flashcards and quiz questions for all concepts.

    State inputs:
      fast_path (bool, default False):
        True  → top-8 concepts, 1 surface card each, no quiz (fast dashboard load)
        False → all concepts, full counts, + quiz questions (deep background pass)

    State outputs:
      flashcards_ready, flashcard_count, quiz_count
    """

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        lecture_id: str = state.get("lecture_id", "")
        fast_path:  bool = bool(state.get("fast_path", False))
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

                # ── Fast path: top-8, 1 surface card each ─────────────────────
                if fast_path:
                    return await self._fast_path(db, lecture_id, concepts, llm)

                # ── Deep path: full set, batched ───────────────────────────────
                return await self._deep_path(db, lecture_id, concepts, llm)

            except Exception as exc:
                logger.error("[exam_coach] Failed: %s", exc, exc_info=True)
                await db.rollback()
                return {"flashcards_ready": False, "error": str(exc)}

    # ── Fast path ─────────────────────────────────────────────────────────────

    async def _fast_path(
        self,
        db: AsyncSession,
        lecture_id: str,
        concepts: list[Concept],
        llm: LLMClient,
    ) -> dict[str, Any]:
        """Top-8 concepts, 1 surface flashcard each, 1 batch LLM call."""
        # Sort by importance then exam_likelihood; take top 8
        order = {"core": 3, "supporting": 2, "supplemental": 1}
        top8 = sorted(
            concepts,
            key=lambda c: (-order.get(c.importance, 0), -(c.exam_likelihood or 0)),
        )[:8]

        # Clear existing fast-path cards (idempotent re-runs)
        await db.execute(sa_delete(Flashcard).where(Flashcard.lecture_id == lecture_id))
        await db.execute(sa_delete(UserMastery).where(UserMastery.lecture_id == lecture_id))

        total_cards = 0

        if llm.available:
            pairs = [(c, 1) for c in top8]
            flashcard_map = await _batch_generate_flashcards(pairs, llm)
        else:
            flashcard_map = {}

        for concept in top8:
            cards = flashcard_map.get(concept.name.lower())
            if cards:
                gf = cards[0]
                db.add(Flashcard(
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
                ))
                total_cards += 1
            else:
                # Fallback surface card from definition
                db.add(Flashcard(
                    lecture_id=lecture_id,
                    concept_id=concept.id,
                    front=f"What is {concept.name}?",
                    back=concept.definition,
                    difficulty="easy",
                    tags=concept.tags or [],
                    question_type=QuestionType.SURFACE.value,
                    timestamp_start=concept.timestamp_start or 0.0,
                    timestamp_end=concept.timestamp_end,
                    exam_likelihood=concept.exam_likelihood,
                    evidence_quote=concept.evidence_quote or "",
                ))
                total_cards += 1

        await db.flush()

        # Initialize mastery records
        fc_ids = [row[0] for row in (await db.execute(
            select(Flashcard.id).where(Flashcard.lecture_id == lecture_id)
        )).fetchall()]
        for fid in fc_ids:
            db.add(UserMastery(
                lecture_id=lecture_id, flashcard_id=fid,
                mastery_level="unseen", confidence="not_started",
                attempts=0, correct_count=0, ease_factor=2.5,
                next_review_interval_days=1,
            ))
        for c in top8:
            db.add(UserMastery(
                lecture_id=lecture_id, concept_id=c.id,
                mastery_level="unseen", confidence="not_started",
                attempts=0, correct_count=0, ease_factor=2.5,
                next_review_interval_days=1,
            ))

        await db.commit()
        logger.info("[exam_coach] Fast path: %d flashcards for lecture %s", total_cards, lecture_id)
        return {"flashcards_ready": True, "flashcard_count": total_cards, "quiz_count": 0}

    # ── Deep path ─────────────────────────────────────────────────────────────

    async def _deep_path(
        self,
        db: AsyncSession,
        lecture_id: str,
        concepts: list[Concept],
        llm: LLMClient,
    ) -> dict[str, Any]:
        """
        Full flashcard set (2-3 per concept) + quiz questions, batched.
        Replaces the fast-path flashcard set entirely.
        """
        # Wipe everything and regenerate completely
        await db.execute(sa_delete(Flashcard).where(Flashcard.lecture_id == lecture_id))
        await db.execute(sa_delete(QuizQuestion).where(QuizQuestion.lecture_id == lecture_id))
        await db.execute(sa_delete(UserMastery).where(UserMastery.lecture_id == lecture_id))

        # Build (concept, n_cards) and (concept, n_quiz) lists
        flash_pairs: list[tuple[Concept, int]] = [
            (c, _CARDS_BY_IMPORTANCE.get(c.importance, 1)) for c in concepts
        ]
        quiz_pairs: list[tuple[Concept, int]] = [
            (c, n) for c in concepts
            if (n := _QUIZ_BY_IMPORTANCE.get(c.importance, 0)) > 0
        ]

        # ── Batch flashcard + quiz generation — ALL batches run in parallel ────
        async def _run_all_flash_batches() -> dict[str, list[GeneratedFlashcard]]:
            if not llm.available:
                return {}
            results = await asyncio.gather(
                *[_batch_generate_flashcards(list(b), llm) for b in _chunks(flash_pairs, _BATCH_SIZE)],
                return_exceptions=True,
            )
            merged: dict[str, list[GeneratedFlashcard]] = {}
            for r in results:
                if isinstance(r, dict):
                    merged.update(r)
            return merged

        async def _run_all_quiz_batches() -> dict[str, list[GeneratedQuizQuestion]]:
            if not llm.available or not quiz_pairs:
                return {}
            results = await asyncio.gather(
                *[_batch_generate_quiz(list(b), llm) for b in _chunks(quiz_pairs, _BATCH_SIZE)],
                return_exceptions=True,
            )
            merged: dict[str, list[GeneratedQuizQuestion]] = {}
            for r in results:
                if isinstance(r, dict):
                    merged.update(r)
            return merged

        # Flash and quiz run concurrently; within each, all batches run concurrently
        all_flashcard_map, all_quiz_map = await asyncio.gather(
            _run_all_flash_batches(),
            _run_all_quiz_batches(),
        )

        # ── Persist flashcards ────────────────────────────────────────────────
        total_cards = 0
        for concept, n_cards in flash_pairs:
            cards = all_flashcard_map.get(concept.name.lower())
            if cards:
                for gf in cards:
                    db.add(Flashcard(
                        lecture_id=lecture_id, concept_id=concept.id,
                        front=gf.front, back=gf.back, hint=gf.hint,
                        difficulty=gf.difficulty, tags=concept.tags or [],
                        question_type=gf.question_type.value,
                        timestamp_start=gf.timestamp_start, timestamp_end=gf.timestamp_end,
                        time_spent_seconds=concept.time_spent_seconds,
                        exam_likelihood=concept.exam_likelihood,
                        evidence_quote=gf.evidence_quote,
                    ))
                    total_cards += 1
            else:
                # Fallback surface card
                db.add(Flashcard(
                    lecture_id=lecture_id, concept_id=concept.id,
                    front=f"What is {concept.name}?", back=concept.definition,
                    difficulty="easy", tags=concept.tags or [],
                    question_type=QuestionType.SURFACE.value,
                    timestamp_start=concept.timestamp_start or 0.0,
                    timestamp_end=concept.timestamp_end,
                    exam_likelihood=concept.exam_likelihood,
                    evidence_quote=concept.evidence_quote or "",
                ))
                total_cards += 1

        # ── Persist quiz questions ────────────────────────────────────────────
        total_quiz = 0
        for concept, _ in quiz_pairs:
            qs = all_quiz_map.get(concept.name.lower(), [])
            for gq in qs:
                db.add(QuizQuestion(
                    lecture_id=lecture_id, concept_id=concept.id,
                    question_text=gq.question_text, question_type=gq.question_type,
                    options=gq.options, correct_answer=gq.correct_answer,
                    explanation=gq.explanation, difficulty=gq.difficulty,
                    timestamp_start=gq.timestamp_start,
                    evidence_quote=gq.evidence_quote,
                ))
                total_quiz += 1

        await db.flush()

        # ── Initialize mastery records ────────────────────────────────────────
        fc_ids = [row[0] for row in (await db.execute(
            select(Flashcard.id).where(Flashcard.lecture_id == lecture_id)
        )).fetchall()]
        for fid in fc_ids:
            db.add(UserMastery(
                lecture_id=lecture_id, flashcard_id=fid,
                mastery_level="unseen", confidence="not_started",
                attempts=0, correct_count=0, ease_factor=2.5,
                next_review_interval_days=1,
            ))
        for concept in concepts:
            db.add(UserMastery(
                lecture_id=lecture_id, concept_id=concept.id,
                mastery_level="unseen", confidence="not_started",
                attempts=0, correct_count=0, ease_factor=2.5,
                next_review_interval_days=1,
            ))

        await db.commit()
        logger.info(
            "[exam_coach] Deep path: %d flashcards, %d quiz qs for lecture %s",
            total_cards, total_quiz, lecture_id,
        )
        return {
            "flashcards_ready": True,
            "flashcard_count": total_cards,
            "quiz_count": total_quiz,
        }


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _load_concepts(db: AsyncSession, lecture_id: str) -> list[Concept]:
    result = await db.execute(
        select(Concept)
        .where(Concept.lecture_id == lecture_id)
        .order_by(Concept.exam_likelihood.desc())
    )
    return list(result.scalars().all())
