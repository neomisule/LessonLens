"""Pydantic schemas for Subject-level intelligence endpoints."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


# ── Subject Concept (canonical cross-lecture concept) ─────────────────────────

class SubjectConceptRead(BaseModel):
    id: str
    name: str
    cluster_label: str
    frequency: int                   # number of lectures it appears in
    is_recurring: bool
    is_prerequisite: bool
    importance: str
    avg_exam_likelihood: float
    avg_mastery: float               # 0.0 = not started, 1.0 = mastered
    lecture_ids: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ── Subject Graph (for visualization) ─────────────────────────────────────────

class GraphNode(BaseModel):
    """Unified node for the subject-level graph visualization."""
    id: str
    kind: str               # "lecture" | "concept"
    label: str
    importance: str = "supporting"
    is_recurring: bool = False
    is_prerequisite: bool = False
    avg_mastery: float = 0.0
    exam_likelihood: float = 0.5
    lecture_id: str | None = None    # set when kind="concept"
    timestamp_start: float | None = None
    color: str = "#6B7280"


class GraphEdge(BaseModel):
    id: str
    source: str             # node id
    target: str             # node id
    kind: str               # "belongs_to" | "prerequisite" | "recurring" | "related"
    label: str | None = None


class SubjectGraphRead(BaseModel):
    subject_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    lecture_count: int
    concept_count: int
    recurring_count: int
    weak_topic_count: int   # avg_mastery < 0.3


# ── Recurring Concepts ────────────────────────────────────────────────────────

class RecurringConceptRead(BaseModel):
    id: str
    name: str
    frequency: int
    lecture_ids: list[str]
    avg_exam_likelihood: float
    avg_mastery: float
    importance: str


# ── Prerequisite Chain ────────────────────────────────────────────────────────

class PrerequisiteChainNode(BaseModel):
    concept_name: str
    lecture_id: str
    lecture_title: str
    timestamp_start: float | None
    is_mastered: bool


class PrerequisiteChainRead(BaseModel):
    concept_name: str
    chain: list[PrerequisiteChainNode]  # ordered prerequisite → concept
