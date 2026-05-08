"""Semantic Search API router.

Base: /api/v1/search

Endpoints:
  POST /search/             → combined segment + concept search
  GET  /search/related/{id} → related moments for a segment
  POST /search/concepts/    → concept-only semantic search
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.search import (
    SearchQuerySchema,
    SearchResultRead,
    ConceptSearchResult,
    RelatedMomentsQuery,
    CombinedSearchResponse,
)
from app.services import search_service
from app.vector import search as vs

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=CombinedSearchResponse)
async def semantic_search(
    payload: SearchQuerySchema,
    db: AsyncSession = Depends(get_db),
):
    """
    Semantic search over lecture transcript segments.

    - Set lecture_id to scope to a single lecture.
    - Set subject_id to search across all lectures in a subject.
    - Set include_concepts=true to also search concept embeddings.
    - confidence_tier: "high" (≥0.85) | "good" (≥0.70) | "partial" (≥0.50) | "weak"
    """
    try:
        return await search_service.semantic_search(db, payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc


@router.post("/concepts/", response_model=list[ConceptSearchResult])
async def concept_search(
    payload: SearchQuerySchema,
    db: AsyncSession = Depends(get_db),
):
    """Semantic search over concept embeddings — returns concept-level matches."""
    try:
        return await vs.concept_search(
            db,
            query_text=payload.query,
            subject_id=payload.subject_id,
            lecture_id=payload.lecture_id,
            limit=payload.limit,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Concept search failed: {exc}") from exc


@router.get("/related/{segment_id}", response_model=list[SearchResultRead])
async def related_moments(
    segment_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    same_lecture_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """
    Find transcript segments semantically similar to the given segment.
    Use same_lecture_only=true to restrict to the same lecture.
    """
    try:
        return await search_service.get_related_moments(
            db,
            RelatedMomentsQuery(
                segment_id=segment_id,
                limit=limit,
                same_lecture_only=same_lecture_only,
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Related moments failed: {exc}") from exc
