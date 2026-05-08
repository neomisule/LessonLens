"""YouTube caption and metadata client.

Fetches captions via youtube_transcript_api (no API key required) and
video metadata via the public YouTube oEmbed endpoint.
"""
import logging
import httpx

from app.transcript.schemas import RawSegment, VideoMetadata

logger = logging.getLogger(__name__)

_OEMBED_URL = "https://www.youtube.com/oembed"

# youtube_transcript_api raises these on bad videos
_TRANSCRIPT_ERRORS: tuple[type[Exception], ...] = ()
try:
    from youtube_transcript_api import (
        YouTubeTranscriptApi,
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )
    _TRANSCRIPT_ERRORS = (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable)
    _YT_API_AVAILABLE = True
except ImportError:
    _YT_API_AVAILABLE = False
    logger.warning("youtube_transcript_api not installed; transcript fetching disabled")


async def fetch_video_metadata(video_id: str) -> VideoMetadata:
    """Fetch lightweight video metadata via YouTube oEmbed (no API key)."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(_OEMBED_URL, params={"url": url, "format": "json"})
        if resp.status_code != 200:
            return VideoMetadata(
                title=f"YouTube Lecture ({video_id})",
                channel_name="Unknown",
                thumbnail_url=f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            )
        data = resp.json()
        return VideoMetadata(
            title=data.get("title", f"YouTube Lecture ({video_id})"),
            channel_name=data.get("author_name", "Unknown"),
            thumbnail_url=data.get("thumbnail_url", f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"),
        )


def fetch_captions_sync(video_id: str) -> list[RawSegment] | None:
    """
    Fetch YouTube auto-generated or manual captions synchronously.

    Returns a list of RawSegments, or None if captions are unavailable.
    Prefers manual English captions, falls back to auto-generated.
    """
    if not _YT_API_AVAILABLE:
        return None

    try:
        # Prefer manual captions, fall back to auto-generated
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_manually_created_transcript(["en", "en-US", "en-GB"])
        except Exception:
            transcript = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])

        raw = transcript.fetch()
        return [
            RawSegment(
                text=entry["text"],
                start=float(entry["start"]),
                duration=float(entry["duration"]),
                confidence=0.85,  # YouTube captions don't expose per-segment confidence
            )
            for entry in raw
            if entry.get("text", "").strip()
        ]

    except _TRANSCRIPT_ERRORS as e:
        logger.info("YouTube captions unavailable for %s: %s", video_id, e)
        return None
    except Exception as e:
        logger.warning("Unexpected error fetching captions for %s: %s", video_id, e)
        return None
