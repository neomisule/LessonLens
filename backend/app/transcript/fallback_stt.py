"""Whisper fallback speech-to-text transcription.

Used when YouTube captions are unavailable or have poor quality.

Flow:
  1. Download audio from YouTube using yt-dlp
  2. Transcribe with Groq Whisper API (primary — ~10-20x faster than OpenAI)
     OR OpenAI Whisper API (secondary fallback)
  3. Return list[RawSegment]
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

_GROQ_AVAILABLE = False
try:
    import groq  # noqa: F401
    _GROQ_AVAILABLE = True
except ImportError:
    pass


async def download_audio(youtube_url: str, output_dir: str) -> str:
    """
    Download the audio track of a YouTube video using yt-dlp.

    Uses the SMALLEST available audio stream and skips ffmpeg conversion
    entirely — Groq/OpenAI Whisper both accept webm/m4a/opus natively.
    This cuts download size by 4-8x and eliminates the ffmpeg CPU step.

    Returns the path of the downloaded audio file.
    Raises RuntimeError if yt-dlp is not available or download fails.
    """
    if not _YT_DLP_AVAILABLE:
        raise RuntimeError(
            "yt-dlp is not installed. Install it with: pip install yt-dlp"
        )

    output_template = os.path.join(output_dir, "audio.%(ext)s")
    ydl_opts = {
        # worstaudio = smallest stream; Whisper doesn't need high quality
        # Falls back to bestaudio if worstaudio unavailable
        "format": "worstaudio/bestaudio",
        "outtmpl": output_template,
        # NO postprocessors — skip ffmpeg entirely, saves 30-90s per video
        "quiet": True,
        "no_warnings": True,
    }

    # Run yt-dlp in a thread so we don't block the event loop
    def _download() -> str:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        # yt-dlp outputs audio.<ext> — find the actual file
        import glob as _glob
        files = _glob.glob(os.path.join(output_dir, "audio.*"))
        if not files:
            raise RuntimeError("yt-dlp produced no output file in " + output_dir)
        return files[0]

    try:
        return await asyncio.wait_for(
            asyncio.get_running_loop().run_in_executor(None, _download),
            timeout=300,  # 5-minute hard cap — avoids infinite hang on large videos
        )
    except asyncio.TimeoutError:
        raise RuntimeError(f"Audio download timed out after 5 minutes for {youtube_url}")


async def transcribe_with_groq(audio_path: str, api_key: str) -> list[RawSegment]:
    """Transcribe using Groq Whisper — ~10-20x faster than OpenAI Whisper."""
    if not _GROQ_AVAILABLE:
        raise RuntimeError("groq package not installed")

    from groq import AsyncGroq

    client = AsyncGroq(api_key=api_key)
    with open(audio_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    segments: list[RawSegment] = []
    for seg in (getattr(response, "segments", None) or []):
        duration = seg.end - seg.start
        if duration <= 0:
            continue
        segments.append(RawSegment(
            text=seg.text.strip(),
            start=seg.start,
            duration=duration,
            confidence=0.92,  # Groq doesn't expose no_speech_prob; assume high quality
        ))
    return segments


async def transcribe_with_openai(audio_path: str, api_key: str) -> list[RawSegment]:
    """Transcribe using OpenAI Whisper API (secondary fallback)."""
    if not _OPENAI_AVAILABLE:
        raise RuntimeError("openai package is not installed")

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
    groq_api_key: str = "",
    openai_api_key: str = "",
) -> list[RawSegment] | None:
    """
    Orchestrate audio download + Whisper transcription.
    Tries Groq first (fast), falls back to OpenAI, returns None on total failure.
    """
    with tempfile.TemporaryDirectory(prefix="lecturelens_audio_") as tmpdir:
        try:
            logger.info("Downloading audio for Whisper fallback: %s", youtube_url)
            audio_path = await download_audio(youtube_url, tmpdir)

            if groq_api_key and _GROQ_AVAILABLE:
                try:
                    logger.info("Transcribing with Groq Whisper (fast path)")
                    segs = await transcribe_with_groq(audio_path, groq_api_key)
                    logger.info("Groq Whisper produced %d segments", len(segs))
                    return segs
                except Exception as exc:
                    logger.warning("Groq Whisper failed (%s), trying OpenAI", exc)

            if openai_api_key and _OPENAI_AVAILABLE:
                logger.info("Transcribing with OpenAI Whisper (fallback)")
                segs = await transcribe_with_openai(audio_path, openai_api_key)
                logger.info("OpenAI Whisper produced %d segments", len(segs))
                return segs

            logger.error("No STT API key configured for Whisper fallback")
            return None

        except Exception as exc:
            logger.error("Whisper fallback failed for %s: %s", youtube_url, exc)
            return None
