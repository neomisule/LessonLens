"""Pydantic schemas for Semantic Search endpoints."""
from __future__ import annotations
from pydantic import BaseModel, Field


class SearchQuerySchema(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    lecture_id: str | None = None
    subject_id: str | None = None
    limit: int = Field(default=10, ge=1, le=50)
    include_concepts: bool = Field(default=False, description="Also search concept embeddings")


class SearchResultRead(BaseModel):
    segment_id: str
    lecture_id: str
    lecture_title: str
    content: str
    similarity: float
    confidence_tier: str          # "high" | "good" | "partial" | "weak"
    timestamp_start: float | None
    timestamp_end: float | None
    topic_label: str | None = None


class ConceptSearchResult(BaseModel):
    concept_id: str
    lecture_id: str
    lecture_title: str
    name: str
    definition: str
    importance: str
    exam_likelihood: float
    similarity: float
    confidence_tier: str
    timestamp_start: float | None
    evidence_quote: str | None


class RelatedMomentsQuery(BaseModel):
    segment_id: str
    limit: int = Field(default=5, ge=1, le=20)
    same_lecture_only: bool = False


class CombinedSearchResponse(BaseModel):
    query: str
    segments: list[SearchResultRead]
    concepts: list[ConceptSearchResult]
    total_segments: int
    total_concepts: int
