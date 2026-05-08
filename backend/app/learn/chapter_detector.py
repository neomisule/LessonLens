"""Chapter boundary detection from semantic segments.

Uses the topic_boundary_score from SegmentationAgent as a primary signal,
then calls the LLM to label and summarize chapters.
"""
import logging
from app.learn.schemas import ExtractedChapter
from app.learn.llm_client import LLMClient
from app.learn.prompts import CHAPTER_DETECTION_SYSTEM, CHAPTER_DETECTION_USER

logger = logging.getLogger(__name__)

# topic_boundary_score below this → high probability of chapter break
_BOUNDARY_THRESHOLD = 0.65
# Minimum chapter duration in seconds
_MIN_CHAPTER_SECONDS = 60.0


def _format_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m"
    return f"{m}m {s}s"


def _detect_breaks_heuristic(segments: list[dict]) -> list[int]:
    """
    Return segment indices that start a new chapter, using topic_boundary_score.
    Always includes index 0 (first segment).
    """
    if not segments:
        return []

    breaks = [0]
    for i in range(1, len(segments)):
        score = segments[i].get("topic_boundary_score", 1.0)
        prev_start = segments[breaks[-1]].get("start", 0)
        this_start = segments[i].get("start", 0)
        duration_since_last = this_start - prev_start

        # Force a break on low similarity AND enough duration since last break
        if score < _BOUNDARY_THRESHOLD and duration_since_last >= _MIN_CHAPTER_SECONDS:
            breaks.append(i)

    return breaks


def _segment_outline(segments: list[dict]) -> str:
    """Format segments as a numbered outline for the LLM."""
    lines = []
    for seg in segments:
        idx = seg.get("sequence_index", 0)
        start = seg.get("start", 0)
        # Preview: first 80 chars
        preview = seg.get("content", "")[:80].replace("\n", " ")
        lines.append(f"[{idx}] {start:.0f}s | {preview}…")
    return "\n".join(lines)


async def detect_chapters(
    segments: list[dict],
    llm: LLMClient,
    total_duration: float = 0.0,
) -> list[ExtractedChapter]:
    """
    Detect chapters from semantic segments and label them via LLM.

    Falls back to heuristic-only chapters if LLM is unavailable.
    """
    if not segments:
        return []

    break_indices = _detect_breaks_heuristic(segments)
    logger.info("[chapter_detector] %d heuristic breaks found", len(break_indices))

    if llm.available:
        chapters = await _label_with_llm(segments, break_indices, llm, total_duration)
        if chapters:
            return chapters
        logger.warning("[chapter_detector] LLM labeling failed, using heuristic chapters")

    # Heuristic fallback: generate generic chapter titles
    return _heuristic_chapters(segments, break_indices)


async def _label_with_llm(
    segments: list[dict],
    break_indices: list[int],
    llm: LLMClient,
    total_duration: float,
) -> list[ExtractedChapter]:
    """Use LLM to generate descriptive chapter titles and summaries."""
    outline = _segment_outline(segments)
    duration_str = _format_duration(total_duration) if total_duration else "unknown"

    response = await llm.extract_json(
        CHAPTER_DETECTION_SYSTEM,
        CHAPTER_DETECTION_USER.format(
            segments_outline=outline,
            total=len(segments),
            duration_str=duration_str,
        ),
    )

    raw_chapters = response.get("chapters", [])
    if not isinstance(raw_chapters, list) or not raw_chapters:
        return []

    result: list[ExtractedChapter] = []
    for i, ch in enumerate(raw_chapters):
        if not isinstance(ch, dict):
            continue
        first_idx = int(ch.get("first_segment_index", 0))
        last_idx = int(ch.get("last_segment_index", len(segments) - 1))
        first_idx = min(first_idx, len(segments) - 1)
        last_idx = min(last_idx, len(segments) - 1)

        ts_start = segments[first_idx].get("start", 0.0)
        ts_end = segments[last_idx].get("end", None)

        result.append(ExtractedChapter(
            sequence_index=i,
            title=str(ch.get("title", f"Chapter {i + 1}")).strip(),
            summary=str(ch.get("summary", "")).strip(),
            timestamp_start=ts_start,
            timestamp_end=ts_end,
            concept_names=[],  # filled by ConceptMapperAgent later
        ))

    return result


def _heuristic_chapters(
    segments: list[dict],
    break_indices: list[int],
) -> list[ExtractedChapter]:
    """Generate simple chapter objects from heuristic breaks without LLM."""
    chapters: list[ExtractedChapter] = []
    for i, start_idx in enumerate(break_indices):
        end_idx = break_indices[i + 1] - 1 if i + 1 < len(break_indices) else len(segments) - 1
        ts_start = segments[start_idx].get("start", 0.0)
        ts_end = segments[end_idx].get("end", None)

        # Use first 60 chars of first segment as a rough title
        first_text = segments[start_idx].get("content", "")[:60].strip()
        title = f"Part {i + 1}: {first_text}…" if first_text else f"Part {i + 1}"

        chapters.append(ExtractedChapter(
            sequence_index=i,
            title=title,
            summary="",
            timestamp_start=ts_start,
            timestamp_end=ts_end,
        ))
    return chapters
