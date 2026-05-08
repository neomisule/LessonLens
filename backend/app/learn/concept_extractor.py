"""Concept extraction from semantic segments.

Processes segments one by one (or in small batches), calls the LLM with strict
grounding prompts, and returns a deduplicated list of ExtractedConcept objects.
"""
import logging
from collections import defaultdict

from app.learn.schemas import ExtractedConcept
from app.learn.llm_client import LLMClient
from app.learn.prompts import CONCEPT_EXTRACTION_SYSTEM, CONCEPT_EXTRACTION_USER

logger = logging.getLogger(__name__)

# Concepts with the same name (case-insensitive) are merged
_IMPORTANCE_RANK = {"core": 3, "supporting": 2, "supplemental": 1}


def _format_user_prompt(seg: dict, index: int) -> str:
    return CONCEPT_EXTRACTION_USER.format(
        index=index,
        start=seg["start"],
        end=seg["end"],
        text=seg["content"],
    )


async def extract_concepts_from_segments(
    segments: list[dict],
    llm: LLMClient,
) -> list[ExtractedConcept]:
    """
    Extract concepts from a list of semantic segment dicts.

    Each segment dict has keys: content, start, end, sequence_index.
    Returns deduplicated concepts sorted by importance then timestamp.
    """
    if not llm.available:
        logger.info("[concept_extractor] LLM unavailable — returning empty concepts")
        return []

    raw: list[ExtractedConcept] = []

    for seg in segments:
        idx = seg.get("sequence_index", 0)
        user_prompt = _format_user_prompt(seg, idx)

        response = await llm.extract_json(CONCEPT_EXTRACTION_SYSTEM, user_prompt)
        concepts_data = response.get("concepts", [])

        if not isinstance(concepts_data, list):
            continue

        for c in concepts_data:
            if not isinstance(c, dict):
                continue
            name = (c.get("name") or "").strip()
            definition = (c.get("definition") or "").strip()
            if not name or not definition:
                continue

            raw.append(ExtractedConcept(
                name=name,
                definition=definition,
                explanation=(c.get("explanation") or "").strip(),
                examples=[str(e) for e in (c.get("examples") or []) if e],
                importance=c.get("importance", "supporting"),
                tags=[str(t) for t in (c.get("tags") or []) if t],
                timestamp_start=float(c.get("timestamp_start", seg["start"])),
                timestamp_end=float(seg["end"]),
                evidence_quote=(c.get("evidence_quote") or "").strip(),
                segment_index=idx,
            ))

    return _deduplicate(raw)


def _deduplicate(concepts: list[ExtractedConcept]) -> list[ExtractedConcept]:
    """
    Merge concepts with the same name (case-insensitive).

    When merging, prefer:
    - Higher importance rank
    - Earlier timestamp
    - Longer definition (more complete)
    """
    groups: dict[str, list[ExtractedConcept]] = defaultdict(list)
    for c in concepts:
        groups[c.name.lower()].append(c)

    merged: list[ExtractedConcept] = []
    for group in groups.values():
        # Sort by importance desc, then timestamp asc
        group.sort(key=lambda c: (-_IMPORTANCE_RANK.get(c.importance, 0), c.timestamp_start))
        primary = group[0]

        # Merge examples from all occurrences
        all_examples = []
        seen_examples: set[str] = set()
        for c in group:
            for ex in c.examples:
                if ex.lower() not in seen_examples:
                    all_examples.append(ex)
                    seen_examples.add(ex.lower())

        primary.examples = all_examples[:5]  # cap at 5
        merged.append(primary)

    # Sort: core first, then supporting, then supplemental; then by timestamp
    merged.sort(key=lambda c: (-_IMPORTANCE_RANK.get(c.importance, 0), c.timestamp_start))
    return merged
