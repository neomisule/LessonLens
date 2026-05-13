"""Thin async LLM wrapper — calls Anthropic SDK directly (no LangChain overhead)."""
import json
import logging
import re
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

_HAIKU_MODEL    = "claude-3-5-haiku-20241022"   # fast/cheap — bulk extraction
_SONNET_MODEL   = "claude-3-5-sonnet-20241022"  # quality — summaries judges read
_DEFAULT_MODEL  = _HAIKU_MODEL
_FALLBACK_MODEL = "gpt-4o-mini"


class LLMClient:
    """
    Async LLM wrapper with per-instance clients.

    Clients are created in __init__ (not cached at module level) so that each
    LLMClient instance — created fresh inside asyncio.run() for every Celery
    task — owns an httpx connection pool bound to the correct event loop.
    Module-level caching caused "Future attached to different event loop" errors
    on all LLM calls after the first Celery task completed.
    """

    def __init__(
        self,
        anthropic_key: str = "",
        openai_key: str = "",
        model: str = _DEFAULT_MODEL,
    ) -> None:
        self._anthropic_key = anthropic_key
        self._openai_key    = openai_key
        self._model         = model
        self._available     = bool(anthropic_key or openai_key)
        # Create fresh client instances bound to the current event loop.
        self._anthropic_client: anthropic.AsyncAnthropic | None = (
            anthropic.AsyncAnthropic(api_key=anthropic_key, timeout=45.0)
            if anthropic_key else None
        )
        self._openai_client: Any = None  # lazy — only instantiated if used

    @property
    def available(self) -> bool:
        return self._available

    async def extract_json(self, system: str, user: str) -> dict[str, Any]:
        if not self._available:
            return {}
        if self._anthropic_key:
            return await self._call_anthropic(system, user)
        return await self._call_openai(system, user)

    async def _call_anthropic(self, system: str, user: str) -> dict[str, Any]:
        try:
            assert self._anthropic_client is not None
            msg = await self._anthropic_client.messages.create(
                model=self._model,
                max_tokens=4096,
                temperature=0.05,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return self._parse_json(msg.content[0].text)
        except Exception as exc:
            logger.error("Anthropic call failed: %s", exc)
            return {}

    async def _call_openai(self, system: str, user: str) -> dict[str, Any]:
        try:
            if self._openai_client is None:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(api_key=self._openai_key)
            resp = await self._openai_client.chat.completions.create(
                model=_FALLBACK_MODEL,
                max_tokens=4096,
                temperature=0.05,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
            )
            return self._parse_json(resp.choices[0].message.content or "")
        except Exception as exc:
            logger.error("OpenAI call failed: %s", exc)
            return {}

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
        else:
            match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
        try:
            result = json.loads(text.strip())
            return result if isinstance(result, dict) else {}
        except json.JSONDecodeError as exc:
            logger.warning("JSON parse failed: %s | text[:200]=%s", exc, text[:200])
            return {}
