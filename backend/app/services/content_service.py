from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.summary import Summary
from app.models.concept import Concept
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
)


async def get_summary(
    db: AsyncSession, lecture_id: str, summary_type: str = "standard"
) -> Summary | None:
    result = await db.execute(
        select(Summary).where(
            Summary.lecture_id == lecture_id,
            Summary.summary_type == summary_type,
        )
    )
    return result.scalar_one_or_none()


async def get_concepts(db: AsyncSession, lecture_id: str) -> list[Concept]:
    result = await db.execute(
        select(Concept)
        .where(Concept.lecture_id == lecture_id)
        .order_by(Concept.importance.desc())
    )
    return list(result.scalars().all())


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


async def get_quiz_questions(db: AsyncSession, lecture_id: str) -> list[QuizQuestion]:
    result = await db.execute(
        select(QuizQuestion).where(QuizQuestion.lecture_id == lecture_id)
    )
    return list(result.scalars().all())


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
