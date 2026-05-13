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


def _parse_raw(raw: list) -> list[RawSegment]:
    """Convert raw transcript entries (dict or object) to RawSegments."""
    result = []
    for entry in raw:
        if isinstance(entry, dict):
            text = entry.get("text", "").strip()
            start = float(entry.get("start", 0))
            duration = float(entry.get("duration", 0))
        else:
            text = getattr(entry, "text", "").strip()
            start = float(getattr(entry, "start", 0))
            duration = float(getattr(entry, "duration", 0))
        if text:
            result.append(RawSegment(text=text, start=start, duration=duration, confidence=0.85))
    return result


def fetch_captions_sync(video_id: str) -> list[RawSegment] | None:
    """
    Fetch YouTube captions with aggressive fallback strategy:
      1. English manual captions
      2. English auto-generated captions
      3. Any available language (translated to English if possible)
      4. Any available language raw (better than nothing)
    """
    if not _YT_API_AVAILABLE:
        return None

    try:
        # ── New v1.0+ API (get_transcript) ───────────────────────────────────
        if not hasattr(YouTubeTranscriptApi, "list_transcripts"):
            try:
                raw = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=["en", "en-US", "en-GB", "en-CA"]
                )
                return _parse_raw(raw)
            except Exception:
                raw = YouTubeTranscriptApi.get_transcript(video_id)
                return _parse_raw(raw)

        # ── v0.x API (list_transcripts) ───────────────────────────────────────
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Strategy 1: English manual
        try:
            return _parse_raw(
                transcript_list.find_manually_created_transcript(
                    ["en", "en-US", "en-GB", "en-CA", "en-AU"]
                ).fetch()
            )
        except Exception:
            pass

        # Strategy 2: English auto-generated
        try:
            return _parse_raw(
                transcript_list.find_generated_transcript(
                    ["en", "en-US", "en-GB", "en-CA", "en-AU"]
                ).fetch()
            )
        except Exception:
            pass

        # Strategy 3 & 4: Any language — translate to English or use raw
        available = list(transcript_list)
        if available:
            t = available[0]
            try:
                return _parse_raw(t.translate("en").fetch())
            except Exception:
                try:
                    return _parse_raw(t.fetch())
                except Exception:
                    pass

        return None

    except _TRANSCRIPT_ERRORS as e:
        logger.info("YouTube captions unavailable for %s: %s", video_id, e)
        return None
    except Exception as e:
        logger.warning("Unexpected error fetching captions for %s: %s", video_id, e)
        return None
