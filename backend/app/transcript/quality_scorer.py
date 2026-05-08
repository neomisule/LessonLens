"""Transcript quality assessment.

Produces a QualityReport from a list of normalised segments.
If the report's `is_poor` flag is True the pipeline will trigger
Whisper fallback transcription.
"""
import re

from app.transcript.schemas import NormalizedSegment, QualityReport, Gap
from app.transcript.chunker import detect_gaps, compute_coverage

# ── Tunable thresholds ────────────────────────────────────────────────────────

# Minimum average confidence to avoid fallback
CONFIDENCE_AVG_THRESHOLD = 0.55
# Maximum noise-token ratio (music/applause/etc.) before marking poor quality
NOISE_RATIO_THRESHOLD = 0.25
# Minimum coverage of the total video duration
COVERAGE_THRESHOLD = 60.0   # percent
# Minimum word density (words per minute)
MIN_WORD_DENSITY_WPM = 30.0
# Silence gaps longer than this (seconds) count toward gap_count
GAP_THRESHOLD = 5.0

# Noise word patterns to count
_NOISE_WORDS = re.compile(
    r"\[(?:Music|Applause|Laughter|Inaudible|Noise|Background)\]"
    r"|\((?:inaudible|music|applause)\)",
    re.IGNORECASE,
)


def _count_noise_tokens(text: str) -> int:
    return len(_NOISE_WORDS.findall(text))


def score_quality(
    segments: list[NormalizedSegment],
    total_duration: float,
    method: str = "youtube_captions",
) -> QualityReport:
    """
    Assess transcript quality and decide whether fallback is needed.

    Args:
        segments: Normalised (but unfiltered) segments including noise ones.
        total_duration: Video duration in seconds; used for coverage/density.
        method: The ingestion method used ("youtube_captions" | "whisper_fallback").
    """
    if not segments:
        return QualityReport(
            method=method,
            confidence_avg=0.0,
            confidence_min=0.0,
            noise_ratio=1.0,
            coverage_pct=0.0,
            gap_count=0,
            gaps=[],
            word_count=0,
            segment_count=0,
            total_duration=total_duration,
            is_poor=True,
        )

    # Filter out noise-only segments for quality metrics
    speech_segs = [s for s in segments if not s.is_noise]

    # Confidence
    confidences = [s.confidence for s in speech_segs] if speech_segs else [0.0]
    conf_avg = sum(confidences) / len(confidences)
    conf_min = min(confidences)

    # Noise ratio (noise tokens / total tokens)
    all_text = " ".join(s.text for s in segments)
    all_words = len(all_text.split()) or 1
    noise_tokens = _count_noise_tokens(all_text) + sum(1 for s in segments if s.is_noise)
    noise_ratio = min(1.0, noise_tokens / all_words)

    # Coverage
    coverage_pct = compute_coverage(speech_segs, total_duration) if total_duration > 0 else 100.0

    # Gaps
    gaps: list[Gap] = detect_gaps(speech_segs, gap_threshold=GAP_THRESHOLD)

    # Word density (words per minute)
    speech_text = " ".join(s.text for s in speech_segs)
    word_count = len(speech_text.split())
    duration_min = max(total_duration / 60, 0.01)
    word_density_wpm = word_count / duration_min

    # ── Decision logic ────────────────────────────────────────────────────────
    is_poor = (
        conf_avg < CONFIDENCE_AVG_THRESHOLD
        or noise_ratio > NOISE_RATIO_THRESHOLD
        or (coverage_pct < COVERAGE_THRESHOLD and total_duration > 30)
        or (word_density_wpm < MIN_WORD_DENSITY_WPM and total_duration > 60)
    )

    return QualityReport(
        method=method,
        confidence_avg=round(conf_avg, 4),
        confidence_min=round(conf_min, 4),
        noise_ratio=round(noise_ratio, 4),
        coverage_pct=round(coverage_pct, 2),
        gap_count=len(gaps),
        gaps=gaps,
        word_count=word_count,
        segment_count=len(speech_segs),
        total_duration=total_duration,
        is_poor=is_poor,
    )
