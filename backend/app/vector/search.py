"""Vector search functions for LectureLens.

All public functions:
  search()           — semantic search over SemanticSegment embeddings
  concept_search()   — semantic search over Concept embeddings
  related_moments()  — find segments similar to a given segment_id
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.concept import Concept
from app.models.lecture import Lecture
from app.models.transcript import SemanticSegment
from app.schemas.search import (
    SearchQuerySchema,
    SearchResultRead,
    ConceptSearchResult,
)
from app.vector.store import create_embedding


def _confidence_tier(similarity: float) -> str:
    if similarity >= 0.85:
        return "high"
    if similarity >= 0.70:
        return "good"
    if similarity >= 0.50:
        return "partial"
    return "weak"


async def search(
    db: AsyncSession,
    query: SearchQuerySchema,
) -> list[SearchResultRead]:
    """
    Perform cosine-similarity vector search over semantic segments.

    Joins with Lecture to return title + subject context.
    Optional filters: lecture_id, subject_id.
    Returns up to `query.limit` results ordered by descending similarity.
    """
    embedding = await create_embedding(query.query)

    similarity_expr = (
        1 - SemanticSegment.embedding.cosine_distance(embedding)
    ).label("similarity")

    stmt = (
        select(SemanticSegment, Lecture, similarity_expr)
        .join(Lecture, Lecture.id == SemanticSegment.lecture_id)
        .where(SemanticSegment.embedding.is_not(None))
        .order_by(SemanticSegment.embedding.cosine_distance(embedding))
        .limit(query.limit)
    )

    if query.lecture_id:
        stmt = stmt.where(SemanticSegment.lecture_id == query.lecture_id)
    elif query.subject_id:
        stmt = stmt.where(Lecture.subject_id == query.subject_id)

    result = await db.execute(stmt)
    rows   = result.all()

    return [
        SearchResultRead(
            segment_id=row.SemanticSegment.id,
            lecture_id=row.SemanticSegment.lecture_id,
            lecture_title=row.Lecture.title or "Untitled",
            content=row.SemanticSegment.content,
            similarity=round(float(row.similarity), 4),
            confidence_tier=_confidence_tier(float(row.similarity)),
            timestamp_start=row.SemanticSegment.timestamp_start,
            timestamp_end=row.SemanticSegment.timestamp_end,
            topic_label=row.SemanticSegment.topic_label,
        )
        for row in rows
    ]


async def concept_search(
    db: AsyncSession,
    query_text: str,
    subject_id: str | None = None,
    lecture_id: str | None = None,
    limit: int = 10,
) -> list[ConceptSearchResult]:
    """
    Semantic search over Concept embeddings — returns concept-level matches.
    Useful for finding which concepts relate to a user query.
    """
    embedding = await create_embedding(query_text)

    similarity_expr = (
        1 - Concept.embedding.cosine_distance(embedding)
    ).label("similarity")

    stmt = (
        select(Concept, Lecture, similarity_expr)
        .join(Lecture, Lecture.id == Concept.lecture_id)
        .where(Concept.embedding.is_not(None))
        .order_by(Concept.embedding.cosine_distance(embedding))
        .limit(limit)
    )

    if lecture_id:
        stmt = stmt.where(Concept.lecture_id == lecture_id)
    elif subject_id:
        stmt = stmt.where(Lecture.subject_id == subject_id)

    result = await db.execute(stmt)
    rows   = result.all()

    return [
        ConceptSearchResult(
            concept_id=row.Concept.id,
            lecture_id=row.Concept.lecture_id,
            lecture_title=row.Lecture.title or "Untitled",
            name=row.Concept.name,
            definition=row.Concept.definition,
            importance=row.Concept.importance,
            exam_likelihood=row.Concept.exam_likelihood,
            similarity=round(float(row.similarity), 4),
            confidence_tier=_confidence_tier(float(row.similarity)),
            timestamp_start=row.Concept.timestamp_start,
            evidence_quote=row.Concept.evidence_quote,
        )
        for row in rows
    ]


async def related_moments(
    db: AsyncSession,
    segment_id: str,
    limit: int = 5,
    same_lecture_only: bool = False,
) -> list[SearchResultRead]:
    """
    Find segments semantically similar to the given segment_id.
    Excludes the source segment from results.
    """
    # Load source embedding
    src_result = await db.execute(
        select(SemanticSegment).where(SemanticSegment.id == segment_id)
    )
    source = src_result.scalar_one_or_none()
    if source is None or source.embedding is None:
        return []

    embedding = source.embedding

    similarity_expr = (
        1 - SemanticSegment.embedding.cosine_distance(embedding)
    ).label("similarity")

    stmt = (
        select(SemanticSegment, Lecture, similarity_expr)
        .join(Lecture, Lecture.id == SemanticSegment.lecture_id)
        .where(SemanticSegment.embedding.is_not(None))
        .where(SemanticSegment.id != segment_id)
        .order_by(SemanticSegment.embedding.cosine_distance(embedding))
        .limit(limit)
    )

    if same_lecture_only:
        stmt = stmt.where(SemanticSegment.lecture_id == source.lecture_id)

    result = await db.execute(stmt)
    rows   = result.all()

    return [
        SearchResultRead(
            segment_id=row.SemanticSegment.id,
            lecture_id=row.SemanticSegment.lecture_id,
            lecture_title=row.Lecture.title or "Untitled",
            content=row.SemanticSegment.content,
            similarity=round(float(row.similarity), 4),
            confidence_tier=_confidence_tier(float(row.similarity)),
            timestamp_start=row.SemanticSegment.timestamp_start,
            timestamp_end=row.SemanticSegment.timestamp_end,
            topic_label=row.SemanticSegment.topic_label,
        )
        for row in rows
    ]
