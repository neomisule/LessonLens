"""Exam likelihood scoring for extracted concepts.

Uses purely heuristic signals derived from the transcript — no LLM calls.
Score is always in [0, 1] where 1 = near-certain exam material.
"""
import re
from app.learn.schemas import ExtractedConcept

# Phrases that signal explicit definition / exam-worthy content
_DEFINITION_SIGNALS = re.compile(
    r"\b(is defined as|is called|refers to|means that|can be defined|"
    r"is known as|we call|is the term for|definition of)\b",
    re.IGNORECASE,
)

# Phrases that signal importance
_IMPORTANCE_SIGNALS = re.compile(
    r"\b(important|key|critical|essential|fundamental|remember|exam|test|"
    r"will ask|make sure|note that|significant|core concept)\b",
    re.IGNORECASE,
)

_IMPORTANCE_RANK = {"core": 1.0, "supporting": 0.6, "supplemental": 0.3}


def compute_exam_likelihood(
    concept: ExtractedConcept,
    all_segments: list[dict],
    total_duration: float,
) -> float:
    """
    Compute a 0-1 exam likelihood score for a concept.

    Signals used:
    1. importance label from extraction
    2. how many segments mention the concept name
    3. explicit definition/importance language in the definition or explanation
    4. position in lecture (near start → likely foundational, near end → likely reviewed)
    """
    # ── 1. Importance label ────────────────────────────────────────────────────
    base = _IMPORTANCE_RANK.get(concept.importance, 0.5)

    # ── 2. Mention frequency ───────────────────────────────────────────────────
    name_lower = concept.name.lower()
    mention_count = sum(
        1 for seg in all_segments
        if name_lower in seg.get("content", "").lower()
    )
    freq_score = min(1.0, mention_count / max(len(all_segments) * 0.3, 3))

    # ── 3. Definition language ─────────────────────────────────────────────────
    combined_text = f"{concept.definition} {concept.explanation}"
    def_score = 1.0 if _DEFINITION_SIGNALS.search(combined_text) else 0.4
    imp_score = min(1.0, 0.4 + 0.3 * bool(_IMPORTANCE_SIGNALS.search(combined_text)))

    # ── 4. Position (concepts introduced early are foundational) ───────────────
    if total_duration > 0:
        relative_pos = concept.timestamp_start / total_duration
        # Bell curve: peak at 0.2 (early), still high at 0.5, lower at 0.9
        pos_score = 1.0 - abs(relative_pos - 0.2) * 0.6
    else:
        pos_score = 0.6

    # ── Weighted average ───────────────────────────────────────────────────────
    score = (
        base * 0.35
        + freq_score * 0.30
        + def_score * 0.20
        + imp_score * 0.10
        + pos_score * 0.05
    )
    return round(min(1.0, max(0.0, score)), 3)


def compute_time_spent(
    concept: ExtractedConcept,
    all_segments: list[dict],
) -> float:
    """
    Estimate total lecture time spent on this concept in seconds.

    Sums durations of segments that mention the concept name.
    """
    name_lower = concept.name.lower()
    total = 0.0
    for seg in all_segments:
        if name_lower in seg.get("content", "").lower():
            duration = seg.get("end", seg.get("start", 0)) - seg.get("start", 0)
            total += max(0.0, duration)
    return round(total, 1)
