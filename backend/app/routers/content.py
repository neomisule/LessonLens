from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.content import (
    SummaryRead,
    ConceptRead,
    FlashcardRead,
    FlashcardSessionSubmit,
    QuizQuestionRead,
    MasteryStatsRead,
    MindMapRead,
    SearchQuerySchema,
    SearchResultRead,
)
import app.services.content_service as svc
from app.vector import search as vector_search

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/lectures/{lecture_id}/summary", response_model=SummaryRead)
async def get_summary(
    lecture_id: str,
    summary_type: str = Query(default="standard", pattern="^(brief|standard|detailed)$"),
    db: AsyncSession = Depends(get_db),
):
    summary = await svc.get_summary(db, lecture_id, summary_type)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not yet generated")
    return summary


@router.get("/lectures/{lecture_id}/concepts", response_model=list[ConceptRead])
async def get_concepts(lecture_id: str, db: AsyncSession = Depends(get_db)):
    return await svc.get_concepts(db, lecture_id)


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


@router.get("/lectures/{lecture_id}/quiz", response_model=list[QuizQuestionRead])
async def get_quiz(lecture_id: str, db: AsyncSession = Depends(get_db)):
    return await svc.get_quiz_questions(db, lecture_id)


@router.get("/lectures/{lecture_id}/mastery", response_model=MasteryStatsRead)
async def get_mastery(lecture_id: str, db: AsyncSession = Depends(get_db)):
    return await svc.get_mastery_stats(db, lecture_id)


@router.get("/lectures/{lecture_id}/mindmap", response_model=MindMapRead)
async def get_mindmap(lecture_id: str, db: AsyncSession = Depends(get_db)):
    return await svc.get_mindmap(db, lecture_id)


@router.post("/search/", response_model=list[SearchResultRead])
async def search(payload: SearchQuerySchema, db: AsyncSession = Depends(get_db)):
    return await vector_search.search(db, payload)
