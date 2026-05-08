from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript import SemanticSegment
from app.schemas.content import SearchQuerySchema, SearchResultRead
from app.vector.store import create_embedding


async def search(
    db: AsyncSession,
    query: SearchQuerySchema,
) -> list[SearchResultRead]:
    """
    Perform cosine-similarity vector search over semantic segments.

    Returns up to `query.limit` results ordered by descending similarity.
    """
    embedding = await create_embedding(query.query)

    stmt = (
        select(
            SemanticSegment,
            (1 - SemanticSegment.embedding.cosine_distance(embedding)).label("similarity"),
        )
        .where(SemanticSegment.embedding.is_not(None))
        .order_by(SemanticSegment.embedding.cosine_distance(embedding))
        .limit(query.limit)
    )

    # Optional scope filters
    if query.lecture_id:
        stmt = stmt.where(SemanticSegment.lecture_id == query.lecture_id)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        SearchResultRead(
            segment_id=row.SemanticSegment.id,
            lecture_id=row.SemanticSegment.lecture_id,
            content=row.SemanticSegment.content,
            similarity=float(row.similarity),
            timestamp_start=row.SemanticSegment.timestamp_start,
            timestamp_end=row.SemanticSegment.timestamp_end,
        )
        for row in rows
    ]
