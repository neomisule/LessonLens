"""Thin async LLM wrapper for the Learn Mode pipeline.

Uses Anthropic Claude by default; falls back to OpenAI only if Anthropic is unavailable
or not configured. All methods return parsed Python dicts/lists — callers never
deal with raw text.
"""
import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_HAIKU_MODEL   = "claude-3-5-haiku-20241022"   # fast/cheap — bulk extraction
_SONNET_MODEL  = "claude-3-5-sonnet-20241022"  # quality — summaries judges read
_DEFAULT_MODEL = _HAIKU_MODEL
_FALLBACK_MODEL = "gpt-4o-mini"


class LLMClient:
    """
    Async LLM client that tries Anthropic first, OpenAI second.

    Usage::
        client = LLMClient(anthropic_key="sk-ant-...", openai_key="sk-...")
        result = await client.extract_json(system_prompt, user_prompt)
    """

    def __init__(
        self,
        anthropic_key: str = "",
        openai_key: str = "",
        model: str = _DEFAULT_MODEL,
    ) -> None:
        self._anthropic_key = anthropic_key
        self._openai_key = openai_key
        self._model = model
        self._available = bool(anthropic_key or openai_key)

    @property
    def available(self) -> bool:
        return self._available

    async def extract_json(self, system: str, user: str) -> dict[str, Any]:
        """
        Send a system + user prompt and parse the JSON response.

        Returns an empty dict if no LLM is configured or on any error.
        Never raises — callers should check the returned dict for expected keys.
        """
        if not self._available:
            logger.debug("LLMClient: no API key configured, returning empty result")
            return {}

        if self._anthropic_key:
            return await self._call_anthropic(system, user)
        return await self._call_openai(system, user)

    async def _call_anthropic(self, system: str, user: str) -> dict[str, Any]:
        try:
            from langchain_anthropic import ChatAnthropic
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = ChatAnthropic(
                model=self._model,
                api_key=self._anthropic_key,
                max_tokens=4096,
                temperature=0.05,       # near-zero for factual extraction
            )
            messages = [SystemMessage(content=system), HumanMessage(content=user)]
            response = await llm.ainvoke(messages)
            return self._parse_json(str(response.content))

        except ImportError:
            logger.warning("langchain_anthropic not installed; trying openai")
            if self._openai_key:
                return await self._call_openai(system, user)
            return {}
        except Exception as exc:
            logger.error("Anthropic call failed: %s", exc)
            return {}

    async def _call_openai(self, system: str, user: str) -> dict[str, Any]:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = ChatOpenAI(
                model=_FALLBACK_MODEL,
                api_key=self._openai_key,
                max_tokens=4096,
                temperature=0.05,
            )
            messages = [SystemMessage(content=system), HumanMessage(content=user)]
            response = await llm.ainvoke(messages)
            return self._parse_json(str(response.content))

        except Exception as exc:
            logger.error("OpenAI call failed: %s", exc)
            return {}

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Extract JSON from LLM response, handling ```json ... ``` wrappers."""
        # Try ```json block first
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1)
        else:
            # Try plain ``` block
            match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)

        try:
            result = json.loads(text.strip())
            return result if isinstance(result, dict) else {}
        except json.JSONDecodeError as exc:
            logger.warning("JSON parse failed: %s | text[:200]=%s", exc, text[:200])
            return {}
