"""Concept extraction from semantic segments — batched + parallel.

Groups BATCH_SIZE segments into a single LLM call, then runs all batches
concurrently with asyncio.gather.

  Old: 12 segments → 12 sequential LLM calls
  Mid: 12 segments, BATCH_SIZE=4 → 3 sequential calls
  New: 12 segments, BATCH_SIZE=4 → 3 parallel calls  (all at once)
"""
import asyncio
import logging
from collections import defaultdict

from app.learn.schemas import ExtractedConcept
from app.learn.llm_client import LLMClient
from app.learn.prompts import CONCEPT_EXTRACTION_SYSTEM, CONCEPT_EXTRACTION_MULTI_USER

logger = logging.getLogger(__name__)

# 4 segments per call is safe within claude-3-5-haiku token limits.
# Even 90-min lectures produce ≤ 20 segments → ≤ 5 LLM calls.
BATCH_SIZE = 4

_IMPORTANCE_RANK = {"core": 3, "supporting": 2, "supplemental": 1}


def _format_batch_prompt(batch: list[dict]) -> str:
    """Format a list of segments into the multi-segment extraction prompt."""
    blocks = []
    for seg in batch:
        idx   = seg.get("sequence_index", 0)
        start = seg["start"]
        end   = seg["end"]
        text  = seg["content"]
        blocks.append(f"=== Segment [{idx}] {start:.1f}s–{end:.1f}s ===\n{text}")

    return CONCEPT_EXTRACTION_MULTI_USER.format(
        n_segments=len(batch),
        first_start=batch[0]["start"],
        last_end=batch[-1]["end"],
        segments_block="\n\n".join(blocks),
    )


async def extract_concepts_from_segments(
    segments: list[dict],
    llm: LLMClient,
) -> list[ExtractedConcept]:
    """
    Extract concepts from segments using batched LLM calls.

    Each segment dict must have: sequence_index, start, end, content.
    Returns deduplicated concepts sorted by importance then timestamp.
    """
    if not llm.available:
        logger.info("[concept_extractor] LLM unavailable — returning empty")
        return []

    # Index segments by sequence_index for fast timestamp lookup
    seg_by_idx: dict[int, dict] = {
        s.get("sequence_index", i): s for i, s in enumerate(segments)
    }

    # Build all batches upfront
    batches = [
        segments[i : i + BATCH_SIZE]
        for i in range(0, len(segments), BATCH_SIZE)
    ]

    async def _call_batch(batch: list[dict]) -> tuple[list[dict], list[dict]]:
        """Returns (batch, results_list) — keeps batch reference for fallback."""
        user_prompt = _format_batch_prompt(batch)
        response = await llm.extract_json(CONCEPT_EXTRACTION_SYSTEM, user_prompt)
        results = response.get("results")
        if not isinstance(results, list):
            legacy = response.get("concepts", [])
            if isinstance(legacy, list):
                results = [{"segment_index": batch[0].get("sequence_index", 0), "concepts": legacy}]
            else:
                results = []
        return batch, results

    # ── Run ALL batches in parallel ───────────────────────────────────────────
    batch_outputs = await asyncio.gather(
        *[_call_batch(b) for b in batches],
        return_exceptions=True,
    )

    raw: list[ExtractedConcept] = []

    for output in batch_outputs:
        if isinstance(output, Exception):
            logger.warning("[concept_extractor] Batch failed: %s", output)
            continue
        batch, results = output
        for item in results:
            if not isinstance(item, dict):
                continue
            seg_idx      = item.get("segment_index", 0)
            seg          = seg_by_idx.get(seg_idx) or batch[0]
            concepts_data = item.get("concepts", [])
            if not isinstance(concepts_data, list):
                continue

            for c in concepts_data:
                if not isinstance(c, dict):
                    continue
                name       = (c.get("name") or "").strip()
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
                    segment_index=seg_idx,
                ))

    extracted = _deduplicate(raw)
    logger.info(
        "[concept_extractor] %d segments → %d parallel LLM calls → %d unique concepts",
        len(segments),
        len(batches),
        len(extracted),
    )
    return extracted


def _deduplicate(concepts: list[ExtractedConcept]) -> list[ExtractedConcept]:
    """Merge concepts with the same name (case-insensitive)."""
    groups: dict[str, list[ExtractedConcept]] = defaultdict(list)
    for c in concepts:
        groups[c.name.lower()].append(c)

    merged: list[ExtractedConcept] = []
    for group in groups.values():
        group.sort(key=lambda c: (-_IMPORTANCE_RANK.get(c.importance, 0), c.timestamp_start))
        primary = group[0]
        all_examples: list[str] = []
        seen: set[str] = set()
        for c in group:
            for ex in c.examples:
                if ex.lower() not in seen:
                    all_examples.append(ex)
                    seen.add(ex.lower())
        primary.examples = all_examples[:5]
        merged.append(primary)

    merged.sort(key=lambda c: (-_IMPORTANCE_RANK.get(c.importance, 0), c.timestamp_start))
    return merged
