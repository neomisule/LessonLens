from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.content import (
    SummaryRead,
    ChapterRead,
    ConceptRead,
    LearnModeRead,
    FlashcardRead,
    FlashcardSessionSubmit,
    QuizQuestionRead,
    MasteryStatsRead,
    MindMapRead,
)
from app.schemas.search import SearchQuerySchema, CombinedSearchResponse
import app.services.content_service as svc
import app.services.search_service as search_svc

router = APIRouter(prefix="/content", tags=["content"])


# ── Learn Mode (aggregate) ────────────────────────────────────────────────────

@router.get("/lectures/{lecture_id}/learn", response_model=LearnModeRead)
async def get_learn_mode(lecture_id: str, db: AsyncSession = Depends(get_db)):
    """Return all Learn Mode data: summaries, chapters, and enriched concepts."""
    data = await svc.get_learn_mode(db, lecture_id)
    if not data.summaries and not data.chapters and not data.concepts:
        raise HTTPException(status_code=404, detail="Learn Mode content not yet generated")
    return data


# ── Summary ───────────────────────────────────────────────────────────────────

@router.get("/lectures/{lecture_id}/summary", response_model=SummaryRead)
async def get_summary(
    lecture_id: str,
    level: str = Query(default="standard", pattern="^(brief|standard|detailed)$"),
    db: AsyncSession = Depends(get_db),
):
    summary = await svc.get_summary(db, lecture_id, level)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not yet generated")
    return SummaryRead.from_orm_sections(summary)


@router.get("/lectures/{lecture_id}/summaries", response_model=list[SummaryRead])
async def get_all_summaries(lecture_id: str, db: AsyncSession = Depends(get_db)):
    """Return all three summary levels for a lecture."""
    summaries = await svc.get_all_summaries(db, lecture_id)
    if not summaries:
        raise HTTPException(status_code=404, detail="Summaries not yet generated")
    return [SummaryRead.from_orm_sections(s) for s in summaries]


# ── Chapters ──────────────────────────────────────────────────────────────────

@router.get("/lectures/{lecture_id}/chapters", response_model=list[ChapterRead])
async def get_chapters(lecture_id: str, db: AsyncSession = Depends(get_db)):
    chapters = await svc.get_chapters(db, lecture_id)
    if not chapters:
        raise HTTPException(status_code=404, detail="Chapters not yet generated")
    return chapters


# ── Concepts ──────────────────────────────────────────────────────────────────

@router.get("/lectures/{lecture_id}/concepts", response_model=list[ConceptRead])
async def get_concepts(lecture_id: str, db: AsyncSession = Depends(get_db)):
    return await svc.get_concepts(db, lecture_id)


# ── Flashcards ────────────────────────────────────────────────────────────────

@router.get("/lectures/{lecture_id}/flashcards", response_model=list[FlashcardRead])
async def get_flashcards(lecture_id: str, db: AsyncSession = Depends(get_db)):
    return await svc.get_flashcards(db, lecture_id)


@router.post("/lectures/{lecture_id}/flashcards/session")
async def submit_flashcard_session(
    lecture_id: str,
    payload: FlashcardSessionSubmit,
    db: AsyncSession = Depends(get_db),
):
    return await svc.submit_flashcard_session(db, lecture_id, payload)


# ── Quiz ──────────────────────────────────────────────────────────────────────

@router.get("/lectures/{lecture_id}/quiz", response_model=list[QuizQuestionRead])
async def get_quiz(lecture_id: str, db: AsyncSession = Depends(get_db)):
    return await svc.get_quiz_questions(db, lecture_id)


# ── Mastery ───────────────────────────────────────────────────────────────────

@router.get("/lectures/{lecture_id}/mastery", response_model=MasteryStatsRead)
async def get_mastery(lecture_id: str, db: AsyncSession = Depends(get_db)):
    return await svc.get_mastery_stats(db, lecture_id)


# ── Mind Map ──────────────────────────────────────────────────────────────────

@router.get("/lectures/{lecture_id}/mindmap", response_model=MindMapRead)
async def get_mindmap(lecture_id: str, db: AsyncSession = Depends(get_db)):
    return await svc.get_mindmap(db, lecture_id)


# ── Search ────────────────────────────────────────────────────────────────────

@router.post("/search/", response_model=CombinedSearchResponse)
async def search(payload: SearchQuerySchema, db: AsyncSession = Depends(get_db)):
    """Semantic search — delegates to the /api/v1/search/ router for full features."""
    return await search_svc.semantic_search(db, payload)
