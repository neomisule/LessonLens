"""SubjectGraphAgent — cross-lecture intelligence for a subject.

NOT a pipeline node. Called on-demand from the subjects router after a
lecture finishes processing, or when the subject graph endpoint is requested.

What it does
────────────
1. Load all lectures in the subject + their concepts.
2. Normalize concept names → cluster_label (lowercase, de-pluralize, strip articles).
3. Group concepts by cluster_label:
   - frequency == 1  → unique concept
   - frequency  > 1  → recurring concept (is_recurring=True)
4. Detect prerequisite relationships from Concept.prerequisites JSON arrays.
5. Aggregate mastery state per cluster from UserMastery records.
6. Persist SubjectConcept + SubjectConceptLink rows (upsert by cluster_label).
"""
import logging
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete as sa_delete

from app.models.concept import Concept
from app.models.lecture import Lecture
from app.models.mastery import UserMastery
from app.models.subject_graph import SubjectConcept, SubjectConceptLink

logger = logging.getLogger(__name__)

_STOP_WORDS = {"the", "a", "an", "of", "in", "on", "at", "to", "and", "or", "for",
               "with", "by", "from", "is", "are", "was", "were"}


def _normalize(name: str) -> str:
    """Lower-case, remove articles/stop-words, strip punctuation, de-pluralize."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)  # strip punctuation except hyphen
    words = [w for w in name.split() if w not in _STOP_WORDS]
    label = " ".join(words)
    # Naive de-pluralization: strip trailing 's' only if word > 3 chars
    if label.endswith("s") and len(label) > 3:
        label = label[:-1]
    return label


async def rebuild_subject_graph(db: AsyncSession, subject_id: str) -> dict[str, Any]:
    """
    Full rebuild of SubjectConcept/SubjectConceptLink for a subject.
    Safe to call multiple times — clears and rebuilds idempotently.
    """
    # ── Load lectures ─────────────────────────────────────────────────────────
    lec_result = await db.execute(
        select(Lecture)
        .where(Lecture.subject_id == subject_id)
        .where(Lecture.processing_status == "completed")
    )
    lectures = list(lec_result.scalars().all())
    if not lectures:
        return {"subject_concepts": 0, "recurring_count": 0, "prerequisite_count": 0}

    lecture_ids = [lec.id for lec in lectures]

    # ── Load all concepts across all lectures ─────────────────────────────────
    con_result = await db.execute(
        select(Concept).where(Concept.lecture_id.in_(lecture_ids))
    )
    all_concepts: list[Concept] = list(con_result.scalars().all())

    # ── Load mastery records ──────────────────────────────────────────────────
    mastery_result = await db.execute(
        select(UserMastery)
        .where(UserMastery.lecture_id.in_(lecture_ids))
        .where(UserMastery.concept_id.is_not(None))
        .where(UserMastery.flashcard_id.is_(None))
    )
    mastery_records = list(mastery_result.scalars().all())
    mastery_map: dict[str, str] = {
        m.concept_id: m.confidence
        for m in mastery_records
        if m.concept_id
    }
    conf_to_score = {"mastered": 1.0, "shaky": 0.5, "confused": 0.2, "not_started": 0.0}

    # ── Clear stale subject graph ─────────────────────────────────────────────
    await db.execute(
        sa_delete(SubjectConceptLink).where(
            SubjectConceptLink.lecture_id.in_(lecture_ids)
        )
    )
    # Delete subject concepts that no longer have any links
    existing_scs = await db.execute(
        select(SubjectConcept).where(SubjectConcept.subject_id == subject_id)
    )
    for sc in existing_scs.scalars().all():
        await db.delete(sc)
    await db.flush()

    # ── Cluster concepts by normalized name ───────────────────────────────────
    clusters: dict[str, list[Concept]] = {}
    for c in all_concepts:
        key = _normalize(c.name)
        clusters.setdefault(key, []).append(c)

    # Build set of all prerequisite cluster labels
    all_prereq_labels: set[str] = set()
    for c in all_concepts:
        for prereq_name in (c.prerequisites or []):
            all_prereq_labels.add(_normalize(prereq_name))

    sc_count = 0
    recurring_count = 0
    prerequisite_count = 0

    # ── Persist SubjectConcept + links ────────────────────────────────────────
    for cluster_label, members in clusters.items():
        frequency    = len({c.lecture_id for c in members})  # unique lecture count
        is_recurring = frequency > 1
        is_prereq    = cluster_label in all_prereq_labels

        # Importance: majority vote among members
        imp_counts: dict[str, int] = {}
        for m in members:
            imp_counts[m.importance] = imp_counts.get(m.importance, 0) + 1
        importance = max(imp_counts, key=imp_counts.get)  # type: ignore[arg-type]

        avg_exam = sum(m.exam_likelihood for m in members) / len(members)

        # Average mastery
        scores = [
            conf_to_score.get(mastery_map.get(m.id, "not_started"), 0.0)
            for m in members
        ]
        avg_mastery = sum(scores) / len(scores) if scores else 0.0

        # Canonical name: pick the most common, falling back to first member
        name_counts: dict[str, int] = {}
        for m in members:
            name_counts[m.name] = name_counts.get(m.name, 0) + 1
        canonical_name = max(name_counts, key=name_counts.get)  # type: ignore[arg-type]

        sc = SubjectConcept(
            subject_id=subject_id,
            name=canonical_name,
            cluster_label=cluster_label,
            frequency=frequency,
            is_prerequisite=is_prereq,
            is_recurring=is_recurring,
            importance=importance,
            avg_exam_likelihood=round(avg_exam, 3),
            avg_mastery=round(avg_mastery, 3),
        )
        db.add(sc)
        await db.flush()
        sc_count += 1
        if is_recurring:
            recurring_count += 1
        if is_prereq:
            prerequisite_count += 1

        for member in members:
            db.add(SubjectConceptLink(
                subject_concept_id=sc.id,
                concept_id=member.id,
                lecture_id=member.lecture_id,
            ))

    await db.commit()
    logger.info(
        "[subject_graph] Built %d subject concepts (%d recurring, %d prerequisites) for subject %s",
        sc_count, recurring_count, prerequisite_count, subject_id,
    )
    return {
        "subject_concepts": sc_count,
        "recurring_count": recurring_count,
        "prerequisite_count": prerequisite_count,
    }
