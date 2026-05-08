"""ElevenLabs TTS client with on-disk audio caching.

Cache strategy:
  - Cache key: SHA-256 of (text + voice_id + model_id)
  - Cache location: {audio_storage_path}/{cache_key[:2]}/{cache_key}.mp3
  - On cache hit: return file path immediately, no API call
  - On cache miss: call ElevenLabs, write to disk, return path

Graceful degradation: if no ElevenLabs API key is configured,
`generate_audio()` returns None and callers handle that case.
"""
import hashlib
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ElevenLabs model that supports 29+ languages
_MODEL_ID = "eleven_multilingual_v2"

# Default voice — "Rachel" (warm, clear, works well cross-language)
_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# Approximate duration estimate: ~150 words per minute of speech
_WORDS_PER_MINUTE = 150


def _cache_key(text: str, voice_id: str, model_id: str) -> str:
    payload = f"{model_id}:{voice_id}:{text}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _cache_path(storage_root: Path, key: str) -> Path:
    """Two-level directory sharding to avoid flat-dir inode limits."""
    shard = key[:2]
    return storage_root / shard / f"{key}.mp3"


def _estimate_duration_ms(text: str) -> int:
    words = len(text.split())
    return int((words / _WORDS_PER_MINUTE) * 60 * 1000)


class ElevenLabsClient:
    """
    Async-safe ElevenLabs TTS client.

    Usage::
        client = ElevenLabsClient(api_key="...", storage_path=Path("/tmp/audio"))
        path, duration_ms, cached = await client.generate_audio(text="Hello world")
    """

    def __init__(
        self,
        api_key: str = "",
        storage_path: Path | None = None,
        voice_id: str = _DEFAULT_VOICE_ID,
        model_id: str = _MODEL_ID,
    ) -> None:
        self._api_key = api_key
        self._storage = storage_path or Path("/tmp/lecturelens_audio")
        self._voice_id = voice_id
        self._model_id = model_id
        self._available = bool(api_key)

    @property
    def available(self) -> bool:
        return self._available

    async def generate_audio(
        self,
        text: str,
        voice_id: str | None = None,
    ) -> tuple[Optional[Path], int, bool]:
        """
        Generate TTS audio for `text`.

        Returns (file_path, duration_ms, from_cache).
        Returns (None, 0, False) if client is unavailable or on error.
        """
        if not self._available:
            return None, 0, False

        vid = voice_id or self._voice_id
        key = _cache_key(text, vid, self._model_id)
        path = _cache_path(self._storage, key)

        # ── Cache hit ─────────────────────────────────────────────────────────
        if path.exists() and path.stat().st_size > 0:
            duration_ms = _estimate_duration_ms(text)
            logger.debug("[elevenlabs] Cache HIT for key=%s", key[:12])
            return path, duration_ms, True

        # ── ElevenLabs API call ───────────────────────────────────────────────
        try:
            audio_bytes = await self._call_api(text, vid)
        except Exception as exc:
            logger.error("[elevenlabs] API call failed: %s", exc)
            return None, 0, False

        # ── Persist to disk ───────────────────────────────────────────────────
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(audio_bytes)
            logger.info("[elevenlabs] Audio written: %s (%d bytes)", path, len(audio_bytes))
        except OSError as exc:
            logger.error("[elevenlabs] Failed to write audio: %s", exc)
            return None, 0, False

        duration_ms = _estimate_duration_ms(text)
        return path, duration_ms, False

    async def _call_api(self, text: str, voice_id: str) -> bytes:
        """Make the blocking ElevenLabs call in a thread pool."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._call_api_sync, text, voice_id)

    def _call_api_sync(self, text: str, voice_id: str) -> bytes:
        try:
            from elevenlabs import ElevenLabs
            from elevenlabs.types import VoiceSettings
        except ImportError as exc:
            raise RuntimeError(
                "elevenlabs package not installed. Run: pip install elevenlabs"
            ) from exc

        client = ElevenLabs(api_key=self._api_key)
        audio_iter = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=self._model_id,
            voice_settings=VoiceSettings(
                stability=0.45,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        return b"".join(audio_iter)
