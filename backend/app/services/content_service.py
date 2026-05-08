from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.summary import Summary
from app.models.concept import Concept
from app.models.chapter import Chapter
from app.models.flashcard import Flashcard
from app.models.quiz import QuizQuestion
from app.models.mastery import UserMastery
from app.models.mindmap import MindMapNode, MindMapEdge
from app.schemas.content import (
    MasteryStatsRead,
    MindMapRead,
    MindMapNodeRead,
    MindMapEdgeRead,
    FlashcardSessionSubmit,
    ChapterRead,
    ConceptRead,
    SummaryRead,
    LearnModeRead,
)


# ── Summary ───────────────────────────────────────────────────────────────────

async def get_summary(
    db: AsyncSession, lecture_id: str, level: str = "standard"
) -> Summary | None:
    result = await db.execute(
        select(Summary).where(
            Summary.lecture_id == lecture_id,
            Summary.level == level,
        )
    )
    return result.scalar_one_or_none()


async def get_all_summaries(db: AsyncSession, lecture_id: str) -> list[Summary]:
    result = await db.execute(
        select(Summary)
        .where(Summary.lecture_id == lecture_id)
        .order_by(Summary.level)
    )
    return list(result.scalars().all())


# ── Chapters ──────────────────────────────────────────────────────────────────

async def get_chapters(db: AsyncSession, lecture_id: str) -> list[Chapter]:
    result = await db.execute(
        select(Chapter)
        .where(Chapter.lecture_id == lecture_id)
        .order_by(Chapter.sequence_index)
    )
    return list(result.scalars().all())


# ── Concepts ──────────────────────────────────────────────────────────────────

async def get_concepts(db: AsyncSession, lecture_id: str) -> list[Concept]:
    result = await db.execute(
        select(Concept)
        .where(Concept.lecture_id == lecture_id)
        .order_by(Concept.exam_likelihood.desc(), Concept.timestamp_start)
    )
    return list(result.scalars().all())


# ── Learn Mode aggregate ──────────────────────────────────────────────────────

async def get_learn_mode(db: AsyncSession, lecture_id: str) -> LearnModeRead:
    """
    Return all Learn Mode data for a lecture in a single aggregated response.
    Includes summaries (all levels), chapters, and enriched concepts.
    """
    summaries_orm = await get_all_summaries(db, lecture_id)
    chapters_orm = await get_chapters(db, lecture_id)
    concepts_orm = await get_concepts(db, lecture_id)

    return LearnModeRead(
        summaries=[SummaryRead.from_orm_sections(s) for s in summaries_orm],
        chapters=[ChapterRead.model_validate(ch) for ch in chapters_orm],
        concepts=[ConceptRead.model_validate(c) for c in concepts_orm],
    )


# ── Flashcards ────────────────────────────────────────────────────────────────

async def get_flashcards(db: AsyncSession, lecture_id: str) -> list[Flashcard]:
    result = await db.execute(
        select(Flashcard).where(Flashcard.lecture_id == lecture_id)
    )
    return list(result.scalars().all())


async def submit_flashcard_session(
    db: AsyncSession, lecture_id: str, payload: FlashcardSessionSubmit
) -> dict:
    """Record flashcard session results and update mastery records."""
    updated = 0
    for item in payload.items:
        result = await db.execute(
            select(UserMastery).where(
                UserMastery.lecture_id == lecture_id,
                UserMastery.flashcard_id == item.flashcard_id,
            )
        )
        mastery = result.scalar_one_or_none()

        if mastery is None:
            mastery = UserMastery(
                lecture_id=lecture_id,
                flashcard_id=item.flashcard_id,
                mastery_level="learning",
                attempts=0,
                correct_count=0,
            )
            db.add(mastery)

        mastery.attempts += 1
        if item.result == "correct":
            mastery.correct_count += 1

        # Simple mastery progression
        ratio = mastery.correct_count / mastery.attempts if mastery.attempts else 0
        if mastery.attempts >= 3 and ratio >= 0.9:
            mastery.mastery_level = "mastered"
        elif mastery.attempts >= 2 and ratio >= 0.6:
            mastery.mastery_level = "familiar"
        else:
            mastery.mastery_level = "learning"

        updated += 1

    await db.commit()
    return {"updated": updated}


# ── Quiz ──────────────────────────────────────────────────────────────────────

async def get_quiz_questions(db: AsyncSession, lecture_id: str) -> list[QuizQuestion]:
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.lecture_id == lecture_id)
    )
    return list(result.scalars().all())


# ── Mastery ───────────────────────────────────────────────────────────────────

async def get_mastery_stats(db: AsyncSession, lecture_id: str) -> MasteryStatsRead:
    result = await db.execute(
        select(UserMastery).where(UserMastery.lecture_id == lecture_id)
    )
    records = list(result.scalars().all())

    counts: dict[str, int] = {"unseen": 0, "learning": 0, "familiar": 0, "mastered": 0}
    for r in records:
        counts[r.mastery_level] = counts.get(r.mastery_level, 0) + 1

    total = sum(counts.values())
    mastered = counts["mastered"]
    mastery_pct = round((mastered / total * 100) if total else 0, 1)

    return MasteryStatsRead(
        total=total,
        unseen=counts["unseen"],
        learning=counts["learning"],
        familiar=counts["familiar"],
        mastered=mastered,
        mastery_percentage=mastery_pct,
    )


# ── Mind Map ──────────────────────────────────────────────────────────────────

async def get_mindmap(db: AsyncSession, lecture_id: str) -> MindMapRead:
    nodes_result = await db.execute(
        select(MindMapNode).where(MindMapNode.lecture_id == lecture_id)
    )
    edges_result = await db.execute(
        select(MindMapEdge).where(MindMapEdge.lecture_id == lecture_id)
    )
    nodes = [MindMapNodeRead.model_validate(n) for n in nodes_result.scalars().all()]
    edges = [MindMapEdgeRead.model_validate(e) for e in edges_result.scalars().all()]
    return MindMapRead(nodes=nodes, edges=edges)
