"""Whisper fallback speech-to-text transcription.

Used when YouTube captions are unavailable or have poor quality.

Flow:
  1. Download audio from YouTube using yt-dlp (subprocess)
  2. Transcribe with OpenAI Whisper API (verbose_json with segment timestamps)
  3. Return list[RawSegment]

Requires:
  - yt-dlp installed and on PATH  (or installed as a Python package)
  - OPENAI_API_KEY set in settings
"""
import asyncio
import logging
import os
import tempfile

from app.transcript.schemas import RawSegment

logger = logging.getLogger(__name__)

_YT_DLP_AVAILABLE = False
try:
    import yt_dlp  # noqa: F401
    _YT_DLP_AVAILABLE = True
except ImportError:
    pass

_OPENAI_AVAILABLE = False
try:
    import openai  # noqa: F401
    _OPENAI_AVAILABLE = True
except ImportError:
    pass


async def download_audio(youtube_url: str, output_dir: str) -> str:
    """
    Download the audio track of a YouTube video using yt-dlp.

    Returns the path of the downloaded mp3 file.
    Raises RuntimeError if yt-dlp is not available or download fails.
    """
    if not _YT_DLP_AVAILABLE:
        raise RuntimeError(
            "yt-dlp is not installed. Install it with: pip install yt-dlp"
        )

    output_template = os.path.join(output_dir, "audio.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
        "quiet": True,
        "no_warnings": True,
    }

    # Run yt-dlp in a thread so we don't block the event loop
    def _download() -> str:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        mp3 = os.path.join(output_dir, "audio.mp3")
        if not os.path.exists(mp3):
            raise RuntimeError(f"yt-dlp produced no output file at {mp3}")
        return mp3

    return await asyncio.get_event_loop().run_in_executor(None, _download)


async def transcribe_with_whisper(
    audio_path: str,
    api_key: str,
) -> list[RawSegment]:
    """
    Transcribe an audio file using the OpenAI Whisper API.

    Uses verbose_json output to get per-segment timestamps and confidence.
    Returns list[RawSegment] matching the same interface as YouTube captions.
    """
    if not _OPENAI_AVAILABLE:
        raise RuntimeError("openai package is not installed. Install it with: pip install openai")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)

    with open(audio_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    segments: list[RawSegment] = []
    for seg in (response.segments or []):
        # no_speech_prob is available on verbose responses
        no_speech = getattr(seg, "no_speech_prob", 0.0) or 0.0
        confidence = max(0.0, min(1.0, 1.0 - no_speech))
        duration = seg.end - seg.start

        if duration <= 0:
            continue

        segments.append(RawSegment(
            text=seg.text.strip(),
            start=seg.start,
            duration=duration,
            confidence=confidence,
        ))

    return segments


async def transcribe_fallback(
    youtube_url: str,
    api_key: str,
) -> list[RawSegment] | None:
    """
    Orchestrate audio download + Whisper transcription.

    Returns None (and logs the error) rather than raising, so callers can
    handle failure gracefully without crashing the entire pipeline.
    """
    with tempfile.TemporaryDirectory(prefix="lecturelens_audio_") as tmpdir:
        try:
            logger.info("Downloading audio for Whisper fallback: %s", youtube_url)
            audio_path = await download_audio(youtube_url, tmpdir)

            logger.info("Transcribing audio with Whisper: %s", audio_path)
            segments = await transcribe_with_whisper(audio_path, api_key)
            logger.info("Whisper produced %d segments", len(segments))
            return segments

        except Exception as exc:
            logger.error("Whisper fallback failed for %s: %s", youtube_url, exc)
            return None
