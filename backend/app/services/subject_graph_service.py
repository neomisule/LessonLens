"""Subject-level intelligence service.

Reads SubjectConcept / SubjectConceptLink tables built by SubjectGraphAgent
and serves the shaped data the API and frontend need.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.subject_graph_agent import rebuild_subject_graph
from app.models.concept import Concept
from app.models.lecture import Lecture
from app.models.mastery import UserMastery
from app.models.subject_graph import SubjectConcept, SubjectConceptLink
from app.schemas.subject_graph import (
    GraphEdge,
    GraphNode,
    PrerequisiteChainNode,
    PrerequisiteChainRead,
    RecurringConceptRead,
    SubjectConceptRead,
    SubjectGraphRead,
)

logger = logging.getLogger(__name__)

_MASTERY_TO_SCORE = {"mastered": 1.0, "shaky": 0.5, "confused": 0.2, "not_started": 0.0}

# Mastery colors for graph overlay
def _mastery_color(avg_mastery: float) -> str:
    if avg_mastery >= 0.8: return "#10B981"   # emerald - mastered
    if avg_mastery >= 0.4: return "#F59E0B"   # amber - in progress
    if avg_mastery >  0.0: return "#EF4444"   # red - confused
    return "#6B7280"                           # gray - not started


# ── Ensure subject graph is built ────────────────────────────────────────────

async def ensure_graph(db: AsyncSession, subject_id: str) -> dict[str, Any]:
    """Rebuild graph if empty, otherwise return cached stats."""
    result = await db.execute(
        select(SubjectConcept).where(SubjectConcept.subject_id == subject_id).limit(1)
    )
    if result.scalar_one_or_none() is None:
        return await rebuild_subject_graph(db, subject_id)
    return {}


# ── Subject Graph for visualization ──────────────────────────────────────────

async def get_subject_graph(db: AsyncSession, subject_id: str) -> SubjectGraphRead:
    """
    Build a full graph for the subject:
      - One node per lecture
      - One node per SubjectConcept
      - Edges: concept→lecture (belongs_to), concept→concept (prerequisite / recurring)
    """
    await ensure_graph(db, subject_id)

    # Load lectures
    lec_result = await db.execute(
        select(Lecture)
        .where(Lecture.subject_id == subject_id)
        .where(Lecture.processing_status == "completed")
    )
    lectures = list(lec_result.scalars().all())
    lecture_map = {lec.id: lec for lec in lectures}

    # Load subject concepts + their links
    sc_result = await db.execute(
        select(SubjectConcept).where(SubjectConcept.subject_id == subject_id)
    )
    subject_concepts = list(sc_result.scalars().all())

    link_result = await db.execute(
        select(SubjectConceptLink).where(
            SubjectConceptLink.lecture_id.in_([lec.id for lec in lectures])
        )
    )
    links = list(link_result.scalars().all())

    # Build SubjectConcept → set of lecture_ids
    sc_lectures: dict[str, set[str]] = {}
    for link in links:
        sc_lectures.setdefault(link.subject_concept_id, set()).add(link.lecture_id)

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    edge_id = 0

    # Lecture nodes
    for lec in lectures:
        nodes.append(GraphNode(
            id=f"lecture:{lec.id}",
            kind="lecture",
            label=lec.title or "Lecture",
            color="#7C3AED",
            lecture_id=lec.id,
        ))

    # Concept nodes + edges to lectures
    recurring_count = 0
    weak_topic_count = 0
    for sc in subject_concepts:
        lec_ids = list(sc_lectures.get(sc.id, set()))
        color = _mastery_color(sc.avg_mastery)
        if sc.is_recurring:
            recurring_count += 1
        if sc.avg_mastery < 0.3:
            weak_topic_count += 1

        nodes.append(GraphNode(
            id=f"concept:{sc.id}",
            kind="concept",
            label=sc.name,
            importance=sc.importance,
            is_recurring=sc.is_recurring,
            is_prerequisite=sc.is_prerequisite,
            avg_mastery=sc.avg_mastery,
            exam_likelihood=sc.avg_exam_likelihood,
            color=color,
        ))

        # Edge: concept → each lecture it belongs to
        for lid in lec_ids:
            edge_id += 1
            edges.append(GraphEdge(
                id=f"e{edge_id}",
                source=f"concept:{sc.id}",
                target=f"lecture:{lid}",
                kind="belongs_to",
            ))

    # Recurring edges: link same-cluster nodes across lectures
    # Build cluster_label → list[sc_id]
    cluster_to_scs: dict[str, list[SubjectConcept]] = {}
    for sc in subject_concepts:
        cluster_to_scs.setdefault(sc.cluster_label, []).append(sc)

    # (Each subject has one SubjectConcept per cluster — no inter-sc edges needed
    # since they are already merged. Instead, add prerequisite edges.)

    # Load per-lecture Concept rows to extract prerequisites
    all_concept_result = await db.execute(
        select(Concept).where(Concept.lecture_id.in_([lec.id for lec in lectures]))
    )
    all_concepts = list(all_concept_result.scalars().all())

    # Build name → SubjectConcept fast lookup
    sc_by_cluster: dict[str, SubjectConcept] = {sc.cluster_label: sc for sc in subject_concepts}

    from app.agents.subject_graph_agent import _normalize
    for concept in all_concepts:
        for prereq_name in (concept.prerequisites or []):
            prereq_key = _normalize(prereq_name)
            prereq_sc  = sc_by_cluster.get(prereq_key)
            src_key    = _normalize(concept.name)
            src_sc     = sc_by_cluster.get(src_key)
            if prereq_sc and src_sc and prereq_sc.id != src_sc.id:
                edge_id += 1
                edges.append(GraphEdge(
                    id=f"e{edge_id}",
                    source=f"concept:{prereq_sc.id}",
                    target=f"concept:{src_sc.id}",
                    kind="prerequisite",
                    label="prerequisite of",
                ))

    return SubjectGraphRead(
        subject_id=subject_id,
        nodes=nodes,
        edges=edges,
        lecture_count=len(lectures),
        concept_count=len(subject_concepts),
        recurring_count=recurring_count,
        weak_topic_count=weak_topic_count,
    )


# ── Recurring concepts ────────────────────────────────────────────────────────

async def get_recurring_concepts(
    db: AsyncSession, subject_id: str
) -> list[RecurringConceptRead]:
    await ensure_graph(db, subject_id)

    result = await db.execute(
        select(SubjectConcept)
        .where(SubjectConcept.subject_id == subject_id)
        .where(SubjectConcept.is_recurring == True)  # noqa: E712
        .order_by(SubjectConcept.frequency.desc(), SubjectConcept.avg_exam_likelihood.desc())
    )
    scs = list(result.scalars().all())

    link_result = await db.execute(
        select(SubjectConceptLink).where(
            SubjectConceptLink.subject_concept_id.in_([sc.id for sc in scs])
        )
    )
    links_by_sc: dict[str, list[str]] = {}
    for link in link_result.scalars().all():
        links_by_sc.setdefault(link.subject_concept_id, []).append(link.lecture_id)

    return [
        RecurringConceptRead(
            id=sc.id,
            name=sc.name,
            frequency=sc.frequency,
            lecture_ids=list({lid for lid in links_by_sc.get(sc.id, [])}),
            avg_exam_likelihood=sc.avg_exam_likelihood,
            avg_mastery=sc.avg_mastery,
            importance=sc.importance,
        )
        for sc in scs
    ]


# ── Weak topics ───────────────────────────────────────────────────────────────

async def get_weak_topics(
    db: AsyncSession, subject_id: str, threshold: float = 0.3
) -> list[SubjectConceptRead]:
    """Return concepts with avg_mastery below threshold — need more study."""
    await ensure_graph(db, subject_id)

    result = await db.execute(
        select(SubjectConcept)
        .where(SubjectConcept.subject_id == subject_id)
        .where(SubjectConcept.avg_mastery < threshold)
        .order_by(SubjectConcept.avg_exam_likelihood.desc())
    )
    scs = list(result.scalars().all())

    link_result = await db.execute(
        select(SubjectConceptLink).where(
            SubjectConceptLink.subject_concept_id.in_([sc.id for sc in scs])
        )
    )
    links_by_sc: dict[str, list[str]] = {}
    for link in link_result.scalars().all():
        links_by_sc.setdefault(link.subject_concept_id, []).append(link.lecture_id)

    return [
        SubjectConceptRead(
            id=sc.id,
            name=sc.name,
            cluster_label=sc.cluster_label,
            frequency=sc.frequency,
            is_recurring=sc.is_recurring,
            is_prerequisite=sc.is_prerequisite,
            importance=sc.importance,
            avg_exam_likelihood=sc.avg_exam_likelihood,
            avg_mastery=sc.avg_mastery,
            lecture_ids=list({lid for lid in links_by_sc.get(sc.id, [])}),
        )
        for sc in scs
    ]


# ── Prerequisite chains ───────────────────────────────────────────────────────

async def get_prerequisite_chains(
    db: AsyncSession, subject_id: str
) -> list[PrerequisiteChainRead]:
    """
    Return concepts that ARE prerequisites and what they are prerequisites for.
    Enriches each node with lecture title and mastery state.
    """
    await ensure_graph(db, subject_id)

    # Load lectures for titles
    lec_result = await db.execute(
        select(Lecture).where(Lecture.subject_id == subject_id)
    )
    lecture_map = {lec.id: lec for lec in lec_result.scalars().all()}

    # Load all per-lecture concepts with prerequisites
    con_result = await db.execute(
        select(Concept).where(
            Concept.lecture_id.in_(list(lecture_map.keys()))
        )
    )
    all_concepts = list(con_result.scalars().all())

    # Load mastery
    mastery_result = await db.execute(
        select(UserMastery)
        .where(UserMastery.lecture_id.in_(list(lecture_map.keys())))
        .where(UserMastery.concept_id.is_not(None))
        .where(UserMastery.flashcard_id.is_(None))
    )
    mastery_map: dict[str, str] = {
        m.concept_id: m.confidence
        for m in mastery_result.scalars().all()
        if m.concept_id
    }

    # Build name+lecture → concept fast lookup
    concept_by_name_lecture: dict[tuple[str, str], Concept] = {}
    for c in all_concepts:
        concept_by_name_lecture[(c.name.lower(), c.lecture_id)] = c

    chains: list[PrerequisiteChainRead] = []
    seen_pairs: set[tuple[str, str]] = set()

    for concept in all_concepts:
        if not concept.prerequisites:
            continue
        for prereq_name in concept.prerequisites:
            pair = (prereq_name.lower(), concept.name.lower())
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            chain_nodes: list[PrerequisiteChainNode] = []

            # Prereq node
            prereq = concept_by_name_lecture.get((prereq_name.lower(), concept.lecture_id))
            if prereq:
                chain_nodes.append(PrerequisiteChainNode(
                    concept_name=prereq.name,
                    lecture_id=prereq.lecture_id,
                    lecture_title=(lecture_map.get(prereq.lecture_id) or type('', (), {'title': 'Unknown'})()).title or "Unknown",
                    timestamp_start=prereq.timestamp_start,
                    is_mastered=mastery_map.get(prereq.id, "not_started") == "mastered",
                ))

            # Target concept node
            chain_nodes.append(PrerequisiteChainNode(
                concept_name=concept.name,
                lecture_id=concept.lecture_id,
                lecture_title=(lecture_map.get(concept.lecture_id) or type('', (), {'title': 'Unknown'})()).title or "Unknown",
                timestamp_start=concept.timestamp_start,
                is_mastered=mastery_map.get(concept.id, "not_started") == "mastered",
            ))

            if len(chain_nodes) >= 2:
                chains.append(PrerequisiteChainRead(
                    concept_name=concept.name,
                    chain=chain_nodes,
                ))

    return chains[:50]  # cap at 50 chains
