"""Semantic topic segmentation.

Takes a list of TranscriptChunks (15-second windows) with their pre-computed
embeddings and groups them into longer topic-level SemanticSegments using
cosine similarity between adjacent chunk embeddings.

Low similarity between consecutive chunks → topic boundary.
"""
import math
import logging
from typing import TypedDict

from app.transcript.schemas import TranscriptChunk

logger = logging.getLogger(__name__)

# Cosine similarity below this value marks a topic boundary
DEFAULT_BOUNDARY_THRESHOLD = 0.72

# Minimum / maximum segment duration in seconds
MIN_SEGMENT_SECONDS = 20.0
MAX_SEGMENT_SECONDS = 300.0


class SemanticSegmentDict(TypedDict):
    """Dict representation of a semantic segment for pipeline state."""
    sequence_index: int
    content: str
    start: float
    end: float
    token_count: int
    topic_boundary_score: float   # similarity score of the boundary that opened this segment


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def detect_topic_boundaries(
    embeddings: list[list[float]],
    threshold: float = DEFAULT_BOUNDARY_THRESHOLD,
) -> list[int]:
    """
    Return indices into `embeddings` where a new topic starts.

    Index 0 is always included (first chunk always starts a segment).
    Subsequent indices are included when cosine similarity between chunk[i-1]
    and chunk[i] drops below `threshold`.
    """
    if not embeddings:
        return []

    boundaries = [0]
    for i in range(1, len(embeddings)):
        sim = _cosine_similarity(embeddings[i - 1], embeddings[i])
        if sim < threshold:
            boundaries.append(i)

    return boundaries


def build_semantic_segments(
    chunks: list[TranscriptChunk],
    boundary_indices: list[int],
    embeddings: list[list[float]] | None = None,
) -> list[SemanticSegmentDict]:
    """
    Group TranscriptChunks between topic boundaries into SemanticSegment dicts.

    Respects MIN_SEGMENT_SECONDS and MAX_SEGMENT_SECONDS:
    - Segments too short are merged with the next one
    - Segments too long are forcibly split at the midpoint
    """
    if not chunks:
        return []

    # Build raw groups from boundary indices
    boundary_set = set(boundary_indices)
    groups: list[list[TranscriptChunk]] = []
    current: list[TranscriptChunk] = []

    for i, chunk in enumerate(chunks):
        if i in boundary_set and current:
            groups.append(current)
            current = []
        current.append(chunk)
    if current:
        groups.append(current)

    # Enforce min/max duration constraints
    groups = _enforce_constraints(groups)

    # Build result dicts
    result: list[SemanticSegmentDict] = []
    for idx, group in enumerate(groups):
        text = " ".join(c.text for c in group)
        start = group[0].start
        end = group[-1].end
        boundary_score = 0.0
        if embeddings and idx > 0 and boundary_indices and idx < len(boundary_indices):
            # Store the similarity score of the boundary that started this segment
            bi = boundary_indices[idx] if idx < len(boundary_indices) else len(chunks) - 1
            if 0 < bi < len(embeddings):
                boundary_score = _cosine_similarity(embeddings[bi - 1], embeddings[bi])

        result.append(SemanticSegmentDict(
            sequence_index=idx,
            content=text,
            start=start,
            end=end,
            token_count=len(text.split()),
            topic_boundary_score=round(boundary_score, 4),
        ))

    return result


def _enforce_constraints(
    groups: list[list[TranscriptChunk]],
) -> list[list[TranscriptChunk]]:
    """Merge too-short groups forward; split too-long groups at midpoint."""
    # Merge short groups (absorb into next, or merge last two)
    merged: list[list[TranscriptChunk]] = []
    i = 0
    while i < len(groups):
        g = groups[i]
        duration = (g[-1].end - g[0].start) if g else 0
        if duration < MIN_SEGMENT_SECONDS and i + 1 < len(groups):
            # Merge with next group
            groups[i + 1] = g + groups[i + 1]
            i += 1
            continue
        merged.append(g)
        i += 1

    # Split groups that are too long
    final: list[list[TranscriptChunk]] = []
    for g in merged:
        duration = (g[-1].end - g[0].start) if g else 0
        if duration > MAX_SEGMENT_SECONDS and len(g) >= 2:
            mid = len(g) // 2
            final.append(g[:mid])
            final.append(g[mid:])
        else:
            final.append(g)

    return final


def fallback_fixed_segments(
    chunks: list[TranscriptChunk],
    target_duration: float = 90.0,
) -> list[SemanticSegmentDict]:
    """
    Fallback segmentation when embeddings are unavailable.
    Groups chunks into ~target_duration second windows.
    """
    if not chunks:
        return []

    groups: list[list[TranscriptChunk]] = []
    current: list[TranscriptChunk] = []
    window_start = chunks[0].start

    for chunk in chunks:
        if chunk.start >= window_start + target_duration and current:
            groups.append(current)
            current = []
            window_start = chunk.start
        current.append(chunk)
    if current:
        groups.append(current)

    result: list[SemanticSegmentDict] = []
    for idx, group in enumerate(groups):
        text = " ".join(c.text for c in group)
        result.append(SemanticSegmentDict(
            sequence_index=idx,
            content=text,
            start=group[0].start,
            end=group[-1].end,
            token_count=len(text.split()),
            topic_boundary_score=0.0,
        ))
    return result
