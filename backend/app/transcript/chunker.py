"""Fixed-size time-window chunking and gap detection.

Splits a normalised segment list into 15-second windows for downstream
embedding and semantic segmentation.  Also detects silence gaps.
"""
from app.transcript.schemas import NormalizedSegment, TranscriptChunk, Gap

# Default window size used throughout the pipeline
DEFAULT_WINDOW_SECONDS = 15.0
GAP_THRESHOLD_SECONDS = 5.0


def chunk_into_windows(
    segments: list[NormalizedSegment],
    window_size: float = DEFAULT_WINDOW_SECONDS,
) -> list[TranscriptChunk]:
    """
    Group segments into non-overlapping time windows of `window_size` seconds.

    A segment is assigned to the window that contains its *start* time.
    Windows with zero words are omitted.
    """
    if not segments:
        return []

    chunks: list[TranscriptChunk] = []
    window_start = segments[0].start
    current_segs: list[NormalizedSegment] = []

    for seg in segments:
        if seg.start >= window_start + window_size:
            if current_segs:
                chunks.append(_build_chunk(current_segs))
            # Advance window boundary to align with new segment
            window_start = (seg.start // window_size) * window_size
            current_segs = []
        current_segs.append(seg)

    if current_segs:
        chunks.append(_build_chunk(current_segs))

    return chunks


def _build_chunk(segs: list[NormalizedSegment]) -> TranscriptChunk:
    text = " ".join(s.text for s in segs if s.text)
    return TranscriptChunk(
        segments=segs,
        start=segs[0].start,
        end=segs[-1].end,
        text=text,
        word_count=len(text.split()),
    )


def detect_gaps(
    segments: list[NormalizedSegment],
    gap_threshold: float = GAP_THRESHOLD_SECONDS,
) -> list[Gap]:
    """
    Find silence gaps larger than `gap_threshold` seconds between consecutive segments.
    """
    gaps: list[Gap] = []
    for i in range(1, len(segments)):
        silence = segments[i].start - segments[i - 1].end
        if silence >= gap_threshold:
            gaps.append(Gap(start=segments[i - 1].end, end=segments[i].start))
    return gaps


def compute_coverage(
    segments: list[NormalizedSegment],
    total_duration: float,
) -> float:
    """
    Compute the fraction (0–100) of total_duration covered by segments.
    Overlapping segments are merged before computing coverage.
    """
    if total_duration <= 0 or not segments:
        return 0.0

    # Sort by start and merge overlapping/adjacent intervals
    intervals = sorted((s.start, s.end) for s in segments)
    covered = 0.0
    start, end = intervals[0]
    for s, e in intervals[1:]:
        if s <= end:
            end = max(end, e)
        else:
            covered += end - start
            start, end = s, e
    covered += end - start

    return min(100.0, (covered / total_duration) * 100)
