"""Transcript normalisation utilities.

Cleans raw caption text and formats timestamps into human-readable MM:SS strings.
Never modifies content semantics — only removes noise artefacts and standardises
whitespace / casing.
"""
import re

from app.transcript.schemas import RawSegment, NormalizedSegment

# Patterns for noise tokens like [Music], [Applause], (inaudible), >>
_NOISE_PATTERN = re.compile(
    r"\[(?:Music|Applause|Laughter|Inaudible|Silence|Noise|Background)\]"
    r"|\((?:inaudible|music|applause|laughter)\)"
    r"|>>\s*\w+:",
    re.IGNORECASE,
)
_SPEAKER_LABEL = re.compile(r"^>>\s*")
_MULTI_SPACE = re.compile(r"\s{2,}")
_NOISE_ONLY = re.compile(r"^\[.*?\]$")


def format_timestamp(seconds: float) -> str:
    """Convert float seconds to 'MM:SS' display string."""
    total = max(0, int(seconds))
    m, s = divmod(total, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def is_noise_segment(text: str) -> bool:
    """Return True if the segment contains only noise markers."""
    stripped = text.strip()
    return bool(_NOISE_ONLY.match(stripped)) or stripped in ("[Music]", "[Applause]", "[Laughter]")


def clean_text(raw: str) -> str:
    """Remove noise tokens and normalise whitespace, preserving all words."""
    text = _NOISE_PATTERN.sub("", raw)
    text = _SPEAKER_LABEL.sub("", text)
    text = _MULTI_SPACE.sub(" ", text)
    return text.strip()


def normalize_segments(
    raw: list[RawSegment],
    min_duration: float = 0.2,
) -> list[NormalizedSegment]:
    """
    Normalise a list of raw segments:
    - Clean text
    - Mark noise segments
    - Remove segments below min_duration that are pure whitespace after cleaning
    - Add MM:SS timestamp strings
    """
    normalized: list[NormalizedSegment] = []

    for seg in raw:
        cleaned = clean_text(seg.text)
        noise = is_noise_segment(seg.text)
        end = seg.start + seg.duration

        if not cleaned and not noise:
            continue  # nothing left after cleaning

        if seg.duration < min_duration and not cleaned:
            continue  # sub-threshold empty segment

        normalized.append(
            NormalizedSegment(
                text=cleaned if cleaned else seg.text.strip(),
                start=seg.start,
                end=end,
                timestamp_str=format_timestamp(seg.start),
                confidence=seg.confidence,
                is_noise=noise,
            )
        )

    return normalized


def merge_short_segments(
    segments: list[NormalizedSegment],
    min_duration: float = 0.8,
    max_merge_gap: float = 0.5,
) -> list[NormalizedSegment]:
    """
    Merge very short consecutive segments that belong to the same utterance.
    Segments are merged if: duration < min_duration AND gap to next < max_merge_gap.
    """
    if not segments:
        return segments

    merged: list[NormalizedSegment] = []
    buf = segments[0]

    for nxt in segments[1:]:
        gap = nxt.start - buf.end
        short = (buf.end - buf.start) < min_duration

        if short and gap <= max_merge_gap and not nxt.is_noise:
            # Merge into buffer
            buf = NormalizedSegment(
                text=f"{buf.text} {nxt.text}".strip(),
                start=buf.start,
                end=nxt.end,
                timestamp_str=buf.timestamp_str,
                confidence=min(buf.confidence, nxt.confidence),
                is_noise=False,
            )
        else:
            if not buf.is_noise:
                merged.append(buf)
            buf = nxt

    if not buf.is_noise:
        merged.append(buf)

    return merged
