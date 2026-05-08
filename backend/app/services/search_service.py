"""Search service — thin orchestration layer over vector search functions."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.search import (
    SearchQuerySchema,
    SearchResultRead,
    ConceptSearchResult,
    RelatedMomentsQuery,
    CombinedSearchResponse,
)
from app.vector import search as vs


async def semantic_search(
    db: AsyncSession,
    query: SearchQuerySchema,
) -> CombinedSearchResponse:
    """
    Run segment search (always) + optional concept search.
    Returns a unified response with both result sets.
    """
    segments = await vs.search(db, query)

    concepts: list[ConceptSearchResult] = []
    if query.include_concepts:
        concepts = await vs.concept_search(
            db,
            query_text=query.query,
            subject_id=query.subject_id,
            lecture_id=query.lecture_id,
            limit=min(query.limit, 5),
        )

    return CombinedSearchResponse(
        query=query.query,
        segments=segments,
        concepts=concepts,
        total_segments=len(segments),
        total_concepts=len(concepts),
    )


async def get_related_moments(
    db: AsyncSession,
    req: RelatedMomentsQuery,
) -> list[SearchResultRead]:
    return await vs.related_moments(
        db,
        segment_id=req.segment_id,
        limit=req.limit,
        same_lecture_only=req.same_lecture_only,
    )
