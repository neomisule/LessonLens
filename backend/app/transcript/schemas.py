"""Internal dataclasses for the transcript ingestion pipeline.

These are NOT Pydantic API schemas — they are pure Python dataclasses used
as intermediate data containers between pipeline stages.
"""
from dataclasses import dataclass, field


@dataclass
class RawSegment:
    """A single caption / ASR segment as returned by the source."""
    text: str
    start: float          # seconds from video start
    duration: float       # seconds
    confidence: float = 0.85  # YouTube captions default; Whisper fills per-segment


@dataclass
class NormalizedSegment:
    """A cleaned, normalised segment ready for storage."""
    text: str
    start: float
    end: float
    timestamp_str: str    # "MM:SS"
    confidence: float
    is_noise: bool        # True if segment is music/applause/etc.


@dataclass
class TranscriptChunk:
    """A fixed-size time window (default 15 s) of concatenated segments."""
    segments: list[NormalizedSegment]
    start: float
    end: float
    text: str             # space-joined text
    word_count: int


@dataclass
class Gap:
    """A silence gap in the transcript."""
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class QualityReport:
    """Transcript quality assessment result."""
    method: str                          # "youtube_captions" | "whisper_fallback"
    confidence_avg: float
    confidence_min: float
    noise_ratio: float                   # 0-1
    coverage_pct: float                  # 0-100
    gap_count: int
    gaps: list[Gap] = field(default_factory=list)
    word_count: int = 0
    segment_count: int = 0
    total_duration: float = 0.0
    is_poor: bool = False                # True → trigger fallback


@dataclass
class VideoMetadata:
    """Lightweight metadata retrieved from YouTube without API key."""
    title: str
    channel_name: str
    thumbnail_url: str
    duration_seconds: int | None = None  # not always available via oEmbed


@dataclass
class IngestionResult:
    """Final output of the IngestionAgent for one lecture."""
    metadata: VideoMetadata
    segments: list[NormalizedSegment]
    quality: QualityReport
