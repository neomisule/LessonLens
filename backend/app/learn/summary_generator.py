"""Summary generation at three levels: brief, standard, detailed.

Each summary is grounded in the actual transcript — timestamps in sections
always come from the semantic segments provided as context.
"""
import logging
from app.learn.schemas import GeneratedSummary, SummarySection, ExtractedConcept
from app.learn.llm_client import LLMClient
from app.learn.prompts import (
    SUMMARY_SYSTEM,
    SUMMARY_USER_BRIEF,
    SUMMARY_USER_STANDARD,
    SUMMARY_USER_DETAILED,
)

logger = logging.getLogger(__name__)


def _format_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m {s:02d}s"


def _build_segment_context(segments: list[dict], max_chars: int = 6000) -> str:
    """Format semantic segments as numbered context blocks for the LLM."""
    lines = []
    chars = 0
    for seg in segments:
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        text = seg.get("content", "")
        line = f"[{start:.0f}s–{end:.0f}s] {text}"
        if chars + len(line) > max_chars:
            lines.append("... (additional segments omitted for length)")
            break
        lines.append(line)
        chars += len(line)
    return "\n\n".join(lines)


def _brief_concepts(concepts: list[ExtractedConcept]) -> str:
    lines = []
    for c in concepts[:10]:  # top 10 for context
        lines.append(f"- {c.name}: {c.definition[:80]}")
    return "\n".join(lines) if lines else "No concepts yet extracted."


def _full_concepts(concepts: list[ExtractedConcept]) -> str:
    lines = []
    for c in concepts:
        lines.append(f"- [{c.timestamp_start:.0f}s] {c.name} ({c.importance}): {c.definition}")
    return "\n".join(lines) if lines else "No concepts yet extracted."


def _parse_sections(data: list) -> list[SummarySection]:
    """Convert LLM-returned section dicts to SummarySection objects."""
    sections: list[SummarySection] = []
    for s in data:
        if not isinstance(s, dict):
            continue
        heading = str(s.get("heading", "")).strip()
        content = str(s.get("content", "")).strip()
        if not heading or not content:
            continue
        ts_start = s.get("timestamp_start")
        ts_end = s.get("timestamp_end")
        key_points = [str(p) for p in (s.get("key_points") or []) if p]
        sections.append(SummarySection(
            heading=heading,
            content=content,
            timestamp_start=float(ts_start) if ts_start is not None else 0.0,
            timestamp_end=float(ts_end) if ts_end is not None else None,
            key_points=key_points,
        ))
    return sections


async def generate_all_summaries(
    segments: list[dict],
    concepts: list[ExtractedConcept],
    lecture_title: str,
    total_duration: float,
    llm: LLMClient,
    levels: tuple[str, ...] | list[str] = ("brief", "standard", "detailed"),
) -> list[GeneratedSummary]:
    """
    Generate summaries at the requested levels (brief / standard / detailed).

    Pass levels=("brief",) for the fast path, levels=("standard","detailed")
    for the background deep path.  Returns only the levels that succeed.
    """
    if not llm.available:
        logger.info("[summary_generator] LLM unavailable — returning empty summaries")
        return []

    duration_str = _format_duration(total_duration)
    title = lecture_title or "Lecture"
    results: list[GeneratedSummary] = []

    for level in levels:
        if level not in ("brief", "standard", "detailed"):
            logger.warning("[summary_generator] Unknown level '%s' — skipping", level)
            continue
        summary = await _generate_one(
            level=level,
            segments=segments,
            concepts=concepts,
            title=title,
            duration_str=duration_str,
            llm=llm,
        )
        if summary:
            results.append(summary)

    return results


async def _generate_one(
    level: str,
    segments: list[dict],
    concepts: list[ExtractedConcept],
    title: str,
    duration_str: str,
    llm: LLMClient,
) -> GeneratedSummary | None:
    context_limit = {"brief": 3000, "standard": 5000, "detailed": 8000}[level]
    context = _build_segment_context(segments, max_chars=context_limit)

    if level == "brief":
        user_prompt = SUMMARY_USER_BRIEF.format(
            title=title, duration_str=duration_str, context=context,
        )
    elif level == "standard":
        user_prompt = SUMMARY_USER_STANDARD.format(
            title=title, duration_str=duration_str, context=context,
            concepts_brief=_brief_concepts(concepts),
        )
    else:
        user_prompt = SUMMARY_USER_DETAILED.format(
            title=title, duration_str=duration_str, context=context,
            concepts_full=_full_concepts(concepts),
        )

    response = await llm.extract_json(SUMMARY_SYSTEM, user_prompt)
    if not response:
        logger.warning("[summary_generator] LLM returned empty for level=%s", level)
        return None

    raw_title = str(response.get("title", title)).strip()
    raw_content = str(response.get("content", "")).strip()
    raw_sections = response.get("sections", [])

    if not raw_content:
        return None

    sections = _parse_sections(raw_sections) if isinstance(raw_sections, list) else []

    # Ensure every section timestamp is grounded: clamp to first segment start
    if segments:
        min_ts = segments[0].get("start", 0.0)
        max_ts = segments[-1].get("end", total_duration)
        for s in sections:
            s.timestamp_start = max(min_ts, min(s.timestamp_start, max_ts))

    return GeneratedSummary(
        level=level,
        title=raw_title,
        content=raw_content,
        sections=sections,
    )
